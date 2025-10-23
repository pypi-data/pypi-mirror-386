from .email_multi_check import (
    verify_email,
    verify_email_domain,
    verify_email_syntax,
    verify_email_rcpt,
    verify_email_vrfy,
    verify_email_expn,
    verify_email_mail_from,
    verify_email_web_auth,
    load_web_auth_config,
    load_requests_config,
    EmailVerificationResult,
)

__version__ = "1.0.7"
