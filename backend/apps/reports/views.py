from django.shortcuts import render


def report(request):
    return render(request, 'report/report.html')

def release_info(request):
    return render(request, 'report/release_info.html')
