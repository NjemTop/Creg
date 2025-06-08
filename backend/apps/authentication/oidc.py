from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class OIDCAuthenticationCallback(OIDCAuthenticationBackend):
    def create_user(self, claims):
        """Создаёт пользователя, если он не существует."""
        user = super().create_user(claims)
        user.email = claims.get("email", "")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.is_staff = "admin" in claims.get("roles", [])
        user.save()
        return user

    def update_user(self, user, claims):
        """Обновляет данные пользователя."""
        user.email = claims.get("email", "")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user
