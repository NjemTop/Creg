from rest_framework import serializers
from .models import BMInfoOnClient

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = BMInfoOnClient
        fields = ('id', 'client_name', 'contact_status', 'service', 'technical_information', 'integration', 'documents', 'notes')
