from django.urls import path
from .views import login_view, logout_view, local_login_view, oidc_login

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("local-login/", local_login_view, name="local_login"),
    path("oidc-login/", oidc_login, name="oidc_login"),
]
