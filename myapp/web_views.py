from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import BMInfoOnClient, ClientsCard
from .forms import AddClientForm, ContactsCardForm

def index(request):
    clients = BMInfoOnClient.objects.all()
    return render(request, 'myapp/index.html', {'clients': clients})

def get_clients(request):
    clients = BMInfoOnClient.objects.all()
    return render(request, 'myapp/get_clients.html', {'clients': clients})

def get_client(request, client_id):
    client = get_object_or_404(BMInfoOnClient, id=client_id)
    return render(request, 'myapp/get_client.html', {'client': client})

def search_clients(request):
    query = request.GET.get('query')
    clients = BMInfoOnClient.objects.filter(client_name__icontains=query).values('client_name', 'id')
    return JsonResponse(list(clients), safe=False)

def add_client(request):
    if request.method == 'POST':
        form = AddClientForm(request.POST)
        if form.is_valid():
            new_client = form.save(commit=False)
            new_client.save()
            return redirect('get_client', client_id=new_client.id)
    else:
        form = AddClientForm()
    return render(request, 'myapp/add_client.html', {'form': form})

def add_contact(request, client_card_id):
    client_card = get_object_or_404(ClientsCard, pk=client_card_id)

    if request.method == 'POST':
        form = ContactsCardForm(request.POST)
        if form.is_valid():
            new_contact = form.save(commit=False)
            new_contact.client_card = client_card
            new_contact.save()
            return redirect('get_client', client_card.client_info.id) # или другой URL, куда вы хотите вернуться после добавления контакта
    else:
        form = ContactsCardForm()

    return render(request, 'myapp/add_contact.html', {'form': form, 'client_card': client_card})
