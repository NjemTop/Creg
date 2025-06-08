import random
import string
import re
from zxcvbn import zxcvbn


FORBIDDEN_PASSWORDS = [
    'admin123', 'password', 'qwerty', '123456', '12345678', 'abc123'
]

def generate_secure_password(length: int = 12) -> str:
    """
    Генерирует безопасный случайный пароль указанной длины.

    Пароль всегда будет содержать как минимум:
    - 1 заглавную букву (A-Z)
    - 1 строчную букву (a-z)
    - 1 цифру (0-9)

    Остальные символы выбираются случайно из набора A-Za-z0-9.

    Args:
        length (int): Длина пароля (по умолчанию 12). Минимально допустимая длина — 8 символов.

    Returns:
        str: Сгенерированный пароль.

    Raises:
        ValueError: Если передана длина меньше 8 символов.
    
    Примеры:
        >>> generate_secure_password()
        'aZ3k8L1pQw9x'

        >>> generate_secure_password(16)
        'M8zLc9Qr1vB2Xa5p'
    """

    if length < 8:
        raise ValueError("Пароль должен быть не менее 8 символов")

    characters = (
        random.choice(string.ascii_uppercase) +
        random.choice(string.ascii_lowercase) +
        random.choice(string.digits)
    )

    # Добавляем остальные символы случайно
    characters += ''.join(random.choices(
        string.ascii_letters + string.digits, k=length - 3)
    )

    # Перемешиваем символы, чтобы исключить шаблонность
    characters = list(characters)
    random.shuffle(characters)

    return ''.join(characters)


def is_password_strong(password: str, username: str = "") -> bool:
    """
    Проверяет, что пароль надёжный:
    - Достаточно сложный (по zxcvbn)
    - Не содержит имени пользователя
    - Не входит в список простых паролей
    """

    if username.lower() in password.lower():
        return False

    if password.lower() in FORBIDDEN_PASSWORDS:
        return False

    analysis = zxcvbn(password)
    return analysis['score'] >= 3  # от 0 до 4 (3 — «приемлемо», 4 — «очень надёжный»)
