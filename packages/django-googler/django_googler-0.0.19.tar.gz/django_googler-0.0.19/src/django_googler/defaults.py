"""
Configuration for django_google OAuth integration.

This module provides a centralized way to manage Google OAuth settings
with sensible defaults that can be overridden in Django settings.

To override any setting, add it to your Django settings.py:
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    GOOGLE_OAUTH_REDIRECT_URIS = ["http://localhost:8000/api/googler/callback"]
    GOOGLE_OAUTH_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    GOOGLE_OAUTH_LOGIN_REDIRECT_URI_NAME = "django_googler_api:google-login"
    GOOGLE_OAUTH_CALLBACK_REDIRECT_URI_NAME = "django_googler_api:google-callback"
    DJANGO_GOOGLER_ALLOW_GET_ON_DRF_CALLBACK = False
"""

from django.conf import settings

# Default settings
DEFAULTS = {
    "GOOGLE_OAUTH_CLIENT_ID": "",
    "GOOGLE_OAUTH_CLIENT_SECRET": "",
    "GOOGLE_OAUTH_REDIRECT_URIS": ["http://localhost:8000/api/googler/callback"],
    "GOOGLE_OAUTH_SCOPES": [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    "GOOGLE_OAUTH_STATE": None,
    "GOOGLE_OAUTH_AUTH_URI": "https://accounts.google.com/o/oauth2/auth",
    "GOOGLE_OAUTH_TOKEN_URI": "https://oauth2.googleapis.com/token",
    # Token handling settings
    "GOOGLE_OAUTH_RETURN_TOKENS": False,  # Return Google tokens in API response
    "GOOGLE_OAUTH_STORE_TOKENS": False,  # Store tokens in session
    "GOOGLE_OAUTH_SAVE_TOKENS_TO_DB": True,  # Save tokens to database
    "GOOGLE_OAUTH_REVOKE_ON_LOGOUT": False,  # Revoke tokens on logout
    # URL names for OAuth redirects
    "GOOGLE_OAUTH_LOGIN_REDIRECT_URI_NAME": "django_googler_api:google-login",
    "GOOGLE_OAUTH_CALLBACK_REDIRECT_URI_NAME": "django_googler_api:google-callback",
    "DJANGO_GOOGLER_ALLOW_GET_ON_DRF_CALLBACK": False,
    # Throttle rates
    "GOOGLE_OAUTH_LOGIN_THROTTLE_RATE": "30/hour",
    "GOOGLE_OAUTH_CALLBACK_THROTTLE_RATE": "100/hour",
}


def get_django_google_setting(name):
    """
    Get a django_google setting from Django settings or return the default.

    Args:
        name: The setting name (e.g., 'GOOGLE_OAUTH_CLIENT_ID')

    Returns:
        The setting value from Django settings, or the default if not set
    """
    return getattr(settings, name, DEFAULTS.get(name))


# Convenience accessors
GOOGLE_OAUTH_CLIENT_ID = get_django_google_setting("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = get_django_google_setting("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT_URIS = get_django_google_setting("GOOGLE_OAUTH_REDIRECT_URIS")
GOOGLE_OAUTH_SCOPES = get_django_google_setting("GOOGLE_OAUTH_SCOPES")
GOOGLE_OAUTH_STATE = get_django_google_setting("GOOGLE_OAUTH_STATE")
GOOGLE_OAUTH_AUTH_URI = get_django_google_setting("GOOGLE_OAUTH_AUTH_URI")
GOOGLE_OAUTH_TOKEN_URI = get_django_google_setting("GOOGLE_OAUTH_TOKEN_URI")
GOOGLE_OAUTH_RETURN_TOKENS = get_django_google_setting("GOOGLE_OAUTH_RETURN_TOKENS")
GOOGLE_OAUTH_STORE_TOKENS = get_django_google_setting("GOOGLE_OAUTH_STORE_TOKENS")
GOOGLE_OAUTH_SAVE_TOKENS_TO_DB = get_django_google_setting(
    "GOOGLE_OAUTH_SAVE_TOKENS_TO_DB"
)
GOOGLE_OAUTH_REVOKE_ON_LOGOUT = get_django_google_setting(
    "GOOGLE_OAUTH_REVOKE_ON_LOGOUT"
)
GOOGLE_OAUTH_LOGIN_REDIRECT_URI_NAME = get_django_google_setting(
    "GOOGLE_OAUTH_LOGIN_REDIRECT_URI_NAME"
)
GOOGLE_OAUTH_CALLBACK_REDIRECT_URI_NAME = get_django_google_setting(
    "GOOGLE_OAUTH_CALLBACK_REDIRECT_URI_NAME"
)
DJANGO_GOOGLER_ALLOW_GET_ON_DRF_CALLBACK = get_django_google_setting(
    "DJANGO_GOOGLER_ALLOW_GET_ON_DRF_CALLBACK"
)
GOOGLE_OAUTH_LOGIN_THROTTLE_RATE = get_django_google_setting(
    "GOOGLE_OAUTH_LOGIN_THROTTLE_RATE"
)
GOOGLE_OAUTH_CALLBACK_THROTTLE_RATE = get_django_google_setting(
    "GOOGLE_OAUTH_CALLBACK_THROTTLE_RATE"
)
