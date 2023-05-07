# mixins.py

from rest_framework import status
from .response_helpers import custom_update_response, custom_delete_response

class CustomResponseMixin:
    """
    Миксин для создания пользовательских ответов при частичном обновлении (PATCH) и удалении (DELETE) объектов модели.
    """

    def __init__(self, obj_name_field, client_name_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obj_name_field = obj_name_field
        self.client_name_field = client_name_field

    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление объекта модели с пользовательским ответом.
        :param request: Объект HTTP запроса
        :param args: Дополнительные аргументы
        :param kwargs: Дополнительные именованные аргументы
        :return: Response объект с пользовательским сообщением и кодом статуса
        """

        # Получаем объект, который нужно обновить
        instance = self.get_object()

        # Вызываем стандартное частичное обновление и сохраняем результат в переменную response
        response = super().partial_update(request, *args, **kwargs)

        # Если статус ответа 200, то заменяем ответ на пользовательский
        if response.status_code == 200:
            response = custom_update_response(instance, request, 'id', self.obj_name_field, self.client_name_field)
        
        # Возвращаем ответ
        return response

    def destroy(self, request, *args, **kwargs):
        """
        Удаление объекта модели с пользовательским ответом.
        :param request: Объект HTTP запроса
        :param args: Дополнительные аргументы
        :param kwargs: Дополнительные именованные аргументы
        :return: Response объект с пользовательским сообщением и кодом статуса
        """

        # Получаем объект, который нужно удалить
        instance = self.get_object()

        # Сохраняем ID объекта перед удалением
        instance_id = instance.id

        # Выполняем стандартное удаление объекта
        self.perform_destroy(instance)

        # Возвращаем пользовательский ответ с сохраненным ID объекта
        return custom_delete_response(instance, instance_id, self.obj_name_field, self.client_name_field)
