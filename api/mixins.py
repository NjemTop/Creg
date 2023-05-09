# mixins.py

from rest_framework import status
from .response_helpers import custom_create_response, custom_update_response, custom_delete_response
from rest_framework.response import Response

class CustomCreateModelMixin:
    def post(self, request, *args, **kwargs):
        data = request.data
        client_id = self.kwargs['client_id']
        client_card = self.get_client_card(client_id)

        if isinstance(data, list):
            serializer = self.get_serializer(data=data, many=True)
        elif isinstance(data, dict):
            serializer = self.get_serializer(data=data)
        else:
            return Response({"error": "Недопустимый формат данных. Ожидался список или словарь."}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            instance = serializer.save(client_card=client_card)
            return custom_create_response(instance, client_id, client_card)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_card(self, client_id):
        raise NotImplementedError("Метод `get_client_card` должен быть реализован.")


class CustomQuerySetFilterMixin:
    """
    Универсальный миксин для фильтрации QuerySet на основе клиентского идентификатора и related_name.
    related_name - это атрибут, который связывает модель с другой моделью через ForeignKey.
    """
    related_name = None  # Устанавливаем related_name как None по умолчанию

    def get_queryset(self):
        # Если related_name не установлен, вызываем ошибку с указанием на необходимость его установки
        if self.related_name is None:
            raise ValueError("Необходимо установить 'related_name' для CustomQuerySetFilterMixin.")

        client_id = self.kwargs['client_id']  # Получаем идентификатор клиента из аргументов запроса

        # Фильтруем QuerySet, используя переданный related_name и идентификатор клиента, и возвращаем результат
        return self.queryset.filter(**{f"{self.related_name}__client_info__id": client_id})

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
