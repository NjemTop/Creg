from django.http import JsonResponse
from django.db.models import Q
from apps.clients.models import Client

def search_clients(request):
    """
    Эндпоинт для jQuery UI Autocomplete.
    Ищет клиентов по client_name (icontains),
    возвращает JSON-массив объектов {id, name}.
    """
    query = request.GET.get("q", "").strip()

    # Поиск начинается, если введено 2+ символа
    if len(query) > 1:
        clients = Client.objects.filter(
            Q(client_name__icontains=query)
        ).order_by("client_name")[:10] # Ограничиваем 10 результатами

        data = {
            "results": [
                {
                    "id": c.id,
                    "name": c.client_name
                }
                for c in clients
            ]
        }
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"results": []}, safe=False)
