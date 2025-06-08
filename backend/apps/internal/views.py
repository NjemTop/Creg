from django.shortcuts import render

def ws_test_page(request):
    return render(request, "testing/ws_test.html")
