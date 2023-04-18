from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import BMInfoOnClient

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
