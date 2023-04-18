from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import ClientSerializer, ContactsCardSerializer
from .renderers import CustomJSONRenderer
from .models import BMInfoOnClient

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_clients(request):
    # Получаем все записи из таблицы BMInfoOnClient
    clients = BMInfoOnClient.objects.all()

    # Сериализуем записи в JSON
    serializer = ClientSerializer(clients, many=True)

    # Возвращаем сериализованные данные и статус 200
    return Response(serializer.data, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([CustomJSONRenderer])
def api_add_client(request):
    data = JSONParser().parse(request)
    serializer = ClientSerializer(data=data)
    if serializer.is_valid():
        new_client = serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def add_client_web(request):
    serializer = ClientSerializer(data=request.data)  # Замените request.POST на request.data
    if serializer.is_valid():
        new_client = serializer.save()

        contacts_data = request.data.get('contacts', [])
        for contact_data in contacts_data:
            contact_data['client_card'] = new_client.clients_card.id
            contact_serializer = ContactsCardSerializer(data=contact_data)

            if contact_serializer.is_valid():
                contact_serializer.save()
            else:
                return Response(contact_serializer.errors, status=400)

        return Response({'id': new_client.id}, status=201)
    return Response(serializer.errors, status=400)
