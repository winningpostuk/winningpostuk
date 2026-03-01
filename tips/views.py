
# tips/views.py
from django.shortcuts import render
from django.utils.timezone import localdate
from .models import Tip

# Badge filename mapping
RACECOURSE_BADGES = {
    "aintree": "aintree.png",
    "ascot": "ascot.png",
    "ayr": "ayr.png",
    "bangor-on-dee": "bangor-on-dee.png",
    "bath": "bath.png",
    "beverley": "beverley.png",
    "brighton": "brighton.png",
    "carlisle": "carlisle.png",
    "cartmel": "cartmel.png",
    "catterick": "catterick.png",
    "chelmsford-city": "chelmsford-city.png",
    "cheltenham": "cheltenham.png",
    "chepstow": "chepstow.png",
    "chester": "chester.png",
    "doncaster": "doncaster.png",
    "epsom": "epsom.png",
    "exeter": "exeter.png",
    "fakenham": "fakenham.png",
    "ffos-las": "ffos-las.png",
    "fontwell": "fontwell.png",
    "goodwood": "goodwood.png",
    "hamilton-park": "hamilton-park.png",
    "haydock": "haydock.png",
    "hereford": "hereford.png",
    "hexham": "hexham.png",
    "huntingdon": "huntingdon.png",
    "kelso": "kelso.png",
    "kempton": "kempton.png",
    "leicester": "leicester.png",
    "lingfield": "lingfield.png",
    "ludlow": "ludlow.png",
    "market-rasen": "market-rasen.png",
    "musselburgh": "musselburgh.png",
    "newbury": "newbury.png",
    "newcastle": "newcastle.png",
    "newmarket": "newmarket.png",
    "newton-abbot": "newton-abbot.png",
    "nottingham": "nottingham.png",
    "perth": "perth.png",
    "plumpton": "plumpton.png",
    "redcar": "redcar.png",
    "ripon": "ripon.png",
    "salisbury": "salisbury.png",
    "sandown": "sandown.png",
    "sedgefield": "sedgefield.png",
    "southwell": "southwell.png",
    "stratford": "stratford.png",
    "taunton": "taunton.png",
    "thirsk": "thirsk.png",
    "uttoxeter": "uttoxeter.png",
    "warwick": "warwick.png",
    "wetherby": "wetherby.png",
    "wincanton": "wincanton.png",
    "windsor": "windsor.png",
    "wolverhampton": "wolverhampton.png",
    "worcester": "worcester.png",
    "yarmouth": "yarmouth.png",
    "york": "york.png",
}

def get_badge_for_racecourse(racecourse_name: str | None):
    """Return the badge filename based on racecourse name."""
    if not racecourse_name:
        return None
    key = racecourse_name.lower().replace(" ", "-")
    return RACECOURSE_BADGES.get(key)

def get_todays_tips():
    """
    Return *today's* active Tip objects from the database with badges attached.
    NOTE: Uses race_date (not created_at) to filter the day’s selections.
    """
    today = localdate()
    tips = Tip.objects.filter(active=True, race_date=today).order_by("race_time")

    # Attach badge filenames dynamically (for template convenience)
    for tip in tips:
        tip.badge = get_badge_for_racecourse(tip.racecourse)
    return tips

def todays_tips(request):
    """
    Render Today’s Tips page for members, showing only today's selections.
    """
    tips = get_todays_tips()
    context = {
        "tips": tips,
        "today": localdate(),
    }
    return render(request, "tips/tips.html", context)
