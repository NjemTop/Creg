# response_helpers.py

from rest_framework.response import Response
from rest_framework import status

def custom_update_response(instance, request, pk_field, obj_name_field, client_name_field, success_status=status.HTTP_200_OK):
    obj_name = getattr(instance, obj_name_field)
    client_name = getattr(getattr(instance, client_name_field).client_info, 'client_name')
    obj_id = getattr(instance, pk_field)
    return Response(
        {"message": f"Запись '{obj_name}' клиента '{client_name}' с ID '{obj_id}' обновлена"},
        status=success_status,
    )

def custom_delete_response(instance, instance_id, name_field, client_field):
    instance_name = getattr(instance, name_field)
    client_name = getattr(getattr(instance, client_field).client_info, 'client_name')

    response_data = {
        'message': f"Запись '{instance_name}' клиента '{client_name}' с ID '{instance_id}' удалена"
    }
    return Response(response_data, status=status.HTTP_200_OK)
