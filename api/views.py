# views.py

from rest_framework import generics, mixins, viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.http import JsonResponse
from django.core import serializers
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.views import APIView
import django_filters.rest_framework as filters
from django_filters import BaseInFilter
from django.views import View
from django.db.models import Q
from django.db.models import F
from urllib.parse import unquote
import datetime
import logging
import threading
import os
from dotenv import load_dotenv
from scripts.jfrog.add_user_JFrog import generate_random_password, authenticate, create_user
from scripts.tfs.create_client_TFS import trigger_tfs_pipeline
from scripts.nextcloud.manager_nextcloud import NextCloudManager
from .email_send import send_email_alert_async
from django.shortcuts import get_object_or_404, get_list_or_404
from .swagger_schemas import request_schema, response_schema
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from main.models import (ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, 
BMServersCard, Integration, ModuleCard, TechAccountCard, ConnectionInfo, ServiseCard, 
TechInformationCard, TechNote, ReleaseInfo, ReportTicket, UsersBoardMaps)
from .mixins import CustomResponseMixin, CustomCreateModelMixin, CustomQuerySetFilterMixin
from .response_helpers import file_upload_error_response, custom_update_response, custom_delete_response
from .serializers import (
    ClientSerializer,
    ContactsSerializer,
    ConnectInfoSerializer,
    BMServersSerializer,
    IntegrationSerializer,
    ModuleSerializer,
    TechAccountSerializer,
    ConnectionInfoSerializer,
    ServiseSerializer,
    TechInformationSerializer,
    TechNoteSerializer,
    ClientsListSerializer,
    Version2ClientsSerializer,
    Version3ClientsSerializer,
    ReleaseInfoSerializer,
    ReportTicketSerializer,
    UsersBoardMapsSerializer,
)


load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

NEXTCLOUD_URL = os.environ.get('NEXTCLOUD_URL')
NEXTCLOUD_USER = os.environ.get('NEXTCLOUD_USER')
NEXTCLOUD_PASSWORD = os.environ.get('NEXTCLOUD_PASSWORD')

# Инициализация экземпляра NextCloud
create_nextcloud_account = NextCloudManager(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)


def create_user_in_jfrog(username, password):
    cookies = authenticate()
    if cookies:
        create_user(username, password, cookies)


class ClientSearch(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        clients = ClientsList.objects.filter(
            Q(client_name__icontains=query) | 
            Q(clients_card__tech_information__server_version__icontains=query)
        )[:5]
        clients_info = list(clients.values('id', 'client_name', 'clients_card__tech_information__server_version'))
        return JsonResponse(clients_info, safe=False)


class MultipleValueFilter(filters.BaseInFilter, filters.CharFilter):
    pass

# class NonEmptyMDMFilter(filters.BooleanFilter):
#     """
#     Фильтр, который возвращает записи, у которых поле 'mdm' не пустое.
#     """

#     def filter(self, qs, value):
#         if value in filters.constants.EMPTY_VALUES:
#             return qs

#         q = Q(**{f'{self.field_name}__isnull': False}) & ~Q(**{f'{self.field_name}': ''})
#         return qs.filter(q)

class ClientFilter(filters.FilterSet):
    """
    Класс фильтрации по клиентам
    """
    
    def list(self, request, *args, **kwargs):
        """
        Базовый endpoint, который отдаёт список всех клиентов.
        Есть фильтрация в url строке по важным критериям, которые необходимы для вывода этой информации,
        здесь мы можем как указать версию, по которой мы получим ответ со списком клиентов,
        которые используют эту версию, так и проверить у каких клиентов установлена та или иная интеграция,
        например "/clients/?elasticsearch=true&ad=false", которая вернет всех клиентов,
        у которых интеграция с Elasticsearch, а интеграция AD отсутствует.
        """

        # Обработка и удаление лишних символов из параметров запроса
        params = request.query_params.copy()
        for key, values in params.lists():
            # Применяем функцию unquote для удаления лишних символов
            cleaned_values = [unquote(value.replace(",", "").replace("%2C", "")) for value in values]
            cleaned_values = [value for value in cleaned_values if value.lower() not in ["null", "undefined"]]
            if cleaned_values:
                params.setlist(key, cleaned_values)
            else:
                del params[key]

        request.query_params = params

        # Продолжение обработки запроса с обновленными значениями фильтров
        return super().list(request, *args, **kwargs)

    # Фильтр по Наименоанию клиента и его активности
    client_name = filters.CharFilter(field_name="client_name", lookup_expr='iexact')
    contact_status = filters.BooleanFilter(field_name="contact_status")

    # Фильтр по интеграциям
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

    # Фильтр по технической информации
    server_version = filters.CharFilter(field_name="clients_card__tech_information__server_version", lookup_expr='iexact')
    update_date = filters.DateFilter(field_name="clients_card__tech_information__update_date")
    api = filters.BooleanFilter(field_name="clients_card__tech_information__api")
    ipad = filters.CharFilter(field_name="clients_card__tech_information__ipad", lookup_expr='iexact')
    android = filters.CharFilter(field_name="clients_card__tech_information__android", lookup_expr='iexact')
    # mdm = filters.CharFilter(field_name="clients_card__tech_information__mdm", lookup_expr='isnull', exclude=True)
    mdm = filters.Filter(field_name="clients_card__tech_information__mdm", method='filter_by_mdm')

    def filter_by_mdm(self, queryset, name, value):
        # Если значение равно 'true' (независимо от регистра), мы фильтруем строки, в которых MDM не является пустой строкой.
        if value.lower() == 'true':
            lookup = '{}__{}'.format(name, 'gt')
            return queryset.filter(**{lookup: ''})
        # Если значение равно 'false' (независимо от регистра), мы фильтруем строки, в которых MDM является пустой строкой.
        elif value.lower() == 'false':
            lookup = '{}__{}'.format(name, 'exact')
            return queryset.filter(**{lookup: ''})
        else:
            # Если значение не равно 'true' или 'false', мы возвращаем исходный queryset без фильтрации.
            return queryset

    localizable_web = filters.BooleanFilter(field_name="clients_card__tech_information__localizable_web")
    localizable_ios = filters.BooleanFilter(field_name="clients_card__tech_information__localizable_ios")
    skins_web = filters.BooleanFilter(field_name="clients_card__tech_information__skins_web")
    skins_ios = filters.BooleanFilter(field_name="clients_card__tech_information__skins_ios")

    # Фильтр по модулям
    translate = filters.BooleanFilter(field_name="clients_card__module__translate")
    electronic_signature = filters.BooleanFilter(field_name="clients_card__module__electronic_signature")
    action_items = filters.BooleanFilter(field_name="clients_card__module__action_items")
    limesurvey = filters.BooleanFilter(field_name="clients_card__module__limesurvey")
    advanced_voting = filters.BooleanFilter(field_name="clients_card__module__advanced_voting")
    advanced_work_with_documents = filters.BooleanFilter(field_name="clients_card__module__advanced_work_with_documents")
    advanced_access_rights_management = filters.BooleanFilter(field_name="clients_card__module__advanced_access_rights_management")
    visual_improvements = filters.BooleanFilter(field_name="clients_card__module__visual_improvements")
    third_party_product_integrations = filters.BooleanFilter(field_name="clients_card__module__third_party_product_integrations")
    microsoft_enterprise_product_integrations = filters.BooleanFilter(field_name="clients_card__module__microsoft_enterprise_product_integrations")
    microsoft_office_365_integration = filters.BooleanFilter(field_name="clients_card__module__microsoft_office_365_integration")

    # Фильтр по обслуживанию
    service_pack = filters.CharFilter(field_name="clients_card__servise_card__service_pack", lookup_expr='iexact')
    manager = filters.CharFilter(field_name="clients_card__servise_card__manager", lookup_expr='iexact')

    # Фильтр по контактам
    contact_name = filters.CharFilter(field_name="clients_card__contact_cards__contact_name", lookup_expr='icontains')
    contact_email = filters.CharFilter(field_name="clients_card__contact_cards__contact_email", lookup_expr='icontains')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Проверка значений фильтров и исключение "null"
        filters_to_exclude = []
        for name, field in self.filters.copy().items():
            if name in self.data:
                values = self.data.getlist(name)  # Получаем список значений
                if "null" in values or "[]" in values:
                    filters_to_exclude.append(name)
                else:
                    # Обновляем фильтр с методом фильтрации, принимающим список значений
                    self.filters[name] = MultipleValueFilter(field_name=field.field_name, lookup_expr='in')

        for name in filters_to_exclude:
            del self.filters[name]

    # Добавляем поле сортировки по алфавиту client_name
    order_by_client_name = filters.OrderingFilter(
        fields=(
            ('client_name', 'client_name'),  # Сортировка по возрастанию
            ('-client_name', 'client_name_desc'),  # Сортировка по убыванию
        ),
        field_labels={
            'client_name': 'Client Name (A-Z)',
            'client_name_desc': 'Client Name (Z-A)',
        }
    )

    # Добавляем поле сортировки по активному статусу contact_status
    order_by_contact_status = filters.OrderingFilter(
        fields=(
            ('contact_status', 'active_first'),  # Сортировка активных клиентов вначале
            ('-contact_status', 'inactive_first'),  # Сортировка неактивных клиентов вначале
        ),
        field_labels={
            'active_first': 'Active Clients',
            'inactive_first': 'Inactive Clients',
        }
    )

    class Meta:
        model = ClientsList
        fields = [
            'client_name', 'contact_status', 'elasticsearch', 'ad', 'adfs', 'oauth_2',
            'module_translate', 'ms_oos', 'exchange', 'office_365', 'sfb', 'zoom', 'teams',
            'smtp', 'cryptopro_dss', 'cryptopro_csp', 'smpp', 'limesurvey', 'server_version',
            'update_date', 'api', 'ipad', 'android', 'mdm', 'localizable_web', 'localizable_ios',
            'skins_web', 'skins_ios', 'translate', 'electronic_signature', 'action_items',
            'limesurvey', 'advanced_voting', 'advanced_work_with_documents',
            'advanced_access_rights_management', 'visual_improvements',
            'third_party_product_integrations', 'microsoft_enterprise_product_integrations',
            'microsoft_office_365_integration', 'service_pack', 'manager',
            'contact_name', 'contact_email',
            'order_by_client_name',
            'order_by_contact_status',
        ]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # По умолчанию сортируем по алфавиту client_name
        ordering = self.request.query_params.get('ordering', 'client_name')
        if ordering.startswith('client_name'):
            queryset = queryset.order_by(F('client_name').asc(nulls_last=True))
        elif ordering.startswith('-client_name'):
            queryset = queryset.order_by(F('client_name').desc(nulls_last=True))

        # Если указано поле сортировки по активному статусу contact_status, то сортируем
        if ordering.startswith('contact_status'):
            queryset = queryset.order_by(F('contact_status').desc())

        return queryset

class ClientViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]
    """
    tags:
    - Clients
    - All_clients
    """
    queryset = ClientsList.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [filters.DjangoFilterBackend]
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


@swagger_auto_schema(methods=['post'], request_body=request_schema, responses={201: openapi.Response("Клиент 'Имя клиента' создан в БД! ID клиента 'id клиента'", response_schema)})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_client(request):
    """
    Endpoint для создания нового клиента со всей необходимой ему информацией.
    """

    additional_data = {}

    if request.method == 'POST':
        client_data = request.data.get("client_name")
        contacts_data = request.data.get("contacts_card")
        connect_info_data = request.data.get("connect_info_card")
        bm_servers_data = request.data.get("bm_servers")
        tech_account_data = request.data.get("tech_account_card")
        integration_data = request.data.get("integration", None)
        module_data = request.data.get("module", None)
        service_data = request.data.get("servise_card", None)
        tech_information_data = request.data.get("tech_information", None)

        # Проверка на существующего клиента
        existing_client = ClientsList.objects.filter(client_name=client_data).first()
        if existing_client:
            return Response({"error": "Клиент уже есть в системе."}, status=status.HTTP_400_BAD_REQUEST)

        if client_data:
            serializer = ClientSerializer(data=request.data)
            if serializer.is_valid():
                client = serializer.save()
                client_card = client.clients_card  # Получаем объект ClientsCard для созданного клиента

                # Генерируем пароль и сохраняем его в объект клиента
                password = generate_random_password()
                client.password = password
                client.save()

                # Асинхронно запускаем скрипт для создания пользователя в JFrog
                username = client.short_name
                jfrog_thread = threading.Thread(target=create_user_in_jfrog, args=(username, password))
                jfrog_thread.start()

                # Асинхронно запускаем скрипт для создания пользователя в TFS
                client_name = client.client_name
                tfs_thread = threading.Thread(target=trigger_tfs_pipeline, args=(client_name,))
                tfs_thread.start()

                # Асинхронно запускаем скрипт для создания пользователя в NextCloud
                nextcloud_thread = threading.Thread(target=create_nextcloud_account.execute_all, args=(client.client_name, client.short_name, client.short_name))
                nextcloud_thread.start()

                # from api.tasks import add_user_jfrog_task
                # add_user_jfrog_task.apply_async((username, password), countdown=600)

                contact_serializer = ContactsSerializer(data=request.data.get('contacts_card', []), many=True)
                if contact_serializer.is_valid():
                    contact_serializer.save(client_card=client_card)  # Передаем объект ClientsCard
                    additional_data['Контакты клиента'] = str(contacts_data) # Добавляем информацию в словарь
                else:
                    logger.error(f'Ошибка записи данных об информации о контактах {contact_serializer.errors}')
                    client.delete()

                if connect_info_data:
                    for connect_info in connect_info_data:
                        connect_info_serializer = ConnectInfoSerializer(data=connect_info)
                        if connect_info_serializer.is_valid():
                            connect_info_serializer.save(client_card=client_card)
                            additional_data['Информация о подключениях к клиенту'] = str(connect_info) # Добавляем информацию в словарь
                        else:
                            logger.error(f'Ошибка записи данных о подключениях {connect_info_serializer.errors}')
                            client.delete()

                if bm_servers_data:
                    for bm_server in bm_servers_data:
                        bm_server_serializer = BMServersSerializer(data=bm_server, context={'request': request})
                        if bm_server_serializer.is_valid():
                            bm_server_serializer.save(client_card=client_card)
                            additional_data['Сервера BoardMaps'] = str(bm_server) # Добавляем информацию в словарь
                        else:
                            logger.error(f'Ошибка записи данных о серварах ВМ {bm_server_serializer.errors}')
                            client.delete()

                if tech_account_data:
                    for tech_account in tech_account_data:
                        tech_account_serializer = TechAccountSerializer(data=tech_account)
                        if tech_account_serializer.is_valid():
                            tech_account_serializer.save(client_card=client_card)
                            additional_data['Техническая учётная запись'] = str(tech_account) # Добавляем информацию в словарь
                        else:
                            logger.error(f'Ошибка записи данных о тех. УЗ {tech_account_serializer.errors}')
                            client.delete()

                if integration_data:
                    integration_serializer = IntegrationSerializer(data=integration_data)
                    if integration_serializer.is_valid():
                        integration_serializer.save(client_card=client_card)
                        # Добавляем информацию в словарь для отправки алерта на почту
                        additional_data['Интеграции'] = str(integration_data)
                    else:
                        logger.error(f'Ошибка записи данных о интеграциях {integration_serializer.errors}')
                
                if module_data:
                    module_serializer = ModuleSerializer(data=module_data)
                    if module_serializer.is_valid():
                        module_serializer.save(client_card=client_card)
                        additional_data['Модули'] = str(module_data) # Добавляем информацию в словарь
                    else:
                        logger.error(f'Ошибка записи данных о модулях {module_serializer.errors}')

                if service_data:
                    service_serializer = ServiseSerializer(data=service_data)
                    if service_serializer.is_valid():
                        service_serializer.save(client_card=client_card)
                        additional_data['Обслуживание'] = str(service_data) # Добавляем информацию в словарь
                    else:
                        logger.error(f'Ошибка записи данных об обслуживании  {service_serializer.errors}')

                if tech_information_data:
                    # Проверяем наличие даты обновления
                    if 'update_date' not in tech_information_data:
                        tech_information_data['update_date'] = datetime.date.today()  # Устанавливаем текущую дату, если не указана
                    tech_information_serializer = TechInformationSerializer(data=tech_information_data)
                    if tech_information_serializer.is_valid():
                        tech_information_serializer.save(client_card=client_card)
                        additional_data['Техническая информация'] = str(tech_information_data) # Добавляем информацию в словарь
                    else:
                        logger.error(f'Ошибка записи данных о тех. информации {tech_information_serializer.errors}')
                
                # Отправляем алерт на почту
                client_data = {
                    'client_name': client.client_name,
                    'short_name': client.short_name,
                    'password': password,
                }
                email_thread = threading.Thread(target=send_email_alert_async, args=(client_data, additional_data))
                email_thread.start()

                # Логируем запись созданного клиента
                logger.info(f"Клиент {client.client_name} создан в БД! ID клиента {client.pk}.")
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

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]
    
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

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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
        logger.info('Получение класса сериализатора')
        return IntegrationSerializer

    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        logger.info(f'Получение client card для client ID {client_id}')
        return ClientsCard.objects.get(client_info_id=client_id)

class IntegrationDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс изменения информации об интеграциях клиента,
    а также удаления этой информации полностью.
    """

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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


class ModuleCardByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    """
    Класс вывода информации о интеграциях клиента,
    а также добавления этой информации если ещё нет
    """
    def get_serializer_class(self):
        logger.info('Получение класса сериализатора')
        return ModuleSerializer

    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        logger.info(f'Получение client card для client ID {client_id}')
        return ClientsCard.objects.get(client_info_id=client_id)

class ModuleCardDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс изменения информации об интеграциях клиента,
    а также удаления этой информации полностью.
    """

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = ModuleCard.objects.select_related('client_card__client_info')
    serializer_class = ModuleSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта ModuleCard с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта ModuleCard.
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

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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

class TextUploadView(generics.CreateAPIView):
    queryset = ConnectionInfo.objects.all()
    serializer_class = ConnectionInfoSerializer
    parser_classes = [JSONParser]

    def post(self, request, client_id):
        client_card = get_object_or_404(ClientsCard, id=client_id)
        text = request.data.get('text', None)
        connection_info = ConnectionInfo(client_card=client_card, text=text)
        connection_info.save()

        return Response(
            {
                'message': 'Текст успешно загружен и сохранен в базе данных',
                'text': connection_info.text
            },
            status=status.HTTP_201_CREATED
        )

class TextUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):

    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

    queryset = ConnectionInfo.objects.all()
    serializer_class = ConnectionInfoSerializer
    parser_classes = [JSONParser]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        instance.text = request.data.get('text', instance.text)
        instance.save()
        
        return Response(
            {
                'message': 'Текст успешно обновлен',
                'text': instance.text
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        return Response(
            {
                'message': 'Запись успешно удалена',
            },
            status=status.HTTP_204_NO_CONTENT
        )

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
    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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
    
    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]

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
    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]
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


class TechNoteByClientIdView(CustomCreateModelMixin, CustomQuerySetFilterMixin, generics.ListAPIView):
    serializer_class = TechNoteSerializer
    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

class TechNoteDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = TechNote.objects.select_related('client_card__client_info')
    serializer_class = TechNoteSerializer

    def patch(self, request, *args, **kwargs):
        """
        Обновление объекта TechNote с использованием метода PATCH.
        """
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Метод для обработки PATCH-запроса.
        Метод для обработки DELETE-запроса.
        Удаление объекта TechNote.
        """
        return self.destroy(request, *args, **kwargs)


class ClientsListView(generics.ListAPIView):
    queryset = ClientsList.objects.all()
    serializer_class = ClientsListSerializer

class Version2ClientsView(generics.ListAPIView):
    queryset = ClientsList.objects.filter(clients_card__tech_information__server_version__startswith='2')
    serializer_class = Version2ClientsSerializer

class Version3ClientsView(generics.ListAPIView):
    queryset = ClientsList.objects.filter(clients_card__tech_information__server_version__startswith='3')
    serializer_class = Version3ClientsSerializer


class ReleaseInfoFilter(filters.FilterSet):
    release_number = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ReleaseInfo
        fields = ['release_number']

class ReleaseInfoViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = ReleaseInfo.objects.all()
    serializer_class = ReleaseInfoSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ReleaseInfoFilter
    lookup_field = 'release_number'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        release_versions = queryset.values('date', 'release_number').distinct()
        versions_list = [{'Data': release['date'], 'Number': release['release_number']} for release in release_versions]

        return Response(versions_list)

    @action(detail=True, methods=['get'], url_path='version_info')
    def version_info(self, request, *args, **kwargs):
        release_number = self.kwargs['release_number']
        queryset = self.filter_queryset(self.get_queryset())
        releases = get_list_or_404(queryset, release_number=release_number)
        serializer = self.get_serializer(releases, many=True)

        for release in serializer.data:
            if not release['copy_contact']:
                release['copy_contact'] = 'Копии отсутствуют'

        return Response(serializer.data)


class ReportTicketViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, JWTAuthentication, BasicAuthentication]  # Используем все класса аутентификации
    permission_classes = [IsAuthenticated]
    serializer_class = ReportTicketSerializer
    
    def get_queryset(self):
        queryset = ReportTicket.objects.all()
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date is not None and end_date is not None:
            queryset = queryset.filter(creation_date__range=[start_date, end_date])
        return queryset

class UsersBoardMapsView(generics.ListAPIView):
    """
    Класс вывода информации о сотрудниках BoardMaps
    """
    queryset = UsersBoardMaps.objects.all()
    serializer_class = UsersBoardMapsSerializer
