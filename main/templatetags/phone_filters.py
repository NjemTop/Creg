from django import template
import re

register = template.Library()

@register.filter(name='phone_format')
def phone_format(value):
    # Проверяем, что значение не пустое и состоит из ожидаемого количества цифр
    if not value or not re.match(r'^\d{11}$', value):
        return value  # Не форматируем, если значение не соответствует ожидаемому формату
    
    # Регулярное выражение для соответствие формату номера телефона "79052124755" -> "+7 (905) 212-47-55"
    formatted_phone_number = re.sub(r"(\d)(\d{3})(\d{3})(\d{2})(\d{2})", r"+\1 (\2) \3-\4-\5", value)
    return formatted_phone_number
