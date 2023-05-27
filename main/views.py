from django.shortcuts import render, redirect
from .models import ClientsList, ClientsCard, ContactsCard, ReleaseInfo
from .forms import ClientListForm, ContactFormSet, ServiseCardForm
from django.db import transaction


def index(request):
    return render(request, 'main/index.html')


def clients(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/clients.html', {'title': 'Список клиентов', 'clients': clients})


@transaction.atomic
def create_client(request):
    error = ''
    form_client = None

    if request.method == 'POST':
        form_client = ClientListForm(request.POST)
        contact_formset = ContactFormSet(request.POST, prefix='contacts')
        servise_form = ServiseCardForm(request.POST)
        if form_client.is_valid() and contact_formset.is_valid() and servise_form.is_valid():
            client_list = form_client.save()
            client_card = ClientsCard.objects.create(client_info=client_list)
            
            for form in contact_formset:
                contact = form.save(commit=False)
                contact.client_card = client_card
                contact.save()
            
            servise_card = servise_form.save(commit=False)
            servise_card.client_card = client_card
            servise_card.save()
            
            return redirect('clients')
        else:
            error = 'Ошибка при заполнении формы данных'
            raise ValueError('Ошибка при сохранении данных о контактах')
    else:
        form_client = ClientListForm()
        contact_formset = ContactFormSet(prefix='contacts')
        servise_form = ServiseCardForm()

    context = {
        'form_client': form_client,
        'contact_formset': contact_formset,
        'servise_form': servise_form,
        'error': error
    }
    return render(request, 'main/create_client.html', context)


def upload_file(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/upload_file.html', {'clients': clients})


def release_info(request):
    release_infos = ReleaseInfo.objects.order_by('-date')
    return render(request, 'main/release_info.html', {'release_infos': release_infos})
