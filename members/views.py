
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q
from tips.models import Tip
from tips.utils import deactivate_old_tips
from .forms import RegistrationForm, ContactForm
from django.core.mail import send_mail
from .models import ContactMessage, Profile


# -----------------------
# LOGOUT VIEW
# -----------------------
def logout_view(request):
    logout(request)
    return redirect('/')


# -----------------------
# PUBLIC PAGES
# -----------------------
def home(request):
    settled = Tip.objects.filter(settled=True)

    total_settled = settled.count()
    wins = settled.filter(result="WON").count()

    strike_rate = (wins / total_settled * 100) if total_settled else 0
    total_profit = sum(t.profit for t in settled)

    return render(request, 'members/home.html', {
        "strike_rate": round(strike_rate, 1),
        "total_profit": round(total_profit, 2),
    })


def membership(request):
    return render(request, 'members/membership.html')


# -----------------------
# CHECKOUT
# -----------------------
def checkout(request):
    plan = request.GET.get('plan', 'bronze')

    prices = {
        'bronze': '15.00',
        'silver': '42.50',
        'gold': '80.00',
        'platinum': '150.00'
    }

    amount = prices.get(plan, '15.00')
    plan_id = None

    return render(request, 'members/checkout.html', {
        'plan': plan,
        'amount': amount,
        'plan_id': plan_id,
    })


# -----------------------
# PAYMENT SUCCESS
# -----------------------
def success(request):
    username = request.GET.get('username')
    if username:
        try:
            user = User.objects.get(username=username)
            user.is_active = True
            user.save()
        except User.DoesNotExist:
            pass

    return render(request, 'members/success.html')


# -----------------------
# PAYMENT CANCELLED
# -----------------------
def cancel(request):
    return render(request, 'members/cancel.html')


# -----------------------
# DASHBOARD MERGED WITH PERFORMANCE
# -----------------------
@login_required(login_url='/login/')
def dashboard(request):

    today = timezone.now().date()
    range_filter = request.GET.get("range", "all")

    deactivate_old_tips()

    # RANGE FILTER
    if range_filter == "7":
        date_from = today - timedelta(days=7)
    elif range_filter == "30":
        date_from = today - timedelta(days=30)
    elif range_filter == "ytd":
        date_from = today.replace(month=1, day=1)
    else:
        date_from = None

    if date_from:
        settled = Tip.objects.filter(settled=True, race_date__gte=date_from).order_by("race_date")
    else:
        settled = Tip.objects.filter(settled=True).order_by("race_date")

    # KPI METRICS
    total_settled = settled.count()
    wins = settled.filter(result="WON").count()

    strike_rate = (wins / total_settled * 100) if total_settled else 0
    total_profit = sum(t.profit for t in settled)
    roi = (total_profit / total_settled * 100) if total_settled else 0

    # UPDATED CATEGORY STATS
    category_stats = {
        "NAP": settled.filter(category="NAP", result="WON").count(),
        "NB": settled.filter(category="NB", result="WON").count(),
        "To Win": settled.filter(category="WINNER", result="WON").count(),
        "EW": settled.filter(category="EW", result="WON").count(),
        "Dark Horse": settled.filter(category="DARKHORSE", result="WON").count(),
    }

    # CHART DATA
    graph_labels = [t.race_date.strftime("%d %b") for t in settled]
    graph_profit = [float(t.profit) for t in settled]

    strike_rate_labels = []
    strike_rate_values = []

    running_total = 0
    running_wins = 0

    for tip in settled:
        running_total += 1
        if tip.result == "WON":
            running_wins += 1

        strike_rate_labels.append(tip.race_date.strftime("%d %b"))
        strike_rate_values.append(round((running_wins / running_total * 100), 2))

    # COURSE PERFORMANCE
    course_performance = (
        settled.values("racecourse")
        .annotate(
            wins=Count("id", filter=Q(result="WON")),
            placed=Count("id", filter=Q(result="PLACED")),
            total_profit=Sum("profit")
        )
        .order_by("-total_profit")
    )

    # YESTERDAY WINNERS (optional)
    yesterday = today - timedelta(days=1)
    yday_winners = Tip.objects.filter(
        settled=True,
        result="WON",
        created_at__date=yesterday
    )

    return render(request, "members/dashboard.html", {
        "strike_rate": round(strike_rate, 1),
        "roi": round(roi, 1),
        "total_profit": round(total_profit, 2),
        "category_stats": category_stats,
        "graph_labels": graph_labels,
        "graph_profit": graph_profit,
        "strike_rate_labels": strike_rate_labels,
        "strike_rate_values": strike_rate_values,
        "course_performance": course_performance,
        "yday_winners": yday_winners,
        "range_filter": range_filter,
    })


# -----------------------
# USER REGISTRATION
# -----------------------
def register(request):
    if request.user.is_authenticated:
        return redirect('membership')

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )

            profile, created = Profile.objects.get_or_create(user=user)
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.save()

            login(request, user)
            return redirect('membership')

    else:
        form = RegistrationForm()

    return render(request, 'members/register.html', {'form': form})


# -----------------------
# CONTACT FORM
# -----------------------
def contact(request):
    success = False

    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )

            send_mail(
                subject="New Contact Form Submission - Winning Post UK",
                message=(
                    f"Message from: {form.cleaned_data['name']}\n"
                    f"Email: {form.cleaned_data['email']}\n\n"
                    f"Message:\n{form.cleaned_data['message']}"
                ),
                from_email=form.cleaned_data['email'],
                recipient_list=['support@winningpostuk.com'],
            )

            success = True
            form = ContactForm()
    else:
        form = ContactForm()

    return render(request, 'members/contact.html', {
        'form': form,
        'success': success
    })
