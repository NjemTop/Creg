from django import template
from django.forms import BoundField

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Добавляет CSS-класс к полю формы, но проверяет тип перед применением."""
    if isinstance(field, BoundField):  # Проверяем, что это поле формы
        return field.as_widget(attrs={'class': css_class})
    return field  # Если это просто строка, возвращаем её без изменений
