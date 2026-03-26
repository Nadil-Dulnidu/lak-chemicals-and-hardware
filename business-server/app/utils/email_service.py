import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from app.config.logging import get_logger

def get_config_value(*keys, default=None):
    """Lazy import to avoid circular dependency"""
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)

logger = get_logger(__name__)

# ── SMTP configuration ────────────────────────────────────────────────────────
SMTP_HOST = get_config_value("smtp", "smtp_host", default="smtp.gmail.com")
SMTP_PORT = get_config_value("smtp", "smtp_port", default=587)
SENDER_EMAIL = get_config_value("smtp", "sender_email", default="")
SENDER_PASSWORD = get_config_value("smtp", "sender_password", default="")


def _build_approved_html(quotation_id: int, total_amount, discount_amount) -> str:
    """Return an HTML email body for an APPROVED quotation."""
    net_amount = float(total_amount) - float(discount_amount or 0)
    discount_row = (
        f"""
        <tr>
          <td style="padding:8px 0;color:#555;font-size:14px;">Discount Applied</td>
          <td style="padding:8px 0;color:#e53e3e;font-size:14px;text-align:right;">
            - Rs.{float(discount_amount):.2f}
          </td>
        </tr>"""
        if discount_amount and float(discount_amount) > 0
        else ""
    )
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#f7f8fa;margin:0;padding:0;">
      <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:10px;
                  box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;">
        <div style="background:linear-gradient(135deg,#38a169,#276749);padding:32px 40px;">
          <h1 style="color:#fff;margin:0;font-size:24px;">✅ Quotation Approved</h1>
        </div>
        <div style="padding:32px 40px;">
          <p style="color:#333;font-size:16px;margin-top:0;">
            Great news! Your quotation request <strong>#{quotation_id}</strong> has been
            <strong style="color:#38a169;">approved</strong>.
          </p>
          <table style="width:100%;border-top:1px solid #e2e8f0;margin:24px 0;">
            <tr>
              <td style="padding:12px 0;color:#555;font-size:14px;">Quotation ID</td>
              <td style="padding:12px 0;color:#333;font-size:14px;text-align:right;">
                #{quotation_id}
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0;color:#555;font-size:14px;">Original Amount</td>
              <td style="padding:8px 0;color:#333;font-size:14px;text-align:right;">
                Rs.{float(total_amount):.2f}
              </td>
            </tr>
            {discount_row}
            <tr style="border-top:1px solid #e2e8f0;">
              <td style="padding:12px 0;color:#333;font-weight:bold;font-size:15px;">
                Net Amount
              </td>
              <td style="padding:12px 0;color:#38a169;font-weight:bold;font-size:15px;
                         text-align:right;">
                Rs.{net_amount:.2f}
              </td>
            </tr>
          </table>
          <p style="color:#555;font-size:14px;">
            You can now proceed to place your order using this quotation.
            Please log in to your account to continue.
          </p>
        </div>
        <div style="background:#f7f8fa;padding:18px 40px;text-align:center;">
          <p style="color:#aaa;font-size:12px;margin:0;">
            LAK Chemicals &amp; Hardware &nbsp;|&nbsp; This is an automated message.
          </p>
        </div>
      </div>
    </body>
    </html>
    """


def _build_rejected_html(quotation_id: int) -> str:
    """Return an HTML email body for a REJECTED quotation."""
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#f7f8fa;margin:0;padding:0;">
      <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:10px;
                  box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;">
        <div style="background:linear-gradient(135deg,#e53e3e,#9b2c2c);padding:32px 40px;">
          <h1 style="color:#fff;margin:0;font-size:24px;">❌ Quotation Rejected</h1>
        </div>
        <div style="padding:32px 40px;">
          <p style="color:#333;font-size:16px;margin-top:0;">
            We regret to inform you that your quotation request
            <strong>#{quotation_id}</strong> has been
            <strong style="color:#e53e3e;">rejected</strong>.
          </p>
          <p style="color:#555;font-size:14px;">
            This may be due to stock availability or pricing constraints.
            Please feel free to submit a new quotation request or contact us for more
            information.
          </p>
        </div>
        <div style="background:#f7f8fa;padding:18px 40px;text-align:center;">
          <p style="color:#aaa;font-size:12px;margin:0;">
            LAK Chemicals &amp; Hardware &nbsp;|&nbsp; This is an automated message.
          </p>
        </div>
      </div>
    </body>
    </html>
    """


def _send_email_sync(
    recipient_email: str,
    subject: str,
    html_body: str,
) -> bool:
    """
    Send an HTML email synchronously via Gmail SMTP (TLS).
    Returns True on success, False on failure.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        logger.info(
            f"Email sent to {recipient_email} | subject='{subject}'",
            extra={"action": "email_sent"},
        )
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed. Check SENDER_PASSWORD.",
            extra={"action": "email_smtp_auth_error"},
        )
        return False
    except Exception as exc:
        logger.error(
            f"Failed to send email to {recipient_email}: {exc}",
            extra={"action": "email_send_error"},
            exc_info=True,
        )
        return False


async def send_quotation_status_email(
    recipient_email: str,
    quotation_id: int,
    new_status: str,
    total_amount=None,
    discount_amount=None,
) -> bool:
    """
    Async wrapper — sends a quotation status notification email.

    Args:
        recipient_email: Customer's email address.
        quotation_id:    Quotation ID.
        new_status:      'APPROVED' or 'REJECTED'.
        total_amount:    Quotation total (used for APPROVED emails).
        discount_amount: Discount applied (used for APPROVED emails).

    Returns:
        True if the email was dispatched successfully.
    """
    status = new_status.upper()

    if status == "APPROVED":
        subject = f"Your Quotation #{quotation_id} Has Been Approved – LAK Chemicals & Hardware"
        html_body = _build_approved_html(quotation_id, total_amount, discount_amount)
    elif status == "REJECTED":
        subject = f"Update on Your Quotation #{quotation_id} – LAK Chemicals & Hardware"
        html_body = _build_rejected_html(quotation_id)
    else:
        # No email needed for PENDING or other statuses
        return True

    # Run the blocking SMTP call in a thread pool so we don't block the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _send_email_sync, recipient_email, subject, html_body
    )
