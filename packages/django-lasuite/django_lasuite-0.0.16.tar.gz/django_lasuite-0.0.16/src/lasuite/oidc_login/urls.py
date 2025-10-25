"""Authentication URLs for the OIDC backend."""

from django.urls import path
from mozilla_django_oidc.urls import urlpatterns as mozilla_oidc_urls

from .views import OIDCBackChannelLogoutView, OIDCLogoutCallbackView, OIDCLogoutView

urlpatterns = [
    # Override the default 'logout/' path from Mozilla Django OIDC with our custom view.
    path("logout/", OIDCLogoutView.as_view(), name="oidc_logout_custom"),
    path(
        "logout-callback/",
        OIDCLogoutCallbackView.as_view(),
        name="oidc_logout_callback",
    ),
    path(
        "backchannel-logout/",
        OIDCBackChannelLogoutView.as_view(),
        name="oidc_backchannel_logout",
    ),
    *mozilla_oidc_urls,
]
