
![Снимок](https://github.com/user-attachments/assets/e0626c69-0ba9-4ad2-be2b-94882a5cc026)

# Email Multi Check

A Python package for verifying email addresses using DNS MX record checks, SMTP methods (RCPT, VRFY, EXPN, MAIL FROM / RCPT TO with RSET), and web-based authentication checks for specific providers like mail.ru.

## Description

This package provides functions to validate email syntax, check domain MX records, and verify email existence using multiple SMTP methods or web API calls. It is designed for reliability across different email providers, with configurable web verification for domains like mail.ru.

Key features:
- Syntax validation using a RFC 5322-compliant regex.
<details>
<summary>RegExp diagram:</summary>

>*No Punycode support*

<img width="1288" height="318" alt="Без названия (1)" src="https://github.com/user-attachments/assets/d66e985d-3cdc-46bf-b7a8-4e52d9bcca22" />
</details>
- DNS MX record verification with IDNA support.
- SMTP verification using four methods: RCPT, VRFY, EXPN, and MAIL FROM / RCPT TO.
- Web-based verification for configured domains, using external configuration files for URLs and request parameters.
- Example Command-line testing script (`test_dns_smtp.py`) with customizable modes and ports.
- Easy integration with FastAPI for REST API endpoints returning JSON responses.

## Installation

Install the package via pip from the wheel file or source:

```bash
pip install email-multi-check
```

Or from source:

```bash
pip install .\dist\email_multi_check-1.0.7-py3-none-any.whl
```

## Dependencies

- dnspython >= 2.8.0
- pydantic >= 2.11.10
- idna >= 3.10
- requests >= 2.32.5

Install them with:

```bash
pip install -r requirements.txt
```

## Usage

### Direct Function Calls

Import and use the functions directly in your Python code.

Example for full verification:
(You can control which mailbox the request will be sent from.)

```python
from email_multi_check import verify_email

# Full verification using all methods on specified ports
results = verify_email(
    email="test@gmail.com",
    sender_email="info@filterdns.net",
    ports=[25, 587]
)
for result in results:
    print(result)
```

Example for syntax verification:
(Uses an improved email regular expression pattern (improved to be more RFC 5322 compliant))

```python
from email_multi_check import verify_email_syntax

# Syntax verification
result = verify_email_syntax("test@gmail.com")
if result:
    print(result)
else:
    print("Valid syntax")
```

Example for domain verification:
(Checking for IDNA encoding errors for a domain and checking the MX records)

```python
from email_multi_check import verify_email_domain

# Domain verification
valid, mx_servers = verify_email_domain("test@gmail.com")
print({"valid": valid, "mx_servers": mx_servers})
```

Example for web-based verification (requires url.cfg):
(Verify email existence via web API specified)

```python
from email_multi_check import verify_email_web_auth

# Web-based verification
result = verify_email_web_auth("test@mail.ru")
print(result)
```

### Command-Line Testing with test_dns_smtp.py

The package includes a test script `test_dns_smtp.py` for command-line verification.

Usage:

```bash
python test_dns_smtp.py -c <email> [-e <sender_email>] [-p <ports>] [-m <mode>]
```

Parameters:
- `-c`, `--check-email`: Email address to check (required, e.g., test@gmail.com).
- `-e`, `--sender-email`: Sender email address (default: info@filterdns.net).
- `-p`, `--ports`: Comma-separated SMTP ports (default: 25,2525,587,465).
- `-m`, `--mode`: Verification mode (default: all). Options: rcpt, vrfy, expn, mf, web, all.

>*use your existing email address to send*

Detailed examples for all iterations (combinations of modes and ports):

1. All modes on default ports:
```bash
   python test_dns_smtp.py -c test@gmail.com -e info@filterdns.net -m all
```

2. All modes on port 25:
```bash
   python test_dns_smtp.py -c test@gmail.com -e info@filterdns.net -p 25 -m all
```

3. RCPT mode on ports 25 and 587:
```bash
   python test_dns_smtp.py -c test@gmail.com -e info@filterdns.net -p 25,587 -m rcpt
```

4. RCPT mode without sender email (uses default=info@filterdns.net):
```bash
    python test_dns_smtp.py -c test@gmail.com -p 25 -m rcpt
```

5. VRFY mode on port 25:
```bash
   python test_dns_smtp.py -c test@gmail.com -e info@filterdns.net -p 25 -m vrfy
```

6. EXPN mode on ports 25,587:
```bash
   python test_dns_smtp.py -c test@gmail.com -e info@filterdns.net -p 25,587 -m expn
```

7. MF mode on port 465:
```bash
   python test_dns_smtp.py -c test@gmail.com -e info@filterdns.net -p 465 -m mf
```
8. Web mode (no ports needed, requires url.cfg):
```bash
   python test_dns_smtp.py -c test@mail.ru -e info@filterdns.net -m web
```
<details>
<summary>Example out True:</summary>
    
```python   
    INFO:__main__:MX records for mail.ru: ['mxs.mail.ru.']
    INFO:__main__:Email verification (web): email=support@mail.ru, message=Valid email, status=True, MX=[], data=Web auth response: exists=True
    system_id='1.0.6' email='support@mail.ru' message='Valid email' status=True MX=[] smtplib_code=None method_code=None method='web' web_auth_code=None data='Web auth response: exists=True'
```
</details>

<details>
<summary>Example out False:</summary>

```python
    INFO:__main__:MX records for mail.ru: ['mxs.mail.ru.']
    INFO:__main__:Email verification (web): email=6tgfjkl@mail.ru, message=No such user!, status=False, MX=[], data=Web auth response: exists=False, alternatives=['6tgfjkl@bk.ru', '6tgfjkl00@mail.ru', '6tgfjkl@inbox.ru', '6tgfjkl2025@mail.ru',        '6tgfjkl@list.ru', '6tgfjkl2026@mail.ru', '6tgfjkl@internet.ru', '6tgfjkl.00@mail.ru']
    system_id='1.0.6' email='6tgfjkl@mail.ru' message='No such user!' status=False MX=[] smtplib_code=None method_code=None method='web' web_auth_code=100 data="Web auth response: exists=False, alternatives=['6tgfjkl@bk.ru', '6tgfjkl00@mail.ru',     '6tgfjkl@inbox.ru', '6tgfjkl2025@mail.ru', '6tgfjkl@list.ru', '6tgfjkl2026@mail.ru', '6tgfjkl@internet.ru', '6tgfjkl.00@mail.ru']"
```
</details>
    
### REST API with FastAPI

You can integrate the package with FastAPI to create a REST API for email verification. Responses are structured as JSON using Pydantic.
<details>
<summary>Example script (`test_api.py`):</summary>
(The code is structured in such a way for better understanding)

```bash
  python --version
  Python 3.11.9
  pip install fastapi==0.118.0 uvicorn==0.37.0
```
```python
from fastapi import FastAPI
from email_multi_check import verify_email, verify_email_syntax, verify_email_domain, verify_email_web_auth, verify_email_rcpt, verify_email_vrfy, verify_email_expn, verify_email_mail_from

app = FastAPI(title="Email Multi Check API")

@app.get("/verify")
async def verify_email_endpoint(email: str, sender_email: str = "info@filterdns.net", ports: str = "25,2525,587,465"):
    """Verify an email address using all methods in email_multi_check."""
    port_list = [int(p.strip()) for p in ports.split(",")]
    results = verify_email(email, sender_email, port_list)
    return [result.model_dump() for result in results]

@app.get("/verify/syntax")
async def verify_email_syntax_endpoint(email: str):
    """Verify email syntax using regex."""
    result = verify_email_syntax(email)
    return result.model_dump() if result else {"message": "Valid syntax", "status": True}

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
async def verify_email_rcpt_endpoint(email: str, sender_email: str = "info@filterdns.net", port: int = 25):
    """Verify email using RCPT method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_rcpt(email, sender_email, mx_servers, port)
    return result.model_dump()

@app.get("/verify/vrfy")
async def verify_email_vrfy_endpoint(email: str, sender_email: str = "info@filterdns.net", port: int = 25):
    """Verify email using VRFY method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_vrfy(email, sender_email, mx_servers, port)
    return result.model_dump()

@app.get("/verify/expn")
async def verify_email_expn_endpoint(email: str, sender_email: str = "info@filterdns.net", port: int = 25):
    """Verify email using EXPN method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_expn(email, sender_email, mx_servers, port)
    return result.model_dump()

@app.get("/verify/mf")
async def verify_email_mail_from_endpoint(email: str, sender_email: str = "info@filterdns.net", port: int = 25):
    """Verify email using MAIL FROM / RCPT TO method."""
    valid, mx_servers = verify_email_domain(email)
    if not valid:
        return {"message": "Invalid domain", "status": False}
    result = verify_email_mail_from(email, sender_email, mx_servers, port)
    return result.model_dump()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
</details>

Run the API:

```bash
python test_api.py
```

### Detailed Example Requests with curl

1. Full verification using all methods on default ports:
>*Please note that without additional port and request type parameters, a cycle with a timeout of 15 seconds per iteration will be launched.*
<details>
<summary>Example Curl:</summary>

```python
curl -X 'GET' \
  'http://127.0.0.1:8000/verify?email=test%40gmail.com&sender_email=info%40filterdns.net&ports=25%2C2525%2C587%2C465' \
  -H 'accept: application/json'
```
</details>

<details>
<summary>Example Out:</summary>

```python
[
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "No such user!",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 550,
    "method": "rcpt",
    "web_auth_code": null,
    "data": "RCPT code: 550, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP error: 2.1.5 Send some mail, I'll try my best 2adb3069b0e04-591def4a7d0si1680162e87.486 - gsmtp",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 252,
    "method": "vrfy",
    "web_auth_code": null,
    "data": "VRFY code: 252, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP error: 5.5.1 Unimplemented command. For more information, go to\n5.5.1  https://support.google.com/a/answer/3221692 2adb3069b0e04-591deebbcecsi1639517e87.93 - gsmtp",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 502,
    "method": "expn",
    "web_auth_code": null,
    "data": "EXPN code: 502, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "No such user!",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 550,
    "method": "mf",
    "web_auth_code": null,
    "data": "MAIL/RCPT code: 550, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "RCPT error: timed out, port: 2525"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "VRFY error: timed out, port: 2525"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "EXPN error: timed out, port: 2525"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "MAIL/RCPT error: timed out, port: 2525"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "RCPT error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "VRFY error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "EXPN error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "MAIL/RCPT error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "RCPT error: timed out, port: 465"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "VRFY error: timed out, port: 465"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "EXPN error: timed out, port: 465"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "MAIL/RCPT error: timed out, port: 465"
  }
]
```
</details>

2. Full verification with custom ports (25,587):
  <details>
  <summary>Example Curl:</summary>

```python
  curl -X 'GET' \
    'http://127.0.0.1:8000/verify?email=test%40gmail.com&sender_email=info%40filterdns.net&ports=25%2C587' \
    -H 'accept: application/json'
  ```
</details>
<details>
<summary>Example Out:</summary>   
   
```python
   [
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "No such user!",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 550,
    "method": "rcpt",
    "web_auth_code": null,
    "data": "RCPT code: 550, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP error: 2.1.5 Send some mail, I'll try my best d2e1a72fcca58-7a22ff1978bsi4305243b3a.44 - gsmtp",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 252,
    "method": "vrfy",
    "web_auth_code": null,
    "data": "VRFY code: 252, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP error: 5.5.1 Unimplemented command. For more information, go to\n5.5.1  https://support.google.com/a/answer/3221692 d9443c01a7336-29247238fd9si45057255ad.736 - gsmtp",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 502,
    "method": "expn",
    "web_auth_code": null,
    "data": "EXPN code: 502, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "No such user!",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": 250,
    "method_code": 550,
    "method": "mf",
    "web_auth_code": null,
    "data": "MAIL/RCPT code: 550, port: 25"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "RCPT error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "VRFY error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "EXPN error: timed out, port: 587"
  },
  {
    "system_id": "1.0.7",
    "email": "test@gmail.com",
    "message": "SMTP connection failed",
    "status": false,
    "MX": [
      "alt4.gmail-smtp-in.l.google.com.",
      "alt2.gmail-smtp-in.l.google.com.",
      "alt3.gmail-smtp-in.l.google.com.",
      "alt1.gmail-smtp-in.l.google.com.",
      "gmail-smtp-in.l.google.com."
    ],
    "smtplib_code": null,
    "method_code": null,
    "method": null,
    "web_auth_code": null,
    "data": "MAIL/RCPT error: timed out, port: 587"
  }
]
   ```
</details>

3. Syntax verification (valid email):
<details>
<summary>Example Curl:</summary>
  
```python
   curl -X 'GET' \
  'http://127.0.0.1:8000/verify/syntax?email=test%40gmail.com' \
  -H 'accept: application/json'
```
</details>

<details>
<summary>Example Out True:</summary>

```python
{
  "message": "Valid syntax",
  "status": true
}
```
</details>

<details>
<summary>Example Out False:</summary>

```python
 {
  "system_id": "1.0.7",
  "email": "invalid@",
  "message": "Bad Syntax",
  "status": false,
  "MX": [],
  "smtplib_code": null,
  "method_code": null,
  "method": null,
  "web_auth_code": null,
  "data": "Email does not match required pattern"
}
```
</details>
    
4. Domain verification (MX records):
<details>
<summary>Example Curl:</summary>

```python
  curl -X 'GET' \
    'http://127.0.0.1:8000/verify/domain?email=test%40gmail.com' \
    -H 'accept: application/json'
```
</details>

<details>
<summary>Example True:</summary>

```python
{
  "valid": true,
  "mx_servers": [
    "gmail-smtp-in.l.google.com.",
    "alt3.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "alt1.gmail-smtp-in.l.google.com."
  ]
}
```
</details>

<details>
<summary>Example False:</summary>

```python
{
  "valid": false,
  "mx_servers": []
}
```
</details>

5. Web verification (for mail.ru):
<details>
<summary>Example Curl:</summary>

```python
   curl -X 'GET' \
  'http://127.0.0.1:8000/verify/web?email=nonexistent123456%40mail.ru' \
  -H 'accept: application/json'
```
</details>

<details>
<summary>Example False:</summary>

```python
{
  "system_id": "1.0.7",
  "email": "nonexistent123456@mail.ru",
  "message": "No such user!",
  "status": false,
  "MX": [],
  "smtplib_code": null,
  "method_code": null,
  "method": "web",
  "web_auth_code": 100,
  "data": "Web auth response: exists=False, alternatives=['nonexistent123456@bk.ru', 'nonexistent123456@inbox.ru', 'nonexistent123456@list.ru', 'nonexistent123456@internet.ru']"
}

```
</details>

<details>
<summary>Example True:</summary>

```python
{
  "system_id": "1.0.7",
  "email": "support@mail.ru",
  "message": "Valid email",
  "status": true,
  "MX": [],
  "smtplib_code": null,
  "method_code": null,
  "method": "web",
  "web_auth_code": null,
  "data": "Web auth response: exists=True"
}
```
</details>
   
6. RCPT method on port 25:
<details>
<summary>Example Curl:</summary>

```python
curl -X 'GET' \
  'http://127.0.0.1:8000/verify/rcpt?email=test%40gmail.com&sender_email=info%40filterdns.net&port=25' \
  -H 'accept: application/json'
```
</details>

<details>
<summary>Example False:</summary>

```python
{
  "system_id": "1.0.7",
  "email": "test@gmail.com",
  "message": "No such user!",
  "status": false,
  "MX": [
    "alt3.gmail-smtp-in.l.google.com.",
    "gmail-smtp-in.l.google.com.",
    "alt1.gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com."
  ],
  "smtplib_code": 250,
  "method_code": 550,
  "method": "rcpt",
  "web_auth_code": null,
  "data": "RCPT code: 550, port: 25"
}
```
</details>

<details>
<summary>Example True:</summary>

```python
{
  "system_id": "1.0.7",
  "email": "validemail@gmail.com",
  "message": "Valid email",
  "status": true,
  "MX": [
    "alt1.gmail-smtp-in.l.google.com.",
    "alt3.gmail-smtp-in.l.google.com.",
    "gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com."
  ],
  "smtplib_code": 250,
  "method_code": 250,
  "method": "rcpt",
  "web_auth_code": null,
  "data": "RCPT code: 250, port: 25"
}
```
</details>

When a mailbox exists but is full and cannot receive mail:
<details>
<summary>Example True(quote expired):</summary>

```python
{
  "system_id": "1.0.7",
  "email": "noquote@gmail.com",
  "message": "Quota expired!",
  "status": true,
  "MX": [
    "alt1.gmail-smtp-in.l.google.com.",
    "alt3.gmail-smtp-in.l.google.com.",
    "gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com."
  ],
  "smtplib_code": 250,
  "method_code": 452,
  "method": "rcpt",
  "web_auth_code": null,
  "data": "RCPT code: 452, port: 25"
}
```
</details>

7. VRFY method on port 587:
<details>
<summary>Example Curl:</summary>

```python
   curl -X 'GET' \
  'http://127.0.0.1:8000/verify/vrfy?email=test%40gmail.com&sender_email=info%40filterdns.net&port=587' \
  -H 'accept: application/json'
```
</details>

<details>
<summary>Example False:</summary>

```python
{
  "system_id": "1.0.7",
  "email": "test@gmail.com",
  "message": "SMTP connection failed",
  "status": false,
  "MX": [
    "alt1.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com.",
    "alt3.gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "gmail-smtp-in.l.google.com."
  ],
  "smtplib_code": null,
  "method_code": null,
  "method": null,
  "web_auth_code": null,
  "data": "VRFY error: timed out, port: 587"
}
```
</details>

8. EXPN method on port 465:
<details>
<summary>Example False:</summary>

```python
    {
  "system_id": "1.0.7",
  "email": "test@gmail.com",
  "message": "SMTP connection failed",
  "status": false,
  "MX": [
    "alt3.gmail-smtp-in.l.google.com.",
    "gmail-smtp-in.l.google.com.",
    "alt1.gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com."
  ],
  "smtplib_code": null,
  "method_code": null,
  "method": null,
  "web_auth_code": null,
  "data": "EXPN error: timed out, port: 465"
}
```
</details>

9. MF method on port 25:
<details>
<summary>Example Curl:</summary>

```python
curl -X 'GET' \
  'http://127.0.0.1:8000/verify/mf?email=test%40gmail.com&sender_email=info%40filterdns.net&port=25' \
  -H 'accept: application/json'
```
</details>

<details>
<summary>Example False:</summary>

```python
{
  "system_id": "1.0.7",
  "email": "test@gmail.com",
  "message": "No such user!",
  "status": false,
  "MX": [
    "alt3.gmail-smtp-in.l.google.com.",
    "gmail-smtp-in.l.google.com.",
    "alt1.gmail-smtp-in.l.google.com.",
    "alt2.gmail-smtp-in.l.google.com.",
    "alt4.gmail-smtp-in.l.google.com."
  ],
  "smtplib_code": 250,
  "method_code": 550,
  "method": "mf",
  "web_auth_code": null,
  "data": "MAIL/RCPT code: 550, port: 25"
}
```
</details>

## Configuration for Web Verification

For web-based verification (`-m web`), create `url.cfg` in the project root:

```python
[mail.ru]
user_exists_url=https://account.mail.ru/api/v1/user/exists
requests_file=mail.ru_requests

[yandex.ru]
user_exists_url=https://passport.yandex.ru/auth/check
requests_file=yandex.ru_requests
```

Create requests files (e.g., `mail.ru_requests`):

```python
[method]
type=GET

[headers]
User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept=application/json

[params]
email={email}
```

## License

BSD 3-Clause License. See LICENSE file for details.
