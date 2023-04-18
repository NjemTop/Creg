from django.conf import settings

def favicon(request):
    return {
        'FAVICON_URL': settings.MEDIA_URL + 'media/favicons/favicon.png',
    }
