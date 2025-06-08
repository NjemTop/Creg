import re
from django.core.exceptions import ValidationError
from apps.utils.passwords import is_password_strong


def validate_client_password(password: str, client_name: str):
    """
    Валидатор надёжности пароля клиента.

    Бросает ValidationError, если пароль не проходит валидацию.
    """
    if len(password) < 8:
        raise ValidationError("Пароль должен содержать минимум 8 символов.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")
    if not re.search(r"[0-9]", password):
        raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
    if not is_password_strong(password, client_name):
        raise ValidationError("Пароль слишком простой или легко угадывается. Выберите более надёжный.")
