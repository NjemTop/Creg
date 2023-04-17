from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from .models import Client
from .serializers import ClientSerializer
from .renderers import CustomJSONRenderer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([CustomJSONRenderer])
def api_get_clients(request):
    clients = Client.objects.all()
    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([CustomJSONRenderer])
def api_add_client(request):
    data = JSONParser().parse(request)
    serializer = ClientSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
