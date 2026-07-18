"""
Outbound email via SMTP (Gmail App Password supported).

Env:
  SMTP_HOST     default smtp.gmail.com
  SMTP_PORT     default 587 (STARTTLS)
  SMTP_USER     sender login (e.g. Gmail address)
  SMTP_PASS     app password (spaces optional)
  SMTP_FROM     optional From header (defaults to SMTP_USER)
  SMTP_DEV_ECHO if true, also return reset codes in API (local debug only)
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_USER", "").strip() and os.getenv("SMTP_PASS", "").strip())


def smtp_dev_echo() -> bool:
    return os.getenv("SMTP_DEV_ECHO", "").lower() in {"1", "true", "yes"}


def _settings() -> dict[str, str | int]:
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "").replace(" ", "").strip()
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "from_addr": os.getenv("SMTP_FROM", user).strip() or user,
    }


def send_email(*, to: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured (set SMTP_USER and SMTP_PASS)")

    cfg = _settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = str(cfg["from_addr"])
    msg["To"] = to
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(str(cfg["host"]), int(cfg["port"]), timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(str(cfg["user"]), str(cfg["password"]))
        server.send_message(msg)


def send_password_reset_email(*, to: str, reset_code: str) -> None:
    subject = "VedyaAI password reset code"
    text_body = (
        f"Your VedyaAI password reset code is: {reset_code}\n\n"
        "This code expires in 30 minutes.\n"
        "If you did not request a reset, you can ignore this email.\n"
    )
    html_body = f"""\
<html><body style="font-family: system-ui, sans-serif; color: #1a1a1a;">
  <p>Your <strong>VedyaAI</strong> password reset code is:</p>
  <p style="font-size: 1.75rem; letter-spacing: 0.2em; font-weight: 700;">{reset_code}</p>
  <p>This code expires in <strong>30 minutes</strong>.</p>
  <p style="color: #666;">If you did not request a reset, you can ignore this email.</p>
</body></html>
"""
    send_email(to=to, subject=subject, text_body=text_body, html_body=html_body)
