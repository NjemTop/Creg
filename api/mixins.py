# mixins.py

from rest_framework import status
from .response_helpers import custom_update_response, custom_delete_response

class CustomResponseMixin:
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            response = custom_update_response(instance, request, 'id', 'bm_servers_servers_name', 'client_card')
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return custom_delete_response(instance, 'id', 'bm_servers_servers_name', 'client_card')
