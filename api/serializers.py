from rest_framework import serializers
from main.models import ClientsList, ClientsCard, ContactsCard, СonnectInfoCard
from rest_framework.exceptions import ValidationError
from django.db import transaction

class ClientsCardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели ClientsCard. 
    Здесь определены поля, которые будут сериализованы для этой модели.
    """
    class Meta:
        model = ClientsCard
        fields = ('contacts', 'tech_notes', 'connect_info', 'rdp', 'tech_account', 'bm_servers')

class ContactsCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactsCard
        fields = ('contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes')

class СonnectInfoCardSerializer(serializers.ModelSerializer):
    client_id = serializers.ReadOnlyField(source='client_id.client_info.id')
    class Meta:
        model = СonnectInfoCard
        fields = ('id', 'client_id', 'contact_info_name', 'contact_info_account', 'contact_info_password')

class ClientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для клиентов с вложенными сериализаторами для связанных сущностей:
    ClientsCard, ContactsCard и СonnectInfoCard.
    """

    # Вложенные сериализаторы для связанных объектов
    clients_card = ClientsCardSerializer(read_only=True)
    contacts_card = ContactsCardSerializer(many=True, read_only=True, source='clients_card.contact_cards')
    connect_info_card = СonnectInfoCardSerializer(many=True, read_only=True, source='clients_card.connect_info_card')

    class Meta:
        model = ClientsList
        fields = '__all__'

    def create(self, validated_data):
        """
        Переопределенный метод для создания нового объекта клиента.
        Он также создает связанный объект ClientsCard.
        Использует транзакцию для обеспечения консистентности данных.
        """
        with transaction.atomic():
            clients_list = ClientsList.objects.create(**validated_data)
            clients_card = ClientsCard.objects.create(client_info=clients_list)
        return clients_list

    def update(self, instance, validated_data):
        """
        Переопределенный метод для обновления существующего объекта клиента.
        Он также обновляет связанный объект ClientsCard при наличии данных.
        Использует транзакцию для обеспечения консистентности данных.
        """
        with transaction.atomic():
            # Вызываем метод обновления родительского класса для обновления основной информации о клиенте
            instance = super().update(instance, validated_data)

            # Извлекаем данные о связанной карточке клиента (clients_card) из запроса
            clients_card_data = self.context['request'].data.get('clients_card', {})

            # Если данные по clients_card присутствуют, то выполняем их обновление
            if clients_card_data:
                # Получаем связанный объект clients_card с текущим объектом клиента
                clients_card = instance.clients_card

                # Создаем сериализатор с новыми данными для clients_card и указываем partial=True для частичного обновления
                clients_card_serializer = ClientsCardSerializer(clients_card, data=clients_card_data, partial=True)

                # Проверяем, являются ли данные сериализатора валидными, и в случае ошибок вызываем исключение
                if clients_card_serializer.is_valid(raise_exception=True):
                    # Сохраняем обновленный объект clients_card
                    clients_card_serializer.save()

        return instance

class ContactsSerializer(serializers.ModelSerializer):
    """
    Сериализатор со всей информацией о контактах в таблицы
    """
    class Meta:
        model = ContactsCard
        fields = '__all__'

class ClientContactsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода структурированной информации.
    Информация об айди клиента и название этого клиента,
    а также вложенный массив с контактами этого клиента
    """
    # Записываем в аргумент всю информацию о контактах
    contacts_card = ContactsSerializer(many=True, read_only=True, source='clients_card.contact_cards')

    class Meta:
        model = ClientsList
        # Создаём филд, в который записываем информацию о клиенте и вкладываем внутрь массив контактов
        fields = ('id', 'client_name', 'contacts_card')















# class ClientsListSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для модели ClientsList.
#     Здесь определены дополнительные сериализаторы ClientsCardSerializer, ContactsCardSerializer
#     и СonnectInfoCardSerializer для связанных полей. 
#     В методе create реализована логика создания клиента и связанных с ним объектов.
#     """
#     clients_card = ClientsCardSerializer(read_only=True)
#     contacts_card = ContactsCardSerializer(many=True, source='clients_card.contact_cards')
#     connect_info_card = СonnectInfoCardSerializer(many=True, source='clients_card.connect_info_card')

#     class Meta:
#         model = ClientsList
#         fields = '__all__'

#     @transaction.atomic
#     def create(self, validated_data):
#         # Проверяем, существует ли уже клиент с таким именем
#         client_name = validated_data.get('client_name')
#         if ClientsList.objects.filter(client_name=client_name).exists():
#             raise ValidationError(f"Клиент '{client_name}' уже есть в системе")

#         # Создаем список для хранения сообщений об ошибках
#         errors = []

#         # Извлекаем данные контактных карт из валидированных данных
#         clients_card_data = validated_data.pop('clients_card', {})
#         contacts_card_data = clients_card_data.get('contacts_card', [])
#         connect_info_card_data = clients_card_data.get('connect_info_card', [])

#         # Создаем экземпляр ClientsList с переданными данными
#         clients_list = ClientsList.objects.create(**validated_data)

#         # Создаем экземпляр ClientsCard и устанавливаем связь с созданным экземпляром ClientsList
#         clients_card = ClientsCard.objects.create(client_info=clients_list)

#         # Создаем экземпляры ContactsCard с данными из contacts_cards_data
#         for contact_card_data in contacts_card_data:
#             try:
#                 ContactsCard.objects.create(client_card=clients_card, **contact_card_data)
#             except Exception as error_message:
#                 # Если возникает ошибка при создании экземпляра ContactsCard, выводим информацию об ошибке
#                 errors.append(f"Ошибка создания карточки пользователя: {error_message}")

#         # Создаем экземпляры СonnectInfoCard с данными из connect_info_card_data
#         for connect_info_data in connect_info_card_data:
#             try:
#                 СonnectInfoCard.objects.create(client_id=clients_card, **connect_info_data)
#             except Exception as error_message:
#                 errors.append(f"Ошибка создания информации для подключения: {error_message}")

#         # Если список ошибок не пуст, вызываем исключение ValidationError
#         if errors:
#             raise serializers.ValidationError(errors)

#         # Возвращаем созданный экземпляр ClientsList
#         return clients_list
