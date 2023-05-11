# views.py

from rest_framework import generics, mixins, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
import django_filters.rest_framework as filters
import datetime
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from main.models import ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Integration, TechAccountCard, ConnectionInfo, ServiseCard, TechInformationCard
from .mixins import CustomResponseMixin, CustomCreateModelMixin, CustomQuerySetFilterMixin
from .response_helpers import file_upload_error_response, custom_update_response, custom_delete_response
from .serializers import (
    ClientSerializer,
    ContactsSerializer,
    ConnectInfoSerializer,
    BMServersSerializer,
    IntegrationSerializer,
    TechAccountSerializer,
    ConnectionInfoSerializer,
    ServiseSerializer,
    TechInformationSerializer,
)


class ClientFilter(filters.FilterSet):
    """
    Класс фильтрации по клиентам
    """
    client_name = filters.CharFilter(field_name="client_name", lookup_expr='iexact')
    contact_status = filters.BooleanFilter(field_name="contact_status")

    elasticsearch = filters.BooleanFilter(field_name="clients_card__integration__elasticsearch")
    ad = filters.BooleanFilter(field_name="clients_card__integration__ad")
    adfs = filters.BooleanFilter(field_name="clients_card__integration__adfs")
    oauth_2 = filters.BooleanFilter(field_name="clients_card__integration__oauth_2")
    module_translate = filters.BooleanFilter(field_name="clients_card__integration__module_translate")
    ms_oos = filters.BooleanFilter(field_name="clients_card__integration__ms_oos")
    exchange = filters.BooleanFilter(field_name="clients_card__integration__exchange")
    office_365 = filters.BooleanFilter(field_name="clients_card__integration__office_365")
    sfb = filters.BooleanFilter(field_name="clients_card__integration__sfb")
    zoom = filters.BooleanFilter(field_name="clients_card__integration__zoom")
    teams = filters.BooleanFilter(field_name="clients_card__integration__teams")
    smtp = filters.BooleanFilter(field_name="clients_card__integration__smtp")
    cryptopro_dss = filters.BooleanFilter(field_name="clients_card__integration__cryptopro_dss")
    cryptopro_csp = filters.BooleanFilter(field_name="clients_card__integration__cryptopro_csp")
    smpp = filters.BooleanFilter(field_name="clients_card__integration__smpp")
    limesurvey = filters.BooleanFilter(field_name="clients_card__integration__limesurvey")

    server_version = filters.CharFilter(field_name="clients_card__tech_information__server_version", lookup_expr='iexact')
    update_date = filters.DateFilter(field_name="clients_card__tech_information__update_date")
    api = filters.BooleanFilter(field_name="clients_card__tech_information__api")
    ipad = filters.CharFilter(field_name="clients_card__tech_information__ipad", lookup_expr='iexact')
    android = filters.CharFilter(field_name="clients_card__tech_information__android", lookup_expr='iexact')
    mdm = filters.CharFilter(field_name="clients_card__tech_information__mdm", lookup_expr='iexact')
    localizable_web = filters.BooleanFilter(field_name="clients_card__tech_information__localizable_web")
    localizable_ios = filters.BooleanFilter(field_name="clients_card__tech_information__localizable_ios")
    skins_web = filters.BooleanFilter(field_name="clients_card__tech_information__skins_web")
    skins_ios = filters.BooleanFilter(field_name="clients_card__tech_information__skins_ios")

    class Meta:
        model = ClientsList
        fields = ['client_name', 'contact_status', 'elasticsearch', 'ad', 'adfs', 'oauth_2', 'module_translate', 'ms_oos', 'exchange', 'office_365', 'sfb', 'zoom', 'teams', 'smtp', 'cryptopro_dss', 'cryptopro_csp', 'smpp', 'limesurvey', 'server_version', 'update_date', 'api', 'ipad', 'android', 'mdm', 'localizable_web', 'localizable_ios', 'skins_web', 'skins_ios']

class ClientViewSet(viewsets.ModelViewSet):
    """
    tags:
    - Clients
    - All_clients
    """
    queryset = ClientsList.objects.all()
    serializer_class = ClientSerializer
    filterset_class = ClientFilter

    def list(self, request, *args, **kwargs):
        """
        Базовый endpoint, который отдаёт список всех клиентов.
        Есть фильтрация в url строке по важным критериям, которые необходимы для вывода этой информации,
        здесь мы можем как указать версию, по которой мы получим ответ со списком клиентов,
        которые используют эту версию, так и проверить у каких клиентов установлена та или иная интеграция,
        например "/clients/?elasticsearch=true&ad=false", которая вернет всех клиентов,
        у которых интеграция с Elasticsearch, а интеграция AD отсутствует.
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Получить информацию о конкретном клиенте.
        """
        return super().retrieve(request, *args, **kwargs)


response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение о создании записи для клиента'),
    }
)

contact_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'contact_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя контакта'),
        'contact_position': openapi.Schema(type=openapi.TYPE_STRING, description='Должность контакта'),
        'contact_email': openapi.Schema(type=openapi.TYPE_STRING, description='Email контакта'),
        'notification_update': openapi.Schema(type=openapi.TYPE_STRING, description='Уведомление об обновлении'),
        'contact_notes': openapi.Schema(type=openapi.TYPE_STRING, description='Заметки о контакте'),
    }
)

connect_info_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'contact_info_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя контактной информации'),
        'contact_info_account': openapi.Schema(type=openapi.TYPE_STRING, description='Учетная запись контактной информации'),
        'contact_info_password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль контактной информации'),
    }
)

bm_servers_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'bm_servers_circuit': openapi.Schema(type=openapi.TYPE_STRING, description='Server Circuit'),
        'bm_servers_servers_name': openapi.Schema(type=openapi.TYPE_STRING, description='Server Name'),
        'bm_servers_servers_adress': openapi.Schema(type=openapi.TYPE_STRING, description='Server Address'),
        'bm_servers_operation_system': openapi.Schema(type=openapi.TYPE_STRING, description='Operating System'),
        'bm_servers_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL'),
        'bm_servers_role': openapi.Schema(type=openapi.TYPE_STRING, description='Role'),
    }
)

integration_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'elasticsearch': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Elasticsearch'),
        'ad': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='AD'),
        'adfs': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='ADFS'),
        'oauth_2': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='OAuth 2.0'),
        'module_translate': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Module Translate'),
        'ms_oos': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='MS OOS'),
        'exchange': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Exchange'),
        'office_365': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Office 365'),
        'sfb': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='SFB'),
        'zoom': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Zoom'),
        'teams': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Teams'),
        'smtp': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='SMTP'),
        'cryptopro_dss': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='CryptoPro DSS'),
        'cryptopro_csp': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='CryptoPro CSP'),
        'smpp': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='SMPP'),
        'limesurvey': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='LimeSurvey'),
    }
)

tech_account_card_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'contact_info_disc': openapi.Schema(type=openapi.TYPE_STRING, description='Contact Info Description'),
        'contact_info_account': openapi.Schema(type=openapi.TYPE_STRING, description='Contact Info Account'),
        'contact_info_password': openapi.Schema(type=openapi.TYPE_STRING, description='Contact Info Password'),
    }
)

servise_card_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'service_pack': openapi.Schema(type=openapi.TYPE_STRING, description='Service Pack'),
        'manager': openapi.Schema(type=openapi.TYPE_STRING, description='Manager'),
        'loyal': openapi.Schema(type=openapi.TYPE_STRING, description='Loyalty Level'),
    }
)

tech_information_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'server_version': openapi.Schema(type=openapi.TYPE_STRING, description='Server Version'),
        'update_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Update Date'),
        'api': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='API'),
        'localizable_web': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Localizable Web'),
        'localizable_ios': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Localizable iOS'),
        'skins_web': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Skins Web'),
        'skins_ios': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Skins iOS'),
    }
)

request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'client_name': openapi.Schema(type=openapi.TYPE_STRING, description='Client Name'),
        'contacts_card': openapi.Schema(type=openapi.TYPE_ARRAY, items=contact_schema, description='Contacts Card'),
        'connect_info_card': openapi.Schema(type=openapi.TYPE_ARRAY, items=connect_info_schema, description='Connection Info Card'),
        'bm_servers': openapi.Schema(type=openapi.TYPE_ARRAY, items=bm_servers_schema, description='BM Servers'),
        'integration': openapi.Schema(type=openapi.TYPE_ARRAY, items=integration_schema, description='Integration'),
        'tech_account_card': openapi.Schema(type=openapi.TYPE_ARRAY, items=tech_account_card_schema, description='Tech Account Card'),
        'servise_card': openapi.Schema(type=openapi.TYPE_ARRAY, items=servise_card_schema, description='Service Card'),
        'tech_information': openapi.Schema(type=openapi.TYPE_ARRAY, items=tech_information_schema, description='Tech Information'),
    }
)

@swagger_auto_schema(request_body=request_schema, responses={201: openapi.Response("Клиент 'Имя клиента' создан в БД! ID клиента 'id клиента'", response_schema)})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_client(request):
    """
    Endpoint для создания нового клиента со всей необходимой ему информацией.
    """
    if request.method == 'POST':
        client_data = request.data.get("client_name")
        contacts_data = request.data.get("contacts_card")
        connect_info_data = request.data.get("connect_info_card")
        bm_servers_data = request.data.get("bm_servers")
        tech_account_data = request.data.get("tech_account_card")

        # Проверка на существующего клиента
        existing_client = ClientsList.objects.filter(client_name=client_data).first()
        if existing_client:
            return Response({"error": "Клиент уже есть в системе."}, status=status.HTTP_400_BAD_REQUEST)

        if client_data:
            serializer = ClientSerializer(data=request.data)
            if serializer.is_valid():
                client = serializer.save()
                client_card = client.clients_card  # Получаем объект ClientsCard для созданного клиента
                contact_serializer = ContactsSerializer(data=request.data.get('contacts_card', []), many=True)
                if contact_serializer.is_valid():
                    contact_serializer.save(client_card=client_card)  # Передаем объект ClientsCard
                else:
                    client.delete()

                if connect_info_data:
                    for connect_info in connect_info_data:
                        connect_info_serializer = ConnectInfoSerializer(data=connect_info)
                        if connect_info_serializer.is_valid():
                            connect_info_serializer.save(client_card=client_card)
                        else:
                            client.delete()

                if bm_servers_data:
                    for bm_server in bm_servers_data:
                        bm_server_serializer = BMServersSerializer(data=bm_server, context={'request': request})
                        if bm_server_serializer.is_valid():
                            bm_server_serializer.save(client_card=client_card)
                        else:
                            client.delete()

                if tech_account_data:
                    for tech_account in tech_account_data:
                        tech_account_serializer = TechAccountSerializer(data=tech_account)
                        if tech_account_serializer.is_valid():
                            tech_account_serializer.save(client_card=client_card)
                        else:
                            client.delete()

                integration_data = request.data.get("integration", [])
                if integration_data:
                    integration_serializer = IntegrationSerializer(data=integration_data)
                    if integration_serializer.is_valid():
                        integration_serializer.save(client_card=client_card)

                service_data = request.data.get("servise_card", [])
                if service_data:
                    service_serializer = ServiseSerializer(data=service_data)
                    if service_serializer.is_valid():
                        service_serializer.save(client_card=client_card)

                tech_information_data = request.data.get("tech_information", [])
                if tech_information_data:
                    tech_information_serializer = TechInformationSerializer(data=tech_information_data)
                    if tech_information_serializer.is_valid():
                        tech_information_serializer.save(client_card=client_card)

                # Выводим информацию о созданном клиенте
                return Response({"message": f"Клиент {client.client_name} создан в БД! ID клиента {client.pk}."},
                                status=status.HTTP_201_CREATED)
            else:
                return Response(client_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Не предоставлены данные для создания клиента."}, status=status.HTTP_400_BAD_REQUEST)


class ContactsByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    """
    Класс вывода, а также создания нового сотрудника для клиента
    """
    serializer_class = ContactsSerializer
    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)


class ContactDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс для изменения контактов клиента, а также удаление этого контакта
    """
    queryset = ContactsCard.objects.select_related('client_card__client_info')
    serializer_class = ContactsSerializer

    def __init__(self, *args, **kwargs):
        super().__init__('contact_name', 'client_card', *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Выполняет частичное обновление контакта.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки DELETE-запроса.
        Удаляет контакт.
        """
        return self.destroy(request, *args, **kwargs)


class ConnectInfoByClientIdView(CustomCreateModelMixin, generics.ListAPIView):
    """
    Класс вывода учётных записей о подключении к клиенту,
    а также создание новой УЗ для подключения к этому клиенту
    """
    serializer_class = ConnectInfoSerializer

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return ClientsList.objects.filter(id=client_id)

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)


class ConnectInfoDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс представления для обновления и удаления объектов ConnectInfoCard.

    Наследует CustomResponseMixin для настройки пользовательских ответов,
    а также UpdateModelMixin и DestroyModelMixin для выполнения операций обновления и удаления.
    """

    def __init__(self, *args, **kwargs):
        super().__init__('contact_info_name', 'client_card', *args, **kwargs)

    queryset = ConnectInfoCard.objects.select_related('client_card__client_info')
    serializer_class = ConnectInfoSerializer

    def patch(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Обновление объекта ConnectInfoCard с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки DELETE-запроса.
        Удаление объекта ConnectInfoCard.
        """
        return self.destroy(request, *args, **kwargs)


class BMServersByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    """
    Класс BMServersCardByClientIdView обрабатывает HTTP-запросы к связанным данным BMServersCard и ClientsCard.
    Он наследует mixins.CreateModelMixin и generics.ListAPIView для обработки операций создания и получения списка.
    """
    serializer_class = BMServersSerializer

    queryset = BMServersCard.objects.all()
    related_name = "client_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

class BMServersDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс представления для обновления и удаления объектов BMServersCard.

    Наследует CustomResponseMixin для настройки пользовательских ответов,
    а также UpdateModelMixin и DestroyModelMixin для выполнения операций обновления и удаления.
    """
    def __init__(self, *args, **kwargs):
        super().__init__('bm_servers_servers_name', 'client_card', *args, **kwargs)

    queryset = BMServersCard.objects.select_related('client_card__client_info')
    serializer_class = BMServersSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта BMServersCard с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта BMServersCard.
        """
        return self.destroy(request, *args, **kwargs)


class IntegrationByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    """
    Класс вывода информации о интеграциях клиента,
    а также добавления этой информации если ещё нет
    """
    def get_serializer_class(self):
        return IntegrationSerializer

    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

class IntegrationDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс изменения информации об интеграциях клиента,
    а также удаления этой информации полностью.
    """
    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = Integration.objects.select_related('client_card__client_info')
    serializer_class = IntegrationSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта Integration с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта Integration.
        """
        return self.destroy(request, *args, **kwargs)


class TechAccountByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    """
    Класс вывода тех. информации об УЗ, которые использует клиент для своих сервисов,
    а также добавлени этих УЗ
    """
    serializer_class = TechAccountSerializer
    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

class TechAccountDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = TechAccountCard.objects.select_related('client_card__client_info')
    serializer_class = TechAccountSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта TechAccountCard с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта TechAccountCard.
        """
        return self.destroy(request, *args, **kwargs)


class FileUploadView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ConnectionInfo.objects.all()
    serializer_class = ConnectionInfoSerializer
    parser_classes = [MultiPartParser]

    def post(self, request, client_id):
        """
        Метод для обработки POST-запроса на загрузку файла.
        Загружает файл и сохраняет информацию о файле в базе данных.
        :param request: Объект HTTP запроса
        :param client_id: ID клиента
        :return: Response объект с результатом загрузки файла
        """
        client_card = get_object_or_404(ClientsCard, id=client_id)

        if 'file' not in request.FILES:
            return file_upload_error_response(
                "Файл не найден",
                "Пожалуйста, убедитесь, что вы включили файл в запрос с ключом 'file'."
            )

        file = request.FILES['file']
        text = request.data.get('text', None)

        connection_info = ConnectionInfo(client_card=client_card, file_path=file, text=text)
        connection_info.save()

        return Response(
            {
                'сообщение': 'Файл успешно загружен и сохранен в базе данных',
                'имя файла': connection_info.file_path.name
            },
            status=status.HTTP_201_CREATED
        )
    
    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Обрабатываем новый файл
        if 'file' in request.FILES:
            new_file = request.FILES['file']
            # Удаляем старый файл
            instance.file_path.delete(save=False)
            # Заменяем его на новый файл  
            instance.file_path = new_file

        self.perform_update(serializer)
        return custom_update_response(instance, request, 'id', 'file_path', 'client_card')

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        # Удаляем файл в папке перед удалением записи
        if instance.file_path:
            instance.file_path.delete(save=False)

        self.perform_destroy(instance)
        return custom_delete_response(instance, instance_id, 'file_path', 'client_card')

class ClientFilesView(generics.ListAPIView):
    serializer_class = ConnectionInfoSerializer

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return ConnectionInfo.objects.filter(client_card__id=client_id)


class ServiseByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    serializer_class = ServiseSerializer
    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

class ServiseDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = ServiseCard.objects.select_related('client_card__client_info')
    serializer_class = ServiseSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта ServiseCard с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта ServiseCard.
        """
        return self.destroy(request, *args, **kwargs)


class TechInformationByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    serializer_class = TechInformationSerializer
    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

    def post(self, request, *args, **kwargs):
        # Если 'update_date' не предоставлен, устанавливаем сегодняшнюю дату
        if 'update_date' not in request.data:
            request.data['update_date'] = datetime.date.today().strftime('%Y-%m-%d')

        return super().post(request, *args, **kwargs)

class TechInformationDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = TechInformationCard.objects.select_related('client_card__client_info')
    serializer_class = TechInformationSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта TechInformationCard с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта TechInformationCard.
        """
        return self.destroy(request, *args, **kwargs)

























# class ClientIdFilter(filters.BaseFilterBackend):
#     def filter_queryset(self, request, queryset, view):
#         client_id = request.query_params.get('client_id', None)
#         if client_id is not None:
#             queryset = queryset.filter(client_id__client_info__id=client_id)
#         return queryset

# class ClientsViewSet(viewsets.ModelViewSet):
#     """
#     ClientsViewSet предоставляет CRUD операции для модели ClientsList.
#     """
#     queryset = ClientsList.objects.all()  # Получение всех объектов ClientsList
#     serializer_class = ClientsListSerializer  # Указание сериализатора для ClientsList
#     permission_classes = [permissions.IsAuthenticated]  # Установка прав доступа для данного класса

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())

#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# class ContactsViewSet(viewsets.ModelViewSet):
#     """
#     ContactsViewSet предоставляет CRUD операции для модели ContactsCard.
#     """
#     serializer_class = ContactsSerializer  # Указание сериализатора для ContactsCard

#     def get_queryset(self):
#         """
#         Возвращает queryset контактов для определенного клиента или всех контактов, если client_id не указан.
#         """
#         client_id = self.kwargs.get('client_id', None)  # Получение client_id из параметров запроса
#         if client_id is not None:
#             try:
#                 client = ClientsList.objects.get(id=client_id)  # Получение объекта клиента по client_id
#                 return ContactsCard.objects.filter(client_card__client_info=client)  # Фильтрация контактов по клиенту
#             except ClientsList.DoesNotExist:  # Обработка исключения, если клиент с указанным client_id не найден
#                 return ContactsCard.objects.none()  # Возвращение пустого queryset
#         else:
#             return ContactsCard.objects.all()  # Возвращение всех контактов

#     def list_all(self, request, *args, **kwargs):
#         """
#         Возвращает список всех контактов с учетом пагинации.
#         """
#         queryset = self.filter_queryset(self.get_queryset().filter(client_card__isnull=False))  # Фильтрация контактов с привязкой к клиентам

#         page = self.paginate_queryset(queryset)  # Применение пагинации к queryset
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)  # Сериализация данных с пагинацией
#             return self.get_paginated_response(serializer.data)  # Возвращение данных с пагинацией

#         serializer = self.get_serializer(queryset, many=True)  # Сериализация всех данных
#         return Response(serializer.data)  # Возвращение всех сериализованных данных

# class ConnectInfoViewSet(viewsets.ModelViewSet):
#     queryset = СonnectInfoCard.objects.all()
#     serializer_class = СonnectInfoCardSerializer
#     filter_backends = [ClientIdFilter]

#     def get_permissions(self):
#         # Устанавливаем разрешения для разных действий
#         if self.action == 'create' and 'client_id' in self.kwargs:
#             permission_classes = [permissions.IsAuthenticated]
#         else:
#             permission_classes = [permissions.IsAuthenticated]
#         return [permission() for permission in permission_classes]

#     def get_queryset(self):
#         # Возвращаем соответствующий queryset в зависимости от наличия client_id
#         client_id = self.kwargs.get('client_id', None)
#         if client_id is not None:
#             try:
#                 client = ClientsList.objects.get(id=client_id)
#                 return СonnectInfoCard.objects.filter(client_id__client_info=client)
#             except ClientsList.DoesNotExist:
#                 return СonnectInfoCard.objects.none()
#         else:
#             return СonnectInfoCard.objects.all()

#     def create(self, request, *args, **kwargs):
#         # Получаем client_id из аргументов
#         client_id = kwargs.get('client_id', None)

#         # Если client_id предоставлен, продолжаем
#         if client_id is not None:

#             # Пытаемся найти клиента с указанным client_id
#             try:
#                 client = ClientsCard.objects.get(client_info_id=client_id)

#                 # Создаем сериализатор с переданными данными
#                 serializer = self.get_serializer(data=request.data)

#                 # Если сериализатор валиден, сохраняем данные и возвращаем ответ
#                 if serializer.is_valid():
#                     serializer.save(client_id=client)
#                     return Response(serializer.data, status=status.HTTP_201_CREATED)
#                 else:
#                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#             # Если клиент не найден, возвращаем ошибку 404
#             except ClientsCard.DoesNotExist:
#                 return Response({"error": "Клиент не найден"}, status=status.HTTP_404_NOT_FOUND)

#         # Если client_id не предоставлен, возвращаем ошибку 400
#         else:
#             return Response({"error": "Клиент ID не предоставлен"}, status=status.HTTP_400_BAD_REQUEST)

#     def update(self, request, *args, **kwargs):
#         # Получение ID записи из URL
#         connect_info_id = kwargs.get('pk', None)

#         if connect_info_id is not None:
#             try:
#                 # Получение объекта СonnectInfoCard с указанным ID
#                 connect_info = СonnectInfoCard.objects.get(id=connect_info_id)

#                 # Сериализация объекта с новыми данными и разрешение частичного обновления
#                 serializer = self.get_serializer(connect_info, data=request.data, partial=True)

#                 if serializer.is_valid():
#                     # Сохранение обновленного объекта
#                     serializer.save()
#                     return Response(serializer.data, status=status.HTTP_200_OK)
#                 else:
#                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#             except СonnectInfoCard.DoesNotExist:
#                 return Response({"error": "ConnectInfo not found"}, status=status.HTTP_404_NOT_FOUND)
#         else:
#             return Response({"error": "ConnectInfo ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

#     def destroy(self, request, *args, **kwargs):
#         # Получение ID записи из URL
#         connect_info_id = kwargs.get('pk', None)

#         if connect_info_id is not None:
#             try:
#                 # Получение объекта СonnectInfoCard с указанным ID
#                 connect_info = СonnectInfoCard.objects.get(id=connect_info_id)

#                 # Удаление объекта
#                 connect_info.delete()

#                 # Возврат ответа с кодом 204 (NO CONTENT), указывающим на успешное удаление
#                 return Response(status=status.HTTP_204_NO_CONTENT)
#             except СonnectInfoCard.DoesNotExist:
#                 return Response({"error": "ConnectInfo not found"}, status=status.HTTP_404_NOT_FOUND)
#         else:
#             return Response({"error": "ConnectInfo ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
        