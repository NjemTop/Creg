# response_helpers.py

from rest_framework.response import Response
from rest_framework import status

def custom_update_response(instance, request, pk_field, obj_name_field, client_name_field, success_status=status.HTTP_200_OK):
    obj_name = getattr(instance, obj_name_field)
    client_name = getattr(getattr(instance, client_name_field).client_info, 'client_name')
    obj_id = getattr(instance, pk_field)
    return Response(
        {"message": f"{obj_name}' клиента '{client_name}' с ID '{obj_id}' обновлён"},
        status=success_status,
    )

def custom_delete_response(instance, pk_field, obj_name_field, client_name_field, success_status=status.HTTP_204_NO_CONTENT):
    obj_name = getattr(instance, obj_name_field)
    client_name = getattr(getattr(instance, client_name_field).client_info, 'client_name')
    obj_id = getattr(instance, pk_field)
    return Response(
        {"message": f"{obj_name}' клиента '{client_name}' с ID '{obj_id}' удалён"},
        status=success_status,
    )
