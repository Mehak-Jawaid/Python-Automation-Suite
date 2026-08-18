"""Email Sender — send an email with optional attachment using env credentials."""

from __future__ import annotations

import argparse
import mimetypes
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send an email using EMAIL_ADDRESS and EMAIL_PASSWORD env vars.",
    )
    parser.add_argument("-t", "--to", help="Recipient email address")
    parser.add_argument("-s", "--subject", help="Email subject")
    parser.add_argument("-b", "--body", help="Plain-text body")
    parser.add_argument(
        "--body-file",
        help="Read body text from a file instead of --body",
    )
    parser.add_argument("-a", "--attachment", help="Optional file to attach")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    return parser.parse_args(argv)


def load_dotenv_if_present() -> None:
    """Load a local .env file if present, without requiring python-dotenv."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        # Project .env wins for EMAIL_* so local config is predictable
        if key.startswith("EMAIL_"):
            os.environ[key] = value
        elif key and key not in os.environ:
            os.environ[key] = value


def get_credentials() -> tuple[str, str]:
    address = os.environ.get("EMAIL_ADDRESS", "").strip()
    password = os.environ.get("EMAIL_PASSWORD", "").strip()
    if not address:
        raise ValueError(
            "EMAIL_ADDRESS is not set. See README.md for setup instructions."
        )
    if not password:
        raise ValueError(
            "EMAIL_PASSWORD is not set. Use an app password — never hard-code it."
        )
    if "@" not in address:
        raise ValueError("EMAIL_ADDRESS does not look like a valid email.")
    return address, password


def smtp_settings() -> tuple[str, int]:
    host = os.environ.get("EMAIL_SMTP_HOST", "smtp.gmail.com").strip()
    port_raw = os.environ.get("EMAIL_SMTP_PORT", "587").strip()
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError("EMAIL_SMTP_PORT must be a number.") from exc
    return host, port


def validate_email(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or "@" not in cleaned or "." not in cleaned.split("@")[-1]:
        raise ValueError(f"{label} does not look like a valid email: {value}")
    return cleaned


def validate_attachment(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"Attachment not found: {path}")
    if not resolved.is_file():
        raise ValueError(f"Attachment is not a file: {path}")
    return resolved


def prompt_text(label: str, *, required: bool = True) -> str:
    value = input(f"{label}: ").strip()
    if required and not value:
        raise ValueError(f"{label} is required.")
    return value


def prompt_attachment() -> Path | None:
    raw = input("Attachment (optional, Enter to skip): ").strip().strip('"')
    if not raw:
        return None
    return validate_attachment(Path(raw))


def build_message(
    *,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    attachment: Path | None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body if body else "(no body)")

    if attachment is not None:
        mime_type, _ = mimetypes.guess_type(str(attachment))
        if mime_type is None:
            maintype, subtype = "application", "octet-stream"
        else:
            maintype, subtype = mime_type.split("/", 1)
        message.add_attachment(
            attachment.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment.name,
        )
    return message


def preview(
    *,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    attachment: Path | None,
    host: str,
    port: int,
) -> None:
    print(f"\nFrom       : {sender}")
    print(f"Recipient  : {recipient}")
    print(f"Subject    : {subject}")
    print(f"SMTP       : {host}:{port}")
    print(f"Attachment : {attachment.name if attachment else '(none)'}")
    print("\nBody:")
    preview_body = body if body else "(no body)"
    for line in preview_body.splitlines()[:12]:
        print(f"  {line}")
    if preview_body.count("\n") >= 12:
        print("  …")
    print()


def confirm(prompt: str = "Send email? [y/n]: ") -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def send_email(message: EmailMessage, *, sender: str, password: str, host: str, port: int) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.send_message(message)


def run(
    *,
    recipient: str,
    subject: str,
    body: str,
    attachment: Path | None,
    skip_confirm: bool = False,
) -> int:
    try:
        sender, password = get_credentials()
        host, port = smtp_settings()
    except ValueError as exc:
        print(f"\nError: {exc}")
        return 1

    preview(
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        attachment=attachment,
        host=host,
        port=port,
    )

    if not skip_confirm and not confirm():
        print("Cancelled. No email was sent.")
        return 0

    try:
        message = build_message(
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            attachment=attachment,
        )
        send_email(message, sender=sender, password=password, host=host, port=port)
    except smtplib.SMTPAuthenticationError:
        print(
            "\nError: login failed. Check EMAIL_ADDRESS / EMAIL_PASSWORD.\n"
            "  Gmail: use an App Password + smtp.gmail.com\n"
            "  Hotmail/Outlook: use an App Password + smtp-mail.outlook.com"
        )
        return 1
    except smtplib.SMTPException as exc:
        print(f"\nError sending email: {exc}")
        return 1
    except OSError as exc:
        print(f"\nError: {exc}")
        return 1

    print(f"\nOK: email sent to {recipient}")
    return 0


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_present()
    args = parse_args(argv)

    print("Email Sender")
    print("------------")

    try:
        if args.to:
            recipient = validate_email(args.to, "Recipient")
        else:
            print()
            recipient = validate_email(prompt_text("Recipient"), "Recipient")

        if args.subject is not None:
            subject = args.subject.strip()
            if not subject:
                raise ValueError("Subject is required.")
        else:
            subject = prompt_text("Subject")

        if args.body_file:
            body_path = Path(args.body_file).expanduser().resolve()
            if not body_path.is_file():
                raise ValueError(f"Body file not found: {args.body_file}")
            body = body_path.read_text(encoding="utf-8")
        elif args.body is not None:
            body = args.body
        else:
            print("Body (end with a blank line):")
            lines: list[str] = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            body = "\n".join(lines)

        if args.attachment:
            attachment = validate_attachment(Path(args.attachment))
        elif args.to is None:
            # Interactive only — ask about attachment
            attachment = prompt_attachment()
        else:
            attachment = None

        return run(
            recipient=recipient,
            subject=subject,
            body=body,
            attachment=attachment,
            skip_confirm=args.yes,
        )
    except ValueError as exc:
        print(f"\nError: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
