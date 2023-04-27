from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .serializers import ClientsListSerializer, ContactsSerializer, СonnectInfoCardSerializer
from main.models import ClientsList, ContactsCard, СonnectInfoCard, ClientsCard
from rest_framework import status
from rest_framework import filters
from rest_framework import generics


class ClientIdFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        client_id = request.query_params.get('client_id', None)
        if client_id is not None:
            queryset = queryset.filter(client_id__client_info__id=client_id)
        return queryset


class ClientsViewSet(viewsets.ModelViewSet):
    """
    ClientsViewSet предоставляет CRUD операции для модели ClientsList.
    """
    queryset = ClientsList.objects.all()  # Получение всех объектов ClientsList
    serializer_class = ClientsListSerializer  # Указание сериализатора для ClientsList
    permission_classes = [permissions.IsAuthenticated]  # Установка прав доступа для данного класса

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContactsViewSet(viewsets.ModelViewSet):
    """
    ContactsViewSet предоставляет CRUD операции для модели ContactsCard.
    """
    serializer_class = ContactsSerializer  # Указание сериализатора для ContactsCard

    def get_queryset(self):
        """
        Возвращает queryset контактов для определенного клиента или всех контактов, если client_id не указан.
        """
        client_id = self.kwargs.get('client_id', None)  # Получение client_id из параметров запроса
        if client_id is not None:
            try:
                client = ClientsList.objects.get(id=client_id)  # Получение объекта клиента по client_id
                return ContactsCard.objects.filter(client_card__client_info=client)  # Фильтрация контактов по клиенту
            except ClientsList.DoesNotExist:  # Обработка исключения, если клиент с указанным client_id не найден
                return ContactsCard.objects.none()  # Возвращение пустого queryset
        else:
            return ContactsCard.objects.all()  # Возвращение всех контактов

    def list_all(self, request, *args, **kwargs):
        """
        Возвращает список всех контактов с учетом пагинации.
        """
        queryset = self.filter_queryset(self.get_queryset().filter(client_card__isnull=False))  # Фильтрация контактов с привязкой к клиентам

        page = self.paginate_queryset(queryset)  # Применение пагинации к queryset
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # Сериализация данных с пагинацией
            return self.get_paginated_response(serializer.data)  # Возвращение данных с пагинацией

        serializer = self.get_serializer(queryset, many=True)  # Сериализация всех данных
        return Response(serializer.data)  # Возвращение всех сериализованных данных


class ConnectInfoViewSet(viewsets.ModelViewSet):
    queryset = СonnectInfoCard.objects.all()
    serializer_class = СonnectInfoCardSerializer
    filter_backends = [ClientIdFilter]

    def get_permissions(self):
        # Устанавливаем разрешения для разных действий
        if self.action == 'create' and 'client_id' in self.kwargs:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Возвращаем соответствующий queryset в зависимости от наличия client_id
        client_id = self.kwargs.get('client_id', None)
        if client_id is not None:
            try:
                client = ClientsList.objects.get(id=client_id)
                return СonnectInfoCard.objects.filter(client_id__client_info=client)
            except ClientsList.DoesNotExist:
                return СonnectInfoCard.objects.none()
        else:
            return СonnectInfoCard.objects.all()

    def create(self, request, *args, **kwargs):
        # Получаем client_id из аргументов
        client_id = kwargs.get('client_id', None)

        # Если client_id предоставлен, продолжаем
        if client_id is not None:

            # Пытаемся найти клиента с указанным client_id
            try:
                client = ClientsCard.objects.get(client_info_id=client_id)

                # Создаем сериализатор с переданными данными
                serializer = self.get_serializer(data=request.data)

                # Если сериализатор валиден, сохраняем данные и возвращаем ответ
                if serializer.is_valid():
                    serializer.save(client_id=client)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Если клиент не найден, возвращаем ошибку 404
            except ClientsCard.DoesNotExist:
                return Response({"error": "Клиент не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Если client_id не предоставлен, возвращаем ошибку 400
        else:
            return Response({"error": "Клиент ID не предоставлен"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        # Получение ID записи из URL
        connect_info_id = kwargs.get('pk', None)

        if connect_info_id is not None:
            try:
                # Получение объекта СonnectInfoCard с указанным ID
                connect_info = СonnectInfoCard.objects.get(id=connect_info_id)

                # Сериализация объекта с новыми данными и разрешение частичного обновления
                serializer = self.get_serializer(connect_info, data=request.data, partial=True)

                if serializer.is_valid():
                    # Сохранение обновленного объекта
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except СonnectInfoCard.DoesNotExist:
                return Response({"error": "ConnectInfo not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "ConnectInfo ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            return Response({"error": "ConnectInfo not found"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        # Получение ID записи из URL
        connect_info_id = kwargs.get('pk', None)

        if connect_info_id is not None:
            try:
                # Получение объекта СonnectInfoCard с указанным ID
                connect_info = СonnectInfoCard.objects.get(id=connect_info_id)

                # Удаление объекта
                connect_info.delete()

                # Возврат ответа с кодом 204 (NO CONTENT), указывающим на успешное удаление
                return Response(status=status.HTTP_204_NO_CONTENT)
            except СonnectInfoCard.DoesNotExist:
                return Response({"error": "ConnectInfo not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "ConnectInfo ID not provided"}, status=status.HTTP_400_BAD_REQUEST)