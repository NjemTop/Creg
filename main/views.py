from django.shortcuts import render, redirect
from .models import ClientsList, ClientsCard, ContactsCard, ReleaseInfo
from .forms import ClientListForm, ContactFormSet, ServiseCardForm, TechInformationCardForm
from django.db import transaction


def index(request):
    return render(request, 'main/index.html')


def clients(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/clients.html', {'title': 'Список клиентов', 'clients': clients})


@transaction.atomic
def create_client(request):
    error = ''  # Инициализация переменной для хранения ошибки
    form_client = None  # Инициализация переменной для хранения формы клиента

    if request.method == 'POST':
        form_client = ClientListForm(request.POST)  # Создание формы клиента на основе POST-данных
        contact_formset = ContactFormSet(request.POST, prefix='contacts')  # Создание формсета контактов на основе POST-данных с префиксом 'contacts'
        servise_form = ServiseCardForm(request.POST)  # Создание формы сервисной карты на основе POST-данных
        tech_info_form = TechInformationCardForm(request.POST) # Создание формы технической информации на основе POST-данных

        if form_client.is_valid() and contact_formset.is_valid() and servise_form.is_valid() and tech_info_form.is_valid():
            # Если все формы валидны, выполняется сохранение данных

            client_list = form_client.save()  # Сохранение данных клиента
            client_card = ClientsCard.objects.create(client_info=client_list)  # Создание записи о клиенте в модели ClientsCard

            for form in contact_formset:
                contact = form.save(commit=False)  # Создание объекта контакта без сохранения в базу данных
                contact.client_card = client_card  # Привязка контакта к клиентской карте
                contact.save()  # Сохранение контакта в базу данных

            # Создание объекта сервисной карты без сохранения в базу данных
            servise_card = servise_form.save(commit=False)
            servise_card.client_card = client_card  # Привязка сервисной карты к клиентской карте
            servise_card.save()  # Сохранение сервисной карты в базу данных

            # Создание объекта технической информации без сохранения в базу данных
            tech_info = tech_info_form.save(commit=False)
            tech_info.client_card = client_card
            tech_info.save()

            return redirect('clients')  # Перенаправление на страницу со списком клиентов
        else:
            error = 'Ошибка при заполнении формы данных'  # Установка сообщения об ошибке
            raise ValueError('Ошибка при сохранении данных о контактах')  # Генерация исключения ValueError при ошибке валидации форм

    else:
        form_client = ClientListForm()  # Создание пустой формы клиента
        contact_formset = ContactFormSet(prefix='contacts')  # Создание пустого формсета контактов с префиксом 'contacts'
        servise_form = ServiseCardForm()  # Создание пустой формы сервисной карты
        tech_info_form = TechInformationCardForm() # Создание пустой формы технической информации

    context = {
        'form_client': form_client,
        'contact_formset': contact_formset,
        'servise_form': servise_form,
        'tech_info_form': tech_info_form,
        'error': error,
        'contact_formset_total_form_count': contact_formset.total_form_count,  # Передача количества форм в формсете в контекст
        'contact_formset_max_num': contact_formset.max_num,  # Передача максимального количества форм в формсете в контекст
    }
    return render(request, 'main/create_client.html', context)  # Возвращение ответа с рендерингом шаблона 'create_client.html' и передачей контекста


def upload_file(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/upload_file.html', {'clients': clients})


def release_info(request):
    release_infos = ReleaseInfo.objects.order_by('-date')
    return render(request, 'main/release_info.html', {'release_infos': release_infos})
