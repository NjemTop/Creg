from drf_yasg import openapi

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