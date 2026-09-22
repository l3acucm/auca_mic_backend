from django.conf import settings
from moses.authentication import MFAModelBackend


class SingleTenantMFAModelBackend(MFAModelBackend):
    """`MFAModelBackend.authenticate()` scopes users by `site__domain`, a kwarg
    the API passes explicitly — but Django's built-in /admin/login/ form never
    passes it, so every admin login fails with "incorrect credentials" no
    matter the password. Single-tenant deploy (one Site) — default `domain`
    to settings.DOMAIN. See scaffold-backend's moses.md."""

    def authenticate(self, request, username=None, password=None, domain=None, **kwargs):
        return super().authenticate(
            request, username=username, password=password,
            domain=domain or settings.DOMAIN, **kwargs
        )
