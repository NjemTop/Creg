from rest_framework import serializers
from .models import BMInfoOnClient, ClientsCard

class ClientsCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientsCard
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    clients_card = ClientsCardSerializer(required=False)

    class Meta:
        model = BMInfoOnClient
        fields = ('id', 'client_name', 'contact_status', 'service', 'technical_information', 'integration', 'documents', 'notes', 'clients_card')

    def create(self, validated_data):
        clients_card_data = validated_data.pop('clients_card', None)
        
        # Создайте объект BMInfoOnClient сначала, чтобы получить его ID
        bm_info_on_client = BMInfoOnClient.objects.create(**validated_data)

        # Затем создайте объект ClientsCard с указанием только что созданного объекта BMInfoOnClient
        if clients_card_data is None:
            clients_card = ClientsCard.objects.create(client_info=bm_info_on_client)
        else:
            clients_card_data['client_info'] = bm_info_on_client
            clients_card = ClientsCardSerializer.create(ClientsCardSerializer(), validated_data=clients_card_data)
            
        bm_info_on_client.clients_card = clients_card
        bm_info_on_client.save()

        return bm_info_on_client
