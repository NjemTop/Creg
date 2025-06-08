from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User, Group
import logging

logger = logging.getLogger(__name__)

class CustomOIDCBackend(OIDCAuthenticationBackend):
    """Кастомный OIDC-бэкенд для Django, обрабатывающий аутентификацию через Keycloak."""

    # Разрешённые группы и административные роли
    ALLOWED_GROUPS = {"support", "manager", "pmo", "product", "dev", "admin"}
    ADMIN_GROUPS = {"admin"}  # Группы, которые получают суперправа

    def filter_users_by_claims(self, claims):
        """Поиск пользователя по email."""
        return User.objects.filter(email=claims.get("email"))

    def create_user(self, claims):
        """Создаёт нового пользователя и назначает группы."""
        user = User.objects.create_user(
            username=claims.get("preferred_username"),
            email=claims.get("email"),
            first_name=claims.get("given_name", ""),
            last_name=claims.get("family_name", ""),
            password=None,  # Django не хранит пароль для OIDC-пользователей
        )

        self._assign_groups(user, claims.get("groups", []))
        return user

    def update_user(self, user, claims):
        """Обновляет группы пользователя при входе."""
        self._assign_groups(user, claims.get("groups", []))
        return user

    def _assign_groups(self, user, groups):
        """Добавляет пользователя в Django-группы и назначает административные права."""
        if not groups:
            logger.warning(f"⚠️ {user.username} зашёл без групп! Доступ будет ограничен.")
            return

        groups_set = set(groups)  # Преобразуем в множество для быстрого поиска

        # Определяем группы, которые разрешены и неизвестные
        valid_groups = groups_set & self.ALLOWED_GROUPS
        unknown_groups = groups_set - self.ALLOWED_GROUPS

        # Логируем неизвестные группы
        if unknown_groups:
            logger.warning(f"⚠️ {user.username} имеет неизвестные группы: {unknown_groups}. Они не будут назначены.")

        # Сбрасываем административные права перед назначением
        user.is_staff = user.is_superuser = False

        # Назначаем только разрешённые группы
        for group_name in valid_groups:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

        # Проверяем, есть ли у пользователя административные группы
        if groups_set & self.ADMIN_GROUPS:
            user.is_staff = user.is_superuser = True
            logger.info(f"⚡ Пользователю {user.username} назначены полные права администратора!")

        user.save()
        logger.info(f"👤 {user.username} теперь состоит в группах: {valid_groups}")
