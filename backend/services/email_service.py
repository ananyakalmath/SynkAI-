"""
Email Service for SynkAI.

A thin wrapper around smtplib used for login codes now, and meeting invites/
reminders from Phase 2 onward. The one rule that matters everywhere this is used:
never claim an email was sent when it wasn't — callers get back a result they must
check, not a fire-and-forget call.
"""

import smtplib
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Tuple

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# (filename, content_bytes, mime_subtype) — e.g. ("invite.ics", b"...", "calendar")
Attachment = Tuple[str, bytes, str]


@dataclass
class EmailSendResult:
    success: bool
    error: Optional[str] = None


class EmailService:
    """Sends email via SMTP using credentials from Settings."""

    def send(
        self,
        to: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Attachment]] = None,
        calendar_invite: Optional[Tuple[bytes, str]] = None,
    ) -> EmailSendResult:
        """
        `calendar_invite`, if given, is `(ics_bytes, method)` ("REQUEST" or "CANCEL") —
        sent as a proper `text/calendar; method=...` part, which is what calendar
        clients actually look for to offer "Add to calendar" / "Accept" treatment,
        rather than a plain attachment.
        """
        if not settings.SMTP_HOST:
            message = "SMTP is not configured (SMTP_HOST is empty)."
            logger.error(message)
            return EmailSendResult(success=False, error=message)

        message = MIMEMultipart("mixed")
        message["Subject"] = subject
        message["From"] = settings.MAIL_FROM
        message["To"] = to

        body = MIMEMultipart("alternative")
        body.attach(MIMEText(text_body, "plain"))
        if html_body:
            body.attach(MIMEText(html_body, "html"))
        message.attach(body)

        for filename, content, subtype in attachments or []:
            part = MIMEApplication(content, _subtype=subtype)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            message.attach(part)

        if calendar_invite:
            ics_bytes, method = calendar_invite
            calendar_part = MIMEText(ics_bytes.decode("utf-8"), _subtype="calendar")
            calendar_part.set_param("method", method, header="Content-Type")
            calendar_part.set_param("charset", "UTF-8", header="Content-Type")
            calendar_part.add_header(
                "Content-Disposition", "attachment", filename="invite.ics"
            )
            message.attach(calendar_part)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.MAIL_FROM, [to], message.as_string())
        except Exception as exc:
            logger.error(f"Failed to send email to '{to}': {exc}", exc_info=True)
            return EmailSendResult(success=False, error=str(exc))

        logger.info(f"Email sent to '{to}' (subject: '{subject}').")
        return EmailSendResult(success=True)
