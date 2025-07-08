from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from .mixins import RedirectAuthenticatedUserMixin

class CustomLoginView(RedirectAuthenticatedUserMixin, LoginView):
    template_name = 'registration/login.html'

class CustomPasswordResetView(RedirectAuthenticatedUserMixin, PasswordResetView):
    pass

class CustomPasswordResetDoneView(RedirectAuthenticatedUserMixin, PasswordResetDoneView):
    pass

class CustomPasswordResetConfirmView(RedirectAuthenticatedUserMixin, PasswordResetConfirmView):
    pass

class CustomPasswordResetCompleteView(RedirectAuthenticatedUserMixin, PasswordResetCompleteView):
    pass