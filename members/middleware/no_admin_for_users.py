
from django.shortcuts import redirect

class BlockNormalUsersFromAdmin:
    """
    Allow admin login page and admin assets.
    Block only the admin dashboard for non-staff users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # 1) Allow all admin login pages (important!)
        if path.startswith('/admin/login'):
            return self.get_response(request)

        if path.startswith('/admin/logout'):
            return self.get_response(request)

        if path.startswith('/admin/password_reset'):
            return self.get_response(request)

        # 2) Allow admin static assets
        if path.startswith('/admin/js') or path.startswith('/admin/css') or path.startswith('/admin/img'):
            return self.get_response(request)

        # 3) Now block NAVIGATING TO ADMIN if user is not staff
        if path.startswith('/admin/'):

            # If user is not logged in → allow login to load
            if not request.user.is_authenticated:
                return self.get_response(request)

            # If logged in but not staff → block
            if not request.user.is_staff:
                return redirect('/')

        return self.get_response(request)
