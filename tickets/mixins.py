from django.contrib.auth.mixins import UserPassesTestMixin

class AdminOrAgentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == 'agent'