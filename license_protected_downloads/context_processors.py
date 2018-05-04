from django.conf import settings


def llp_common(request):
    return {
        'site_name': settings.SITE_NAME,
        'base_page': settings.BASE_PAGE,
        'revno': settings.VERSION,
    }
