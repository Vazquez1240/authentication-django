from django.conf import settings

DEFAULTS = {
    "SECRET_KEY": "default-secret-key",
    "TOKEN_ALGORITHM": "HS256",
}

class UsersAuthSettings:
    def __init__(self, defaults=None):
        self.defaults = defaults or DEFAULTS

    def __getattr__(self, attr):
        if hasattr(settings, "DJANGO_USERS_AUTH_TOKEN"):
            return settings.USERS_AUTH.get(attr, self.defaults.get(attr))
        return self.defaults.get(attr)

users_auth_settings = UsersAuthSettings()
