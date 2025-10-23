from fastapi import FastAPI
from email_multi_check import (
    verify_email,
    verify_email_syntax,
    verify_email_domain,
    verify_email_web_auth,
    verify_email_rcpt,
    verify_email_vrfy,
    verify_email_expn,
    verify_email_mail_from,
)

app = FastAPI(title="Email Verifier API")


@app.get("/verify")
async def verify_email_endpoint(
    email: str, sender_email: str = "info@filterdns.net", ports: str = "25,2525,587,465"
):
    """Verify an email address using all methods in email_verifier."""
    port_list = [int(p.strip()) for p in ports.split(",")]
    results = verify_email(email, sender_email, port_list)
    return [result.model_dump() for result in results]


@app.get("/verify/syntax")
async def verify_email_syntax_endpoint(email: str):
    """Verify email syntax using regex."""
    result = verify_email_syntax(email)
    return (
        result.model_dump() if result else {"message": "Valid syntax", "status": True}
    )


@app.get("/verify/domain")
async def verify_email_domain_endpoint(email: str):
    """Verify email domain by checking MX records."""
    valid, mx_servers = verify_email_domain(email)
    return {"valid": valid, "mx_servers": mx_servers}


@app.get("/verify/web")
async def verify_email_web_auth_endpoint(email: str):
    """Verify email existence via web API for supported domains."""
    result = verify_email_web_auth(email)
    return result.model_dump()


@app.get("/verify/rcpt")
async def verify_email_rcpt_endpoint(
    email: str, sender_email: str = "info@filterdns.net", port: int = 25
):
    """Verify email using RCPT method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_rcpt(email, sender_email, mx_servers, port)
    return result.model_dump()


@app.get("/verify/vrfy")
async def verify_email_vrfy_endpoint(
    email: str, sender_email: str = "info@filterdns.net", port: int = 25
):
    """Verify email using VRFY method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_vrfy(email, sender_email, mx_servers, port)
    return result.model_dump()


@app.get("/verify/expn")
async def verify_email_expn_endpoint(
    email: str, sender_email: str = "info@filterdns.net", port: int = 25
):
    """Verify email using EXPN method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_expn(email, sender_email, mx_servers, port)
    return result.model_dump()


@app.get("/verify/mf")
async def verify_email_mail_from_endpoint(
    email: str, sender_email: str = "info@filterdns.net", port: int = 25
):
    """Verify email using MAIL FROM / RCPT TO method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_mail_from(email, sender_email, mx_servers, port)
    return result.model_dump()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
