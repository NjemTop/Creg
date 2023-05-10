from rest_framework import serializers
from django.db import transaction
from main.models import ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Integration, TechAccountCard, ConnectionInfo, ServiseCard
from rest_framework.exceptions import ValidationError

class ClientsCardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели ClientsCard. 
    Здесь определены поля, которые будут сериализованы для этой модели.
    """
    class Meta:
        model = ClientsCard
        fields = ('contacts', 'tech_notes', 'connect_info', 'rdp', 'tech_account', 'bm_servers')

class ContactsCardSerializer(serializers.ModelSerializer):
    client_id = serializers.ReadOnlyField(source='client_id.client_info.id')
    class Meta:
        model = ContactsCard
        fields = ('client_id', 'contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes')

class ConnectInfoCardSerializer(serializers.ModelSerializer):
    client_id = serializers.ReadOnlyField(source='client_id.client_info.id')
    class Meta:
        model = ConnectInfoCard
        fields = ('id', 'client_id', 'contact_info_name', 'contact_info_account', 'contact_info_password')

class BMServersCardSerializer(serializers.ModelSerializer):
    client_id = serializers.ReadOnlyField(source='client_id.client_info.id')
    class Meta:
        model = BMServersCard
        fields = ('id', 'client_id', 'bm_servers_circuit', 'bm_servers_servers_name', 'bm_servers_servers_adress', 'bm_servers_operation_system', 'bm_servers_url', 'bm_servers_role')

class IntegrationCardSerializer(serializers.ModelSerializer):
    client_id = serializers.ReadOnlyField(source='client_id.client_info.id')
    class Meta:
        model = Integration
        fields = ('id', 'client_id', 'integration')

class TechAccountCardSerializer(serializers.ModelSerializer):
    client_id = serializers.ReadOnlyField(source='client_id.client_info.id')
    class Meta:
        model = TechAccountCard
        fields = ('id', 'client_id', 'contact_info_disc', 'contact_info_account', 'contact_info_password')


class ClientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для клиентов с вложенными сериализаторами для связанных сущностей:
    ClientsCard, ContactsCard и ConnectInfoCard.
    """

    # Вложенные сериализаторы для связанных объектов
    clients_card = ClientsCardSerializer(read_only=True)
    contacts_card = ContactsCardSerializer(many=True, read_only=True, source='clients_card.contact_cards')
    connect_info_card = ConnectInfoCardSerializer(many=True, read_only=True, source='clients_card.connect_info_card')
    bm_servers = BMServersCardSerializer(many=True, read_only=True, source='clients_card.bm_servers_card')

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
        fields = ('id', 'contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes')

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


class ConnectInfoSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    """
    Сериализатор со всей информацией о контактах в таблицы
    """
    class Meta:
        model = ConnectInfoCard
        fields = ('id', 'contact_info_name', 'contact_info_account', 'contact_info_password')

    def get_id(self, obj):
        if self.context.get('request', None) and self.context['request'].method == 'POST':
            return None
        return obj.id

    def to_representation(self, instance):
        if isinstance(instance, ClientsList):
            connect_info_card = ConnectInfoSerializer(instance.clients_card.connect_info_card.all(), many=True).data
            return {
                'id': instance.id,
                'client_name': instance.client_name,
                'connect_info_card': connect_info_card
            }
        else:
            return super().to_representation(instance)


class BMServersSerializer(serializers.ModelSerializer):
    # Добавляем поле client_name для вывода имени клиента
    client_name = serializers.CharField(source='client_card.client_info.client_name', read_only=True)

    class Meta:
        model = BMServersCard
        fields = (
            'id',
            'client_name',
            'bm_servers_circuit',
            'bm_servers_servers_name',
            'bm_servers_servers_adress',
            'bm_servers_operation_system',
            'bm_servers_url',
            'bm_servers_role',
        )

    def create(self, validated_data):
        # Получаем client_id из контекста запроса
        client_id = self.context['request'].parser_context['kwargs']['client_id']
        # Используя client_id, получаем объект ClientsCard, соответствующий этому клиенту
        client_card = ClientsCard.objects.get(client_info_id=client_id)
        # Создаем новый объект BMServersCard, передавая остальные данные из validated_data
        bm_server = BMServersCard(**validated_data)
        # Устанавливаем client_card для нового объекта BMServersCard
        bm_server.client_card = client_card
        # Сохраняем новый объект BMServersCard в базе данных
        bm_server.save()
        # Возвращаем новый объект BMServersCard
        return bm_server

    def to_representation(self, instance):
        if isinstance(instance, ClientsList):
            # Записываем в аргумент всю информацию о серверах BoardMaps
            bm_servers = BMServersSerializer(instance.clients_card.bm_servers_card.all(), many=True).data
            return {
                # Создаём филд, в который записываем информацию о клиенте и вкладываем внутрь массив информации о серверах BoardMaps
                'id': instance.id,
                'client_name': instance.client_name,
                'bm_servers': bm_servers
            }
        else:
            return super().to_representation(instance)


class IntegrationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = Integration
        fields = (
            'id', 'elasticsearch', 'ad', 'adfs', 'oauth_2', 'module_translate', 'ms_oos', 'exchange', 'office_365',
            'sfb', 'zoom', 'teams', 'smtp', 'cryptopro_dss', 'cryptopro_csp', 'smpp', 'limesurvey'
        )

    def get_id(self, obj):
        if self.context.get('request', None) and self.context['request'].method == 'POST':
            return None
        return obj.id

    def to_representation(self, instance):
        if isinstance(instance, ClientsList):
            integration = IntegrationSerializer(instance.clients_card.integration.all(), many=True).data
            return {
                'id': instance.id,
                'client_name': instance.client_name,
                'integration': integration
            }
        else:
            return super().to_representation(instance)


class TechAccountSerializer(serializers.ModelSerializer):
    """
    Сериализатор с информацией о технических УЗ для клиентов.
    """
    # Добавляем поле id, которое будет сериализовано с помощью метода get_id
    id = serializers.SerializerMethodField()

    class Meta:
        model = TechAccountCard
        fields = ('id', 'contact_info_disc', 'contact_info_account', 'contact_info_password')

    # Метод для определения значения поля id в сериализаторе
    def get_id(self, obj):
        # Если это POST-запрос, не возвращаем поле id
        if self.context.get('request', None) and self.context['request'].method == 'POST':
            return None
        # В противном случае возвращаем значение поля id
        return obj.id

    # Метод для представления данных в сериализаторе
    def to_representation(self, instance):
        # Если экземпляр относится к модели ClientsList
        if isinstance(instance, ClientsList):
            # Создаем сериализатор для связанных технических учетных записей с опцией many=True
            tech_account_card = TechAccountSerializer(instance.clients_card.tech_account_card, many=True).data
            # Возвращаем представление данных, включающее id, client_name и список технических учетных записей
            return {
                'id': instance.id,
                'client_name': instance.client_name,
                'tech_account_card': tech_account_card
            }
        # Если экземпляр относится к другой модели, используем стандартное представление
        else:
            return super().to_representation(instance)


class ConnectionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionInfo
        fields = ['id', 'file_path', 'text']


class ServiseSerializer(serializers.ModelSerializer):
    """
    Сериализатор с информацией о технических УЗ для клиентов.
    """
    # Добавляем поле id, которое будет сериализовано с помощью метода get_id
    id = serializers.SerializerMethodField()

    class Meta:
        model = ServiseCard
        fields = ('id', 'service_pack', 'manager', 'loyal')

    # Метод для определения значения поля id в сериализаторе
    def get_id(self, obj):
        # Если это POST-запрос, не возвращаем поле id
        if self.context.get('request', None) and self.context['request'].method == 'POST':
            return None
        # В противном случае возвращаем значение поля id
        return obj.id

    # Метод для представления данных в сериализаторе
    def to_representation(self, instance):
        # Если экземпляр относится к модели ClientsList
        if isinstance(instance, ClientsList):
            # Создаем сериализатор для связанных технических учетных записей с опцией many=True
            servise_card = ServiseSerializer(instance.clients_card.servise_card, many=True).data
            # Возвращаем представление данных, включающее id, client_name и список технических учетных записей
            return {
                'id': instance.id,
                'client_name': instance.client_name,
                'servise_card': servise_card
            }
        # Если экземпляр относится к другой модели, используем стандартное представление
        else:
            return super().to_representation(instance)


























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
