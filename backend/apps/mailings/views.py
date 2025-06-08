from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from collections import defaultdict
from .models import Mailing, MailingLog, MailingRecipient, MailingTestRecipient, Component, MailingStatus, MailingMode
from apps.clients.models import Client
from .constants import TEST_RECIPIENT_LABEL
from .tasks import send_mailing_task, send_ws_event, log_event
from .forms import MailingForm


def mailing_list(request):
    """Выводит список рассылок"""
    mailings = Mailing.objects.all().order_by('-created_at')
    return render(request, 'mailings/mailing_list.html', {'mailings': mailings})


def create_mailing(request):
    """Создаёт рассылку, но не запускает её сразу"""
    if request.method == 'POST':
        form = MailingForm(request.POST)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.created_by = request.user
            mailing.status = MailingStatus.DRAFT
            mailing.save()

            components = []
            if mailing.server_version:
                components.append(Component.objects.get(code="server"))
            if mailing.ipad_version:
                components.append(Component.objects.get(code="ipad"))
            if mailing.android_version:
                components.append(Component.objects.get(code="android"))

            if not components:
                messages.error(request, "Ошибка! Вы должны указать хотя бы одну версию для рассылки.")
                mailing.delete()
                return render(request, 'mailings/create_mailing.html', {'form': form})

            mailing.components.set(components)

            if mailing.mode == 'test':
                MailingTestRecipient.objects.create(
                    mailing=mailing,
                    email=form.cleaned_data['test_email']
                )
            else:
                clients = Client.objects.filter(contact_status=True)
                if mailing.language:
                    clients = clients.filter(language=mailing.language)

                for client in clients:
                    contacts = client.contacts.filter(notification_update=True)
                    for contact in contacts:
                        MailingRecipient.objects.create(
                            mailing=mailing,
                            client=client,
                            email=contact.email
                        )

            messages.success(request, "Рассылка успешно создана!")
            return redirect('mailing:mailing_list')

    else:
        form = MailingForm()

    return render(request, 'mailings/create_mailing.html', {'form': form})


def start_mailing(request, mailing_id):
    """Запускает уже созданную рассылку"""
    mailing = get_object_or_404(Mailing, id=mailing_id)

    if mailing.status == MailingStatus.DRAFT:
        mailing.status = MailingStatus.PENDING
        mailing.save()
        send_mailing_task.delay(mailing.id)

        message_text = f"Рассылка #{mailing.id} успешно запущена!"
        return JsonResponse({"status": "started", "message": message_text})
    
    message_text = f"Рассылка #{mailing.id} уже запущена или завершена."
    return JsonResponse({"status": "already_started", "message": message_text})

@require_POST
@csrf_exempt
def stop_mailing(request, mailing_id):
    mailing = get_object_or_404(Mailing, id=mailing_id)

    if mailing.status == MailingStatus.IN_PROGRESS:
        mailing.status = MailingStatus.FAILED
        mailing.completed_at = timezone.now()
        mailing.error_message = "Рассылка остановлена вручную."
        mailing.save()

        send_ws_event(mailing.id, "status", mailing.get_status_display())
        log_event(mailing.id, "warning", "Рассылка была принудительно остановлена пользователем.")

        return JsonResponse({"status": "stopped", "message": "Рассылка остановлена вручную."})
    
    return JsonResponse({"status": "not_stoppable", "message": "Нельзя остановить завершённую или неактивную рассылку."})

@require_POST
@csrf_exempt
def repeat_mailing(request, mailing_id):
    mailing = get_object_or_404(Mailing, id=mailing_id)

    # Создаём копию
    new_mailing = Mailing.objects.create(
        mode=mailing.mode,
        release_type=mailing.release_type,
        status=MailingStatus.PENDING,
        language=mailing.language,
        server_version=mailing.server_version,
        ipad_version=mailing.ipad_version,
        android_version=mailing.android_version,
        service_window=mailing.service_window,
        saas_notification=mailing.saas_notification,
        saas_update_time=mailing.saas_update_time,
        created_by=request.user,
    )

    new_mailing.components.set(mailing.components.all())

    if mailing.mode == MailingMode.TEST:
        for tr in mailing.test_recipients.all():
            MailingTestRecipient.objects.create(mailing=new_mailing, email=tr.email)
    else:
        for r in mailing.recipients.all():
            MailingRecipient.objects.create(
                mailing=new_mailing,
                client=r.client,
                email=r.email
            )

    # Запускаем повторно
    new_mailing.status = MailingStatus.PENDING
    new_mailing.save()
    send_mailing_task.delay(new_mailing.id)

    return JsonResponse({
        "status": "repeated",
        "message": f"Создана и запущена новая рассылка #{new_mailing.id}",
        "redirect_url": f"/mailings/detail/{new_mailing.id}/"
    })


def edit_mailing(request, mailing_id):
    """Позволяет редактировать черновик рассылки перед отправкой"""
    mailing = get_object_or_404(Mailing, id=mailing_id)

    if mailing.status != MailingStatus.DRAFT:
        messages.error(request, "Нельзя редактировать рассылку, которая уже отправляется или отправлена.")
        return redirect('mailing:mailing_list')

    # Получаем test_email, если это тестовая рассылка
    test_email = ""
    if mailing.mode == MailingMode.TEST:
        test_recipient = MailingTestRecipient.objects.filter(mailing=mailing).first()
        if test_recipient:
            test_email = test_recipient.email

    if request.method == 'POST':
        form = MailingForm(request.POST, instance=mailing)
        if form.is_valid():
            mailing = form.save()

            # Обновляем или создаём test_email
            if mailing.mode == MailingMode.TEST:
                MailingTestRecipient.objects.update_or_create(
                    mailing=mailing,
                    defaults={"email": form.cleaned_data["test_email"]}
                )

            messages.success(request, "Рассылка обновлена!")
            return redirect('mailing:mailing_list')
    else:
        form = MailingForm(instance=mailing, initial={"test_email": test_email})

    return render(request, 'mailings/edit_mailing.html', {'form': form, 'mailing': mailing})


def mailing_detail(request, mailing_id):
    """Страница с логами рассылки"""
    mailing = get_object_or_404(Mailing, id=mailing_id)

    # Группируем контакты по клиенту
    grouped_recipients = defaultdict(list)

    if mailing.mode == MailingMode.TEST:
        # Тестовые отправки
        test_recipients = MailingTestRecipient.objects.filter(mailing=mailing)
        for recipient in test_recipients:
            # У тестовых отправок нет клиента, поэтому создаём специальную запись
            grouped_recipients[TEST_RECIPIENT_LABEL].append(recipient)
    else:
        # Продакшен отправки
        recipients = MailingRecipient.objects.filter(mailing=mailing).select_related("client")
        for recipient in recipients:
            grouped_recipients[recipient.client].append(recipient)

    # Загружаем логи из базы (по убыванию времени)
    logs = MailingLog.objects.filter(mailing=mailing).order_by("-timestamp")

    return render(request, 'mailings/mailing_detail.html', {
        "mailing": mailing,
        "grouped_recipients": dict(grouped_recipients),
        "logs": logs,
        "test_recipient_label": TEST_RECIPIENT_LABEL
    })
