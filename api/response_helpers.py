# response_helpers.py

from rest_framework.response import Response
from rest_framework import status


def custom_create_response(instance, client_id, client_card, success_status=status.HTTP_201_CREATED):
    """
    Функция для создания пользовательского ответа после успешного создания объекта.
    :param instance: Созданный объект модели
    :param client_id: ID клиента
    :param client_card: Экземпляр объекта ClientsCard
    :param success_status: Код статуса успешного ответа (по умолчанию 201)
    :return: Response объект с пользовательским сообщением и кодом статуса
    """

    # Получаем имя клиента
    client_name = client_card.client_info.client_name

    # Создаем словарь с данными для ответа
    response_data = {
        "message": f"Запись для клиента {client_name} успешно создалась"
    }

    # Возвращаем Response объект с данными и кодом статуса
    return Response(response_data, status=success_status)


def custom_update_response(instance, request, pk_field, obj_name_field, client_name_field, success_status=status.HTTP_200_OK):
    """
    Функция для создания пользовательского ответа после успешного обновления объекта.
    :param instance: Обновленный объект модели
    :param request: Объект HTTP запроса
    :param pk_field: Название поля с первичным ключом (ID) объекта
    :param obj_name_field: Название поля с именем объекта (например, название сервера)
    :param client_name_field: Название поля с информацией о клиенте, которому принадлежит объект
    :param success_status: Код статуса успешного ответа (по умолчанию 200)
    :return: Response объект с пользовательским сообщением и кодом статуса
    """

    # Получаем имя объекта, имя клиента и ID объекта
    obj_name = getattr(instance, obj_name_field)
    client_name = getattr(getattr(instance, client_name_field).client_info, 'client_name')
    obj_id = getattr(instance, pk_field)

    # Создаем словарь с данными для ответа
    response_data = {
        "message": f"Запись '{obj_name}' клиента '{client_name}' с ID '{obj_id}' обновлена"
    }

    # Возвращаем Response объект с данными и кодом статуса
    return Response(response_data, status=success_status)

def custom_delete_response(instance, instance_id, name_field, client_field):
    """
    Функция для создания пользовательского ответа после успешного удаления объекта.
    :param instance: Удаленный объект модели
    :param instance_id: ID удаленного объекта
    :param name_field: Название поля с именем объекта (например, название сервера)
    :param client_field: Название поля с информацией о клиенте, которому принадлежал объект
    :return: Response объект с пользовательским сообщением и кодом статуса
    """

    # Получаем имя объекта и имя клиента
    instance_name = getattr(instance, name_field)
    client_name = getattr(getattr(instance, client_field).client_info, 'client_name')

    # Создаем словарь с данными для ответа
    response_data = {
        "message": f"Запись '{instance_name}' клиента '{client_name}' с ID '{instance_id}' удалена"
    }

    # Возвращаем Response объект с данными и кодом статуса
    return Response(response_data, status=status.HTTP_200_OK)
