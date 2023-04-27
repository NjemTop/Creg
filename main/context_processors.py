from django.conf import settings


def favicon(request):
    return {
        'FAVICON_URL': settings.MEDIA_URL + 'favicons/favicon.png',
    }

