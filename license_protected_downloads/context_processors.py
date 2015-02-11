from django.conf import settings


def llp_common(request):
    return {
        'base_page': settings.BASE_PAGE,
        'revno': settings.VERSION,
    }
