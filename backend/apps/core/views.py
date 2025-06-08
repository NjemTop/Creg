from django.shortcuts import render

def index(request):
    context = {
        # Добавляем переменную в контекст, которая указывает на то, что это главная страница
        'hide_footer': True,
    }
    return render(request, 'core/index.html', context)

def custom_400(request, exception):
    return render(request, "errors/400.html", status=400)

def custom_404(request, exception):
    return render(request, "errors/404.html", status=404)

def custom_500(request):
    return render(request, "errors/500.html", status=500)

def contacts(request):
    return render(request, 'core/contacts.html')

def about(request):
    return render(request, 'core/about.html')

def faq(request):
    return render(request, 'core/faq.html')
