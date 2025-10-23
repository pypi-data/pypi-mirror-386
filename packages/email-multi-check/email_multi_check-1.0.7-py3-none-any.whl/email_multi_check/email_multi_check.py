import configparser
import logging
import os
import re
import smtplib
import time
import requests
import dns.resolver
import idna
from pydantic import BaseModel
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)  # level INFO & DEBUG
logger = logging.getLogger(__name__)

# Email regex pattern (improved to be more RFC 5322 compliant)
EMAIL_REGEX = r"^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"


class EmailVerificationResult(BaseModel):
    """Pydantic model for email verification result."""

    system_id: str
    email: str
    message: str
    status: bool
    MX: List[str]
    smtplib_code: Optional[int] = None
    method_code: Optional[int] = None
    method: Optional[str] = None
    web_auth_code: Optional[int] = None
    data: Optional[str] = None


def load_web_auth_config(domain: str) -> Tuple[Optional[str], Optional[str]]:
    """Load web auth URL and requests file from url.cfg for the given domain."""
    config_file = "url.cfg"
    if not os.path.exists(config_file):
        return None, None

    config = configparser.ConfigParser()
    config.read(config_file)

    if domain.lower() not in config:
        return None, None

    section = config[domain.lower()]
    return section.get("user_exists_url"), section.get("requests_file")


def load_requests_config(requests_file: str, email: str) -> Tuple[str, dict, dict]:
    """Load request configuration from the specified requests file."""
    if not os.path.exists(requests_file):
        logger.error(f"Requests file {requests_file} not found")
        return "GET", {}, {}

    config = configparser.ConfigParser()
    config.read(requests_file)

    method = config.get("method", "type", fallback="GET").upper()
    headers = dict(config["headers"]) if "headers" in config else {}
    params = (
        {k: v.format(email=email) for k, v in config["params"].items()}
        if "params" in config
        else {}
    )

    return method, headers, params


def verify_email_syntax(
    email: str, allow_success: bool = False
) -> Optional[EmailVerificationResult]:
    """Verify email syntax using regex."""
    logger.debug(f"Verifying syntax for email: {email}")
    if not re.match(EMAIL_REGEX, email, re.IGNORECASE):
        logger.debug(f"Email {email} does not match regex pattern")
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="Bad Syntax",
            status=False,
            MX=[],
            data="Email does not match required pattern",
        )
    logger.debug(f"Email {email} matches regex pattern")
    if allow_success:
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="Valid syntax",
            status=True,
            MX=[],
            method="syntax",
        )
    return None


def verify_email_domain(email: str) -> Tuple[bool, List[str]]:
    """Verify email domain by checking MX records."""
    try:
        domain = email.split("@")[1]
        try:
            idna.encode(domain)
        except idna.IDNAError as e:
            logger.error(f"IDNA encoding error for domain {domain}: {str(e)}")
            return False, []

        answers = dns.resolver.resolve(domain, "MX")
        mx_servers = [str(answer.exchange) for answer in answers]
        return True, mx_servers
    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.NoAnswer,
        IndexError,
        UnicodeError,
    ) as e:
        logger.error(f"Domain verification failed for {domain}: {str(e)}")
        return False, []


def verify_email_rcpt(
    email: str, sender_email: str, mx_servers: List[str], port: int
) -> EmailVerificationResult:
    """Verify email using EHLO + RCPT method."""
    try:
        mx_record = mx_servers[0]
        logger.debug(f"Trying SMTP connection to {mx_record} on port {port} for RCPT")
        server = (
            smtplib.SMTP_SSL(mx_record, port, timeout=15)
            if port == 465
            else smtplib.SMTP(mx_record, port, timeout=15)
        )
        server.set_debuglevel(0)
        server.ehlo()
        server.mail(sender_email)
        code, message = server.rcpt(email)
        server.quit()

        logger.debug(f"RCPT response on port {port}: code={code}, message={message}")
        status = code == 250
        message_text = (
            "Valid email"
            if code == 250
            else (
                "No such user!"
                if code == 550
                else (
                    "Quota expired!"
                    if code == 452
                    else f"SMTP error: {message.decode('utf-8') if isinstance(message, bytes) else message}"
                )
            )
        )

        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            smtplib_code=250,
            method_code=code,
            method="rcpt",
            message=message_text,
            status=status,
            MX=mx_servers,
            data=f"RCPT code: {code}, port: {port}",
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        logger.error(f"RCPT verification failed for {email} on port {port}: {str(e)}")
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="SMTP connection failed",
            status=False,
            MX=mx_servers,
            data=f"RCPT error: {str(e)}, port: {port}",
        )


def verify_email_vrfy(
    email: str, sender_email: str, mx_servers: List[str], port: int
) -> EmailVerificationResult:
    """Verify email using VRFY method."""
    try:
        mx_record = mx_servers[0]
        logger.debug(f"Trying SMTP connection to {mx_record} on port {port} for VRFY")
        server = (
            smtplib.SMTP_SSL(mx_record, port, timeout=15)
            if port == 465
            else smtplib.SMTP(mx_record, port, timeout=15)
        )
        server.set_debuglevel(0)
        server.ehlo()
        if not hasattr(server, "vrfy"):
            server.quit()
            return EmailVerificationResult(
                system_id="1.0.7",
                email=email,
                message="VRFY not supported",
                status=False,
                MX=mx_servers,
                data=f"VRFY not supported by server on port {port}",
            )
        code, message = server.vrfy(email)
        server.quit()

        logger.debug(f"VRFY response on port {port}: code={code}, message={message}")
        status = code == 250
        message_text = (
            "Valid email"
            if code == 250
            else (
                "No such user!"
                if code == 550
                else (
                    "Quota expired!"
                    if code == 452
                    else f"SMTP error: {message.decode('utf-8') if isinstance(message, bytes) else message}"
                )
            )
        )

        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            smtplib_code=250,
            method_code=code,
            method="vrfy",
            message=message_text,
            status=status,
            MX=mx_servers,
            data=f"VRFY code: {code}, port: {port}",
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        logger.error(f"VRFY verification failed for {email} on port {port}: {str(e)}")
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="SMTP connection failed",
            status=False,
            MX=mx_servers,
            data=f"VRFY error: {str(e)}, port: {port}",
        )


def verify_email_expn(
    email: str, sender_email: str, mx_servers: List[str], port: int
) -> EmailVerificationResult:
    """Verify email using EXPN method."""
    try:
        mx_record = mx_servers[0]
        logger.debug(f"Trying SMTP connection to {mx_record} on port {port} for EXPN")
        server = (
            smtplib.SMTP_SSL(mx_record, port, timeout=15)
            if port == 465
            else smtplib.SMTP(mx_record, port, timeout=15)
        )
        server.set_debuglevel(0)
        server.ehlo()
        if not hasattr(server, "expn"):
            server.quit()
            return EmailVerificationResult(
                system_id="1.0.7",
                email=email,
                message="EXPN not supported",
                status=False,
                MX=mx_servers,
                data=f"EXPN not supported by server on port {port}",
            )
        code, message = server.expn(email)
        server.quit()

        logger.debug(f"EXPN response on port {port}: code={code}, message={message}")
        status = code == 250
        message_text = (
            "Valid email"
            if code == 250
            else (
                "No such user!"
                if code == 550
                else (
                    "Quota expired!"
                    if code == 452
                    else f"SMTP error: {message.decode('utf-8') if isinstance(message, bytes) else message}"
                )
            )
        )

        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            smtplib_code=250,
            method_code=code,
            method="expn",
            message=message_text,
            status=status,
            MX=mx_servers,
            data=f"EXPN code: {code}, port: {port}",
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        logger.error(f"EXPN verification failed for {email} on port {port}: {str(e)}")
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="SMTP connection failed",
            status=False,
            MX=mx_servers,
            data=f"EXPN error: {str(e)}, port: {port}",
        )


def verify_email_mail_from(
    email: str, sender_email: str, mx_servers: List[str], port: int
) -> EmailVerificationResult:
    """Verify email using MAIL FROM / RCPT TO with RSET."""
    try:
        mx_record = mx_servers[0]
        logger.debug(
            f"Trying SMTP connection to {mx_record} on port {port} for MAIL FROM / RCPT TO"
        )
        server = (
            smtplib.SMTP_SSL(mx_record, port, timeout=15)
            if port == 465
            else smtplib.SMTP(mx_record, port, timeout=15)
        )
        server.set_debuglevel(0)
        server.ehlo()
        server.mail(sender_email)
        code, message = server.rcpt(email)
        server.rset()
        server.quit()

        logger.debug(
            f"MAIL FROM / RCPT TO response on port {port}: code={code}, message={message}"
        )
        status = code == 250
        message_text = (
            "Valid email"
            if code == 250
            else (
                "No such user!"
                if code == 550
                else (
                    "Quota expired!"
                    if code == 452
                    else f"SMTP error: {message.decode('utf-8') if isinstance(message, bytes) else message}"
                )
            )
        )

        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            smtplib_code=250,
            method_code=code,
            method="mf",
            message=message_text,
            status=status,
            MX=mx_servers,
            data=f"MAIL/RCPT code: {code}, port: {port}",
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        logger.error(
            f"MAIL FROM / RCPT TO verification failed for {email} on port {port}: {str(e)}"
        )
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="SMTP connection failed",
            status=False,
            MX=mx_servers,
            data=f"MAIL/RCPT error: {str(e)}, port: {port}",
        )


def verify_email_web_auth(email: str) -> EmailVerificationResult:
    """Verify email existence via web API specified in url.cfg."""
    domain = email.split("@")[1].lower()
    url, requests_file = load_web_auth_config(domain)

    if not url or not requests_file:
        error_msg = (
            f"Web auth not configured for domain {domain}. "
            "Please create url.cfg with a section for this domain and specify user_exists_url and requests_file."
        )
        logger.error(error_msg)
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="Web auth configuration missing",
            status=False,
            MX=[],
            method="web",
            data=error_msg,
        )

    try:
        method, headers, params = load_requests_config(requests_file, email)
        logger.debug(
            f"Sending web auth request for {email} to {url} with method {method}"
        )
        time.sleep(1)  # Delay to avoid rate-limiting

        if method == "POST":
            response = requests.post(url, headers=headers, data=params, timeout=10)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=10)

        response.raise_for_status()
        data = response.json()

        logger.debug(f"Web auth response for {email}: {data}")

        # Check for 'body' and 'exists' in response
        if "body" not in data or "exists" not in data["body"]:
            return EmailVerificationResult(
                system_id="1.0.7",
                email=email,
                message="Invalid API response format",
                status=False,
                MX=[],
                method="web",
                data=f"Web auth response: {data}",
            )

        status = data["body"]["exists"]
        alternatives = data["body"].get("alternatives", [])
        message_text = "Valid email" if status else "No such user!"
        data_text = f"Web auth response: exists={status}"
        if alternatives:
            data_text += f", alternatives={alternatives}"

        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message=message_text,
            status=status,
            MX=[],
            method="web",
            web_auth_code=(
                100 if not status else None
            ),  # Assume code 100 for non-existing email
            data=data_text,
        )
    except requests.RequestException as e:
        logger.error(f"Web auth verification failed for {email}: {str(e)}")
        return EmailVerificationResult(
            system_id="1.0.7",
            email=email,
            message="Web auth request failed",
            status=False,
            MX=[],
            method="web",
            data=f"Web auth error: {str(e)}",
        )


def verify_email(
    email: str,
    sender_email: str = "info@filterdns.net",
    ports: List[int] = [25, 2525, 587, 465],
) -> List[EmailVerificationResult]:
    """Verify email address using all SMTP methods and web auth across specified ports."""
    syntax_result = verify_email_syntax(email)
    if syntax_result:
        return [syntax_result]

    domain_valid, mx_servers = verify_email_domain(email)
    results = []

    # Try web auth for configured domains
    url, _ = load_web_auth_config(email.split("@")[1].lower())
    if url:
        results.append(verify_email_web_auth(email))

    if not domain_valid:
        results.append(
            EmailVerificationResult(
                system_id="1.0.7",
                email=email,
                message="Invalid domain",
                status=False,
                MX=[],
                data="No MX records found for domain or invalid domain",
            )
        )
        return results

    for port in ports:
        # Try all SMTP methods
        results.append(verify_email_rcpt(email, sender_email, mx_servers, port))
        results.append(verify_email_vrfy(email, sender_email, mx_servers, port))
        results.append(verify_email_expn(email, sender_email, mx_servers, port))
        results.append(verify_email_mail_from(email, sender_email, mx_servers, port))

    return results
