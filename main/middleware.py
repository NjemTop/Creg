import logging
from django.db import OperationalError
from django.shortcuts import render

logger = logging.getLogger(__name__)

class CustomDatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except OperationalError:
            logger.error("Database connection failed. Rendering custom error page.")
            response = render(request, 'main/error/custom_db_error.html', status=503)
        return response
