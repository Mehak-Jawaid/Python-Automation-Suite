# Email Sender

Send an email with an optional attachment. Credentials come from environment variables — never hard-code passwords.

**Example**

```
Email Sender
------------

Recipient: client@example.com
Subject: Monthly Report
Attachment: report.pdf

Send email? [y/n]: y

OK: email sent to client@example.com
```

## Security rules

Do **not** write:

```python
password = "mypassword123"
```

Use:

```text
EMAIL_ADDRESS
EMAIL_PASSWORD
```

- Never commit `.env` or real passwords to Git
- Prefer an **App Password** (Gmail) over your real account password
- The script never prints your password

## Requirements

- Python 3.10+ (stdlib only — no `pip install` needed)
- An email account with SMTP access

## Setup (Gmail)

1. Turn on [2-Step Verification](https://myaccount.google.com/security)
2. Create an [App Password](https://myaccount.google.com/apppasswords)
3. Copy `.env.example` to `.env` and fill it in:

```powershell
cd email_sender
copy .env.example .env
```

```env
EMAIL_ADDRESS=you@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
```

Or set variables for the current PowerShell session:

```powershell
$env:EMAIL_ADDRESS = "you@gmail.com"
$env:EMAIL_PASSWORD = "your-app-password"
```

Other providers: set `EMAIL_SMTP_HOST` and `EMAIL_SMTP_PORT` (default is Gmail `smtp.gmail.com:587`).

## Usage

### Interactive

```powershell
python sender.py
```

### Command line

```powershell
python sender.py -t client@example.com -s "Monthly Report" -b "Hi, report attached." -a report.pdf
```

| Flag | Meaning |
|------|---------|
| `-t`, `--to` | Recipient |
| `-s`, `--subject` | Subject |
| `-b`, `--body` | Plain-text body |
| `--body-file` | Read body from a text file |
| `-a`, `--attachment` | Optional file to attach |
| `-y`, `--yes` | Skip confirmation |

## What you'll practice

- Environment variables for secrets
- SMTP / email libraries (`smtplib`, `email`)
- File attachments
- Error handling (auth failures, bad paths)
- Confirm-before-send UX
