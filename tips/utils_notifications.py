
# tips/utils_notifications.py
from __future__ import annotations

from typing import Iterable, List, Dict, Optional
import time
import logging
from smtplib import SMTPServerDisconnected, SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.timezone import localdate
from django.db.models import Q

from members.models import Membership

logger = logging.getLogger(__name__)


def _absolute_logo_url(request=None) -> Optional[str]:
    """
    Build an absolute URL to the logo for email clients.
    """
    logo_path = static("images/logo.png")
    if request is not None:
        try:
            return request.build_absolute_uri(logo_path)
        except Exception:
            pass
    base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    if base:
        return f"{base}{logo_path}"
    return None


def _render_notification_html(
    view_url: Optional[str],
    login_url: Optional[str],
    manage_url: Optional[str],
    request=None
) -> str:
    """
    Render the minimal 'tips are ready' email once (no per-user content).
    """
    context = {
        "user": None,  # no personalization to keep memory and time low
        "today": localdate(),
        "view_url": view_url,
        "login_url": login_url,
        "manage_url": manage_url,
        "absolute_logo_url": _absolute_logo_url(request),
    }
    return render_to_string("emails/daily_tips.html", context)


def _render_notification_text(
    view_url: Optional[str],
    login_url: Optional[str],
    manage_url: Optional[str]
) -> str:
    """
    Plain-text fallback for clients that do not render HTML.
    """
    lines = [
        "Hi,",
        "",
        "Your expert horse racing tips for today are now available on the website.",
        "",
    ]
    if view_url:
        lines.append(f"View Today’s Tips: {view_url}")
    if login_url:
        lines.append(f"Log In: {login_url}")
    if manage_url:
        lines.append(f"Manage membership: {manage_url}")
    lines.append("")
    lines.append("You’re receiving this email because you have an active subscription.")
    return "\n".join(lines)


def _active_member_emails_iter() -> Iterable[str]:
    """
    Stream active subscriber emails with minimal memory.
    - Uses iterator() so we don't load the entire queryset into RAM.
    - Filters out null/empty emails.
    - If you need stricter 'paid' logic, adjust the filters here.
    """
    qs = (
        Membership.objects.filter(active=True)
        .select_related("user")
        .filter(~Q(user__email__isnull=True) & ~Q(user__email=""))
        .values_list("user__email", flat=True)
        .iterator(chunk_size=1000)
    )
    for email in qs:
        yield email


def _chunked(iterable: Iterable[str], size: int) -> Iterable[List[str]]:
    """
    Yield lists from iterable in chunks of `size`.
    """
    batch: List[str] = []
    for item in iterable:
        if item:
            batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def send_daily_tip_notifications(
    *,
    batch_size: int = 50,
    sleep_between_batches: float = 1.5,
    max_recipients: Optional[int] = None,
    request=None,
) -> Dict[str, int]:
    """
    Render-safe batched notification sender that avoids timeouts and OOM.

    - Renders HTML once (no per-user personalization).
    - Batches recipients (BCC) to reduce SMTP calls and memory.
    - Reuses SMTP connection and retries once on disconnect.
    - Returns summary dict for admin messages.

    Args:
        batch_size: number of recipients per email (BCC). Keep <= 50 for Gmail.
        sleep_between_batches: seconds to sleep between SMTP sends (throttle).
        max_recipients: if set, stops after sending to this many recipients (safety).
        request: optional HttpRequest for absolute logo URL.

    Returns:
        {"recipients": int, "batches": int, "skipped": int}
    """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)
    subject = "Today's Tips Are Ready"

    view_url = getattr(settings, "TIPS_TODAY_URL", None)
    login_url = getattr(settings, "LOGIN_URL_ABSOLUTE", None)
    manage_url = getattr(settings, "ACCOUNT_MANAGE_URL", None)

    # Render templates once
    html = _render_notification_html(view_url, login_url, manage_url, request=request)
    text = _render_notification_text(view_url, login_url, manage_url)

    recipients_sent = 0
    batches_sent = 0
    skipped = 0

    # Build a generator of emails; we may limit them by max_recipients
    email_iter = _active_member_emails_iter()

    if max_recipients is not None and max_recipients > 0:
        def limited_iter():
            nonlocal recipients_sent, skipped
            count = 0
            for e in email_iter:
                if count >= max_recipients:
                    skipped += 1
                    continue
                count += 1
                yield e
        email_iter = limited_iter()

    # Reuse a single SMTP connection for throughput and to avoid connect storms
    connection = None
    try:
        connection = get_connection(
            fail_silently=False,
            username=getattr(settings, "EMAIL_HOST_USER", None),
            password=getattr(settings, "EMAIL_HOST_PASSWORD", None),
            timeout=getattr(settings, "EMAIL_TIMEOUT", 15),  # add in settings if not present
        )
        connection.open()

        for batch in _chunked(email_iter, batch_size):
            if not batch:
                continue

            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text,
                    from_email=from_email,
                    to=[from_email],       # visible TO
                    bcc=batch,             # recipients in BCC for privacy
                    connection=connection,
                )
                msg.attach_alternative(html, "text/html")
                msg.send()

            except SMTPServerDisconnected:
                # Retry once by reopening connection
                logger.warning("SMTP disconnected during batch; retrying once…")
                try:
                    connection.close()
                except Exception:
                    pass
                connection = get_connection(
                    fail_silently=False,
                    username=getattr(settings, "EMAIL_HOST_USER", None),
                    password=getattr(settings, "EMAIL_HOST_PASSWORD", None),
                    timeout=getattr(settings, "EMAIL_TIMEOUT", 15),
                )
                connection.open()
                # Try send again once
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text,
                    from_email=from_email,
                    to=[from_email],
                    bcc=batch,
                    connection=connection,
                )
                msg.attach_alternative(html, "text/html")
                msg.send()

            except SMTPException as e:
                logger.error("SMTP error while sending batch: %s", e, exc_info=True)
                # Continue with next batch rather than fail the whole action
                continue

            recipients_sent += len(batch)
            batches_sent += 1

            # Throttle to reduce provider suspicion / rate limits
            if sleep_between_batches and sleep_between_batches > 0:
                time.sleep(sleep_between_batches)

    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    return {"recipients": recipients_sent, "batches": batches_sent, "skipped": skipped}

