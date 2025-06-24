from .standard_recipients import StandardRecipientStrategy
from .hotfix_recipients import HotfixRecipientStrategy
from .module_recipients import ModuleRecipientStrategy
from .saas_recipients import SaaSRecipientStrategy
from .service_window_recipients import ServiceWindowRecipientStrategy

def get_recipient_strategy(mailing):
    if mailing.release_type == "hotfix":
        return HotfixRecipientStrategy(mailing)
    if mailing.module:
        return ModuleRecipientStrategy(mailing)
    if mailing.request_service_window:
        return ServiceWindowRecipientStrategy(mailing)
    if mailing.notify_saas:
        return SaaSRecipientStrategy(mailing)
    return StandardRecipientStrategy(mailing)
