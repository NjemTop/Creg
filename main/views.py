from django.shortcuts import render, redirect
from .models import ClientsList, ReleaseInfo
from .forms import ClientListForm

def index(request):
    return render(request, 'main/index.html')


def clients(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/clients.html', {'title': 'Список клиентов', 'clients': clients})


def create_client(request):
    error = ''
    if request.method == 'POST':
        form = ClientListForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clients')
        else:
            error = 'Ошибка при заполнении формы данных'

    form = ClientListForm()
    context = {
        'form': form,
        'error': error
    }
    return render(request, 'main/create_client.html', context)

def upload_file(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/upload_file.html', {'clients': clients})

def release_info(request):
    release_infos = ReleaseInfo.objects.order_by('-date')
    return render(request, 'main/release_info.html', {'release_infos': release_infos})