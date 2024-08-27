import requests
from django.db.models import Q
from .models import ClientsCard, ModuleCard
import logging

logger = logging.getLogger(__name__)

def update_module_info():
    url = "https://licensor.boardmaps.ru/api/v1/licenses"

    try:
        response = requests.get(url)
        response.raise_for_status()  # проверка на статус ответа, в случае ошибки будет выброшено исключение
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении данных с API: {e}")
        return

    data = response.json()

    for item in data:
        client_name_api = clean_client_name(item["Name"])
        client_card = ClientsCard.objects.filter(Q(client_info__client_name__iexact=client_name_api)).first()
        
        if client_card:
            module_card, created = ModuleCard.objects.get_or_create(client_card=client_card)
            
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
                logger.info(f"Создана запись модуля для клиента {client_name_api}")
            else:
                logger.info(f"Обновлена запись модуля для клиента {client_name_api}")
        else:
            logger.warning(f"Клиент {client_name_api} не найден в базе данных")


def clean_client_name(client_name):
    # Удаляем лишние символы и приводим к нижнему регистру
    cleaned_name = ''.join(e for e in client_name if e.isalnum() or e.isspace()).lower()
    return cleaned_name
