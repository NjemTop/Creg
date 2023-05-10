# views.py

from rest_framework import generics, mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from main.models import ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Integration, TechAccountCard, ConnectionInfo, ServiseCard
from .mixins import CustomResponseMixin, CustomCreateModelMixin, CustomQuerySetFilterMixin
from .response_helpers import file_upload_error_response, custom_update_response, custom_delete_response
from .serializers import (
    ClientSerializer,
    ContactsSerializer,
    ClientContactsSerializer,
    ConnectInfoSerializer,
    BMServersSerializer,
    IntegrationSerializer,
    TechAccountSerializer,
    ConnectionInfoSerializer,
    ServiseSerializer,
)
from django.shortcuts import get_object_or_404


class ClientViewSet(viewsets.ModelViewSet):
    queryset = ClientsList.objects.all()
    serializer_class = ClientSerializer

class ContactsViewSet(viewsets.ModelViewSet):
    queryset = ClientsList.objects.all()
    serializer_class = ClientContactsSerializer


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


class ConnectInfoByClientIdView(CustomCreateModelMixin, generics.ListAPIView):
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
    def get_serializer_class(self):
        return IntegrationSerializer

    queryset = ClientsList.objects.all()
    related_name = "clients_card"

    def get_client_card(self, client_id):
        return ClientsCard.objects.get(client_info_id=client_id)

class IntegrationDetailsView(CustomResponseMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

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
        