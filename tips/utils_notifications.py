
from __future__ import annotations

from typing import Optional, Dict, Any, List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.timezone import localdate

from members.models import Membership


# -----------------------------
# Internal helpers
# -----------------------------

def _absolute_logo_url(request=None) -> Optional[str]:
    """
    Build an absolute URL for the header logo so email clients can load it.
    Priority:
      1) request.build_absolute_uri(static('images/logo.png')) if request provided
      2) settings.SITE_BASE_URL + static('images/logo.png') if SITE_BASE_URL set
      3) None (template will hide the logo gracefully)
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


def _view_today_url() -> Optional[str]:
    """
    Returns an absolute URL to the 'Today’s Tips' page suitable for emails.
    """
    # Prefer explicit absolute; fall back if provided
    return getattr(settings, "TIPS_TODAY_URL", None)


def _login_url_absolute() -> Optional[str]:
    """
    Returns an absolute URL to the login page for emails.
    """
    # Do not use settings.LOGIN_URL here (that is a path for Django site redirects).
    return getattr(settings, "LOGIN_URL_ABSOLUTE", None)


def _account_manage_url() -> Optional[str]:
    """
    Returns an absolute URL to the user's membership/manage page for emails.
    """
    return getattr(settings, "ACCOUNT_MANAGE_URL", None)


def _render_notification_html(user=None, request=None) -> str:
    """
    Render the HTML email (no tip details).
    Expects template at templates/emails/daily_tips.html
    """
    context: Dict[str, Any] = {
        "user": user,
        "today": localdate(),
        "view_url": _view_today_url(),
        "login_url": _login_url_absolute(),
        "manage_url": _account_manage_url(),
        "absolute_logo_url": _absolute_logo_url(request),
    }
    return render_to_string("emails/daily_tips.html", context)


def _render_notification_text(user=None) -> str:
    """
    Plain-text fallback. No tip details.
    """
    name = getattr(user, "first_name", "") if user else ""
    greeting = f"Hi {name},".strip() if name else "Hi,"

    lines: List[str] = [
        greeting,
        "",
        "Your expert horse racing tips for today are now available on the website.",
        "",
    ]

    today_url = _view_today_url()
    if today_url:
        lines.append(f"View Today’s Tips: {today_url}")

    login_abs = _login_url_absolute()
    if login_abs:
        lines.append(f"Log In: {login_abs}")

    lines.extend(
        [
            "",
            "You're receiving this email because you have an active WinningPostUK subscription.",
        ]
    )

    return "\n".join(lines)


def _active_memberships_with_emails():
    """
    Returns a queryset of active memberships whose related user has a deliverable email.

    Mirrors your previous logic: Membership.active == True
    """
    return (
        Membership.objects.filter(active=True)
        .select_related("user")
        .filter(~Q(user__email__isnull=True) & ~Q(user__email=""))
    )


# -----------------------------
# Public API
# -----------------------------

def send_daily_tip_notification_to_user(user, request=None, fail_silently: bool = False) -> None:
    """
    Sends a single subscriber the notification that today's tips are ready.
    Does NOT include tip content.
    """
    email = getattr(user, "email", None)
    if not email:
        return

    subject = "Today's Tips Are Ready"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "support@winningpostuk.com")
    text = _render_notification_text(user=user)
    html = _render_notification_html(user=user, request=request)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=from_email,
        to=[email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=fail_silently)


def send_daily_tip_notifications(
    batch_size: int = 200,
    request=None,
    personalized: bool = False,
    fail_silently: bool = False,
) -> Dict[str, int]:
    """
    Send “tips are ready” notifications to all active subscribers (Membership.active == True).

    Modes:
      - personalized=True: send one email per user (personal greeting; slower)
      - personalized=False (default): single render + BCC batches (faster & private)

    Returns:
      {"recipients": int, "batches": int}
    """
    subs = _active_memberships_with_emails()
    if not subs.exists():
        return {"recipients": 0, "batches": 0}

    # Build unique user list & email list
    recipients: List[str] = []
    users: List[Any] = []
    for m in subs:
        u = m.user
        email = getattr(u, "email", "")
        if email and email not in recipients:
            recipients.append(email)
            users.append(u)

    if not recipients:
        return {"recipients": 0, "batches": 0}

    subject = "Today's Tips Are Ready"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "support@winningpostuk.com")

    if personalized:
        sent = 0
        for u in users:
            send_daily_tip_notification_to_user(u, request=request, fail_silently=fail_silently)
            sent += 1
        return {"recipients": sent, "batches": sent}

    # Fast BCC-based approach
    text = _render_notification_text(user=None)
    html = _render_notification_html(user=None, request=request)

    batches = 0
    for i in range(0, len(recipients), batch_size):
        chunk = recipients[i : i + batch_size]
        if not chunk:
            continue
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=from_email,
            to=[from_email],     # visible "To" (sender), recipients in BCC for privacy
            bcc=chunk,
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=fail_silently)
        batches += 1

    return {"recipients": len(recipients), "batches": batches}
