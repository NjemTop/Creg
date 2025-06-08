from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from apps.utils.passwords import generate_secure_password
from apps.clients.models import Client, Module, ClientModule
from apps.clients.forms import (
    ClientForm, TechnicalInfoForm, ServiceInfoForm, 
    ContactFormSet
)
import json
import logging


logger = logging.getLogger(__name__)


def client_list(request):
    clients = Client.objects.all()
    return render(request, 'clients/client_list.html', {'clients': clients})

def client_detail(request, client_id):
    client = get_object_or_404(
        Client.objects.prefetch_related("modules", "integrations", "contacts", "servers"),
        id=client_id
    )
    
    context = {
        "client": client,
        "manager": getattr(client.service_info, "manager", None),
        "technical_info": getattr(client.technical_info, "server_version", "Не указано"),
        "contacts": client.contacts.all(),
        "modules": client.modules.all(),
        "integrations": client.integrations.all(),
        "servers": client.servers.all(),
    }
    
    return render(request, "clients/client_detail.html", context)

def create_client(request):
    if request.method == "POST":
        client_form = ClientForm(request.POST)
        tech_info_form = TechnicalInfoForm(request.POST)
        service_info_form = ServiceInfoForm(request.POST)
        contact_formset = ContactFormSet(request.POST)
        selected_modules = request.POST.getlist("modules")

        contact_formset.instance = Client() 

        # Проверяем валидацию форм
        if not all([client_form.is_valid(), tech_info_form.is_valid(), service_info_form.is_valid(), contact_formset.is_valid()]):
            errors = {
                "client_form": client_form.errors,
                "tech_info_form": tech_info_form.errors,
                "service_info_form": service_info_form.errors,
                "contact_formset": contact_formset.errors,
            }
            logger.error(f"❌ Валидации формы:\n{json.dumps(errors, ensure_ascii=False, indent=4)}")

            # Обрабатываем ошибки клиентской формы
            for field, error_list in client_form.errors.items():
                for error in error_list:
                    messages.error(request, f"{error}")

            # Обрабатываем ошибки контактов
            for i, form in enumerate(contact_formset.forms):
                if form.errors:
                    for field, error_list in form.errors.items():
                        field_name_with_prefix = form.add_prefix(field)
                        field_value = form.data.get(field_name_with_prefix, "")
                        
                        for error in error_list:
                            if field == "email":
                                messages.error(request, f"Контакт #{i+1}: '{error}")
                            else:
                                messages.error(request, f"Ошибка в контакте #{i+1} ({form.fields[field].label}): {error}")

            return render(
                request,
                "clients/create_client.html",
                {
                    "client_form": client_form,
                    "tech_info_form": tech_info_form,
                    "service_info_form": service_info_form,
                    "contact_formset": contact_formset,
                },
                status=400
            )

        try:
            with transaction.atomic():
                client = client_form.save(commit=False)
                client.password = generate_secure_password(8)
                client.save()
                logger.info(f"✅ Клиент создан: ID={client.id}, Имя={client.client_name}, Учётная запись={client.account_name}")
                logger.debug(f"🔐 Сгенерированный пароль для клиента {client.client_name}: {client.password}")

                tech_info = tech_info_form.save(commit=False)
                tech_info.client = client
                tech_info.save()
                logger.info(f"✅ Техническая информация: Версия сервера: {tech_info.server_version}")

                service_info = service_info_form.save(commit=False)
                service_info.client = client
                service_info.save()
                manager = service_info.manager
                logger.info(f"✅ Менеджер: {manager.first_name} {manager.last_name} ({manager.email})")

                contact_formset.instance = client
                contacts = contact_formset.save()
                if contacts:
                    logger.info(f"✅ Контакты ({len(contacts)}) для {client.client_name}:")
                    for contact in contacts:
                        logger.info(f" - {contact.first_name} {contact.last_name}, Email: {contact.email}, Phone: {contact.phone_number}")
                else:
                    logger.info(f"ℹ️ Нет контактов для клиента {client.client_name}")

                if selected_modules:
                    module_names = []
                    for module_id in selected_modules:
                        module = Module.objects.get(id=module_id)
                        ClientModule.objects.create(client=client, module=module, is_active=True)
                        module_names.append(module.name)

                    logger.info(f"✅ Подключены модули ({len(module_names)}) для {client.client_name}: {module_names}")
                else:
                    logger.info(f"ℹ️ Нет активных модулей у клиента {client.client_name}")

                messages.success(request, f"Клиент '{client.client_name}' успешно создан!")
                return redirect("clients:client_detail", client_id=client.id)

        except Exception as error_message:
            logger.exception(f"❌ Критическая ошибка при создании клиента: {error_message}")
            return render(
                request,
                "errors/500.html",
                {
                    "message": "Произошла критическая ошибка при создании клиента.",
                    "error_details": str(error_message)
                },
                status=500
            )

    else:
        return render(request, "clients/create_client.html", {
                "client_form": ClientForm(),
                "tech_info_form": TechnicalInfoForm(),
                "service_info_form": ServiceInfoForm(),
                "contact_formset": ContactFormSet(),
                "modules": Module.objects.all(),
            })
