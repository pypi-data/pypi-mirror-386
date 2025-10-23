import logging
import smtplib
import argparse
import os
from typing import List, Tuple
from email_multi_check import (
    verify_email_domain,
    verify_email_syntax,
    verify_email,
    verify_email_rcpt,
    verify_email_vrfy,
    verify_email_expn,
    verify_email_mail_from,
    verify_email_web_auth,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def check_mx_records(email: str) -> Tuple[bool, List[str]]:
    """Check DNS MX records for the email's domain using email_verifier."""
    try:
        valid, mx_servers = verify_email_domain(email)
        if valid:
            logger.info(f"MX records for {email.split('@')[1]}: {mx_servers}")
        else:
            logger.error("No MX records found or invalid domain")
        return valid, mx_servers
    except Exception as e:
        logger.error(f"MX check failed for {email}: {str(e)}")
        return False, []


def check_smtp_ports(
    email: str, ports: List[int], sender_email: str, mx_servers: List[str]
) -> None:
    """Check SMTP port connectivity for the email's MX server."""
    mx_record = mx_servers[0]
    for port in ports:
        try:
            logger.debug(f"Trying SMTP connection to {mx_record} on port {port}")
            server = (
                smtplib.SMTP_SSL(mx_record, port, timeout=10)
                if port == 465
                else smtplib.SMTP(mx_record, port, timeout=10)
            )
            server.set_debuglevel(0)
            server.helo()
            server.mail(sender_email)
            server.quit()
            logger.info(f"Port {port}: Connection successful")
        except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
            logger.error(f"Port {port}: Connection failed - {str(e)}")


def check_email(email: str, sender_email: str, mode: str, ports: List[int]) -> None:
    """Verify email address using specified method or all methods."""
    valid_modes = {"rcpt", "vrfy", "expn", "mf", "web", "all"}
    if mode not in valid_modes:
        logger.error(f"Invalid mode: {mode}. Choose from {', '.join(valid_modes)}")
        return

    syntax_result = verify_email_syntax(email)
    if syntax_result:
        logger.error(
            f"Invalid email syntax: {syntax_result.message}, {syntax_result.data}"
        )
        return

    if mode == "web" and not os.path.exists("url.cfg"):
        logger.error(
            "Web auth mode requires url.cfg in the project root. "
            "Create url.cfg with sections for domains (e.g., [mail.ru]) containing user_exists_url and requests_file."
        )
        return

    valid, mx_servers = check_mx_records(email)
    if mode != "web" and not valid and not mx_servers:
        logger.error("No valid MX servers to verify email")
        return

    # Check SMTP ports connectivity (skip for web mode)
    if mode != "web" and valid and mx_servers:
        check_smtp_ports(email, ports, sender_email, mx_servers)

    method_map = {
        "rcpt": verify_email_rcpt,
        "vrfy": verify_email_vrfy,
        "expn": verify_email_expn,
        "mf": verify_email_mail_from,
        "web": verify_email_web_auth,
    }

    if mode == "all":
        results = verify_email(email, sender_email, ports)
        for result in results:
            logger.info(
                f"Email verification ({result.method}): email={result.email}, message={result.message}, "
                f"status={result.status}, MX={result.MX}, data={result.data}"
            )
            print(f"{result}")
    else:
        if mode == "web":
            result = method_map[mode](email)
            logger.info(
                f"Email verification ({mode}): email={result.email}, message={result.message}, "
                f"status={result.status}, MX={result.MX}, data={result.data}"
            )
            print(f"{result}")
        else:
            for port in ports:
                result = method_map[mode](email, sender_email, mx_servers, port)
                logger.info(
                    f"Email verification ({mode}): email={result.email}, message={result.message}, "
                    f"status={result.status}, MX={result.MX}, data={result.data}"
                )
                print(f"{result}")


def parse_ports(port_str: str) -> List[int]:
    """Parse comma-separated port string into a list of integers."""
    try:
        return [int(port.strip()) for port in port_str.split(",")]
    except ValueError as e:
        logger.error(
            f"Invalid port format: {port_str}. Expected comma-separated integers."
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test DNS MX records, SMTP ports, and email verification."
    )
    parser.add_argument(
        "-c",
        "--check-email",
        required=True,
        help="Email address to check (e.g., test@gmail.com)",
    )
    parser.add_argument(
        "-e",
        "--sender-email",
        default="info@filterdns.net",
        help="Sender email address (e.g., info@filterdns.net)",
    )
    parser.add_argument(
        "-p",
        "--ports",
        default="25,2525,587,465",
        help="Comma-separated SMTP ports to check (e.g., 25,2525,587,465)",
    )
    parser.add_argument(
        "-m",
        "--mode",
        default="all",
        help="Verification mode: rcpt, vrfy, expn, mf, web, all",
    )

    args = parser.parse_args()
    ports = parse_ports(args.ports)

    check_email(args.check_email, args.sender_email, args.mode, ports)
