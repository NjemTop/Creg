import requests
from django.db.models import Q
from main.models import ClientsCard, ModuleCard
from django.db.utils import IntegrityError
from rapidfuzz import fuzz
import logging
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts', get_abs_log_path('scripts_info.log'), logging.INFO)


def update_module_info():
    url = "https://licensor.boardmaps.ru/api/v1/licenses"

    # Получение данных с API
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        scripts_error_logger.error(f"Ошибка при получении данных с API: {e}")
        return

    data = response.json()

    for item in data:
        client_name_api = clean_client_name(item["Name"])
        try:
            # Находим клиента с наиболее схожим именем
            client_card = None
            max_ratio = 0
            for client in ClientsCard.objects.all():
                ratio = fuzz.ratio(client_name_api, client.client_info.client_name.lower())
                if ratio > max_ratio:
                    max_ratio = ratio
                    client_card = client
        except IntegrityError as e:
            scripts_error_logger.error(f"Ошибка целостности данных: {e}")
            continue  # Переходим к следующему элементу

        if client_card and max_ratio > 70:  # Можно изменить порог схожести по необходимости
            try:
                module_card, created = ModuleCard.objects.get_or_create(client_card=client_card)
            except IntegrityError as e:
                scripts_error_logger.error(f"Ошибка целостности данных: {e}")
                continue  # Переходим к следующему элементу

            # Обновление или создание записи модуля
            module_card.translate = item["ModuleDocumentBroadcastingEnabled"]
            module_card.electronic_signature = item["ModuleElectronicSignatureEnabled"]
            module_card.action_items = item["ModuleActionItemsEnabled"]
            module_card.limesurvey = item["ModuleAdvancedAccessRightsManagementEnabled"]
            module_card.advanced_voting = item["ModuleAdvancedVotingEnabled"]
            module_card.advanced_work_with_documents = item["ModuleAdvancedWorkWithDocumentsEnabled"]
            module_card.advanced_access_rights_management = item["ModuleSurveysEnabled"]
            module_card.visual_improvements = item["ModuleVisualImprovementsEnabled"]
            module_card.third_party_product_integrations = item["ModuleThirdPartyProductIntegrationsEnabled"]
            module_card.microsoft_enterprise_product_integrations = item["ModuleMicrosoftEnterpriseProductIntegrationsEnabled"]
            module_card.microsoft_office_365_integration = item["ModuleMicrosoftOffice365IntegrationEnabled"]
            
            module_card.save()

            if created:
                scripts_info_logger.info(f"Создана запись модуля для клиента {client_name_api}")
            else:
                scripts_info_logger.info(f"Обновлена запись модуля для клиента {client_name_api}")
        else:
            scripts_error_logger.error(f"Клиент {client_name_api} не найден в базе данных")

def clean_client_name(client_name):
    # Удаляем лишние символы и приводим к нижнему регистру
    cleaned_name = ''.join(e for e in client_name if e.isalnum() or e.isspace()).lower()
    return cleaned_name
