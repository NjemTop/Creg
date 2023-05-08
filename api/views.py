# views.py

from rest_framework import generics, mixins, viewsets, status
from rest_framework.response import Response
from main.models import ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Integration
from .mixins import CustomResponseMixin, CustomCreateModelMixin, CustomQuerySetFilterMixin
from .serializers import (
    ClientSerializer,
    ContactsSerializer,
    ClientContactsSerializer,
    ConnectInfoSerializer,
    ConnectInfoCardSerializer,
    ClientConnectInfoSerializer,
    BMServersSerializer,
    ClientBMServersSerializer,
    IntegrationSerializer,
    ClientIntegrationSerializer,
    IntegrationCreateSerializer,
)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = ClientsList.objects.all()
    serializer_class = ClientSerializer

class ContactsViewSet(viewsets.ModelViewSet):
    queryset = ClientsList.objects.all()
    serializer_class = ClientContactsSerializer

class ConnectInfoViewSet(viewsets.ModelViewSet):
    queryset = ClientsList.objects.all()
    serializer_class = ClientConnectInfoSerializer

class BMServersCardViewSet(viewsets.ModelViewSet):
    queryset = ClientsList.objects.all()
    serializer_class = ClientBMServersSerializer


class ContactsByClientIdView(mixins.CreateModelMixin, generics.ListAPIView):
    serializer_class = ClientContactsSerializer

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return ClientsList.objects.filter(id=client_id)

    def post(self, request, *args, **kwargs):
        request.data["client_card"] = self.kwargs['client_id']
        return self.create(request, *args, **kwargs)

class ContactDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
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


class ConnectInfoByClientIdView(mixins.CreateModelMixin, generics.ListAPIView):
    serializer_class = ClientConnectInfoSerializer

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return ClientsList.objects.filter(id=client_id)

    def post(self, request, *args, **kwargs):
        request.data["client_id"] = self.kwargs['client_id']
        return self.create(request, *args, **kwargs)

class ConnectInfoDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """
    Класс представления для обновления и удаления объектов ConnectInfoCard.

    Наследует CustomResponseMixin для настройки пользовательских ответов,
    а также UpdateModelMixin и DestroyModelMixin для выполнения операций обновления и удаления.
    """

    def __init__(self, *args, **kwargs):
        super().__init__('contact_info_name', 'client_id', *args, **kwargs)

    queryset = ConnectInfoCard.objects.select_related('client_id__client_info')
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
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IntegrationCreateSerializer
        else:
            return ClientIntegrationSerializer

    queryset = ClientsList.objects.all()

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)


class IntegrationDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

    def __init__(self, *args, **kwargs):
        super().__init__('client_card', 'client_card', *args, **kwargs)

    queryset = Integration.objects.select_related('client_card__client_info')
    serializer_class = IntegrationSerializer

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
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
        