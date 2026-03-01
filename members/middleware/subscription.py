
from django.shortcuts import redirect
from django.urls import reverse
from members.models import Membership

class SubscriptionRequiredMiddleware:

    PUBLIC_EXACT = {
        '/',
        '/login/',
        '/register/',
        '/password_reset/',
        '/password_reset_done/',
        '/reset/',
        '/reset/done/',
        '/membership/',
        '/checkout/',
        '/success/',
        '/cancel/',
        '/contact/',
    }

    PUBLIC_PREFIXES = (
        '/static/',
        '/admin/',
    )


    PROTECTED_PREFIXES = (
    '/members/',
    '/dashboard/',
    '/tips/',
    '/performance/',
)


    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # DEBUG PRINT — to confirm the middleware is actually running
        print("SUBSCRIPTION MIDDLEWARE RUNNING:", request.path)

        path = request.path

        # 1. Exact public paths
        if path in self.PUBLIC_EXACT:
            return self.get_response(request)

        # 2. Public prefixes (static/admin)
        if path.startswith(self.PUBLIC_PREFIXES):
            return self.get_response(request)

        # 3. Protected members area
        if path.startswith(self.PROTECTED_PREFIXES):

            if not request.user.is_authenticated:
                return redirect(reverse('login'))

            membership = Membership.objects.filter(user=request.user).first()

            if not membership or not membership.active:
                return redirect(reverse('membership'))

        return self.get_response(request)
