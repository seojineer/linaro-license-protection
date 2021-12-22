from django.conf import settings
from django.views.generic import RedirectView

from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.views.static import serve
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views

from license_protected_downloads.views import (
    show_license
    as show_license_views,
    redirect_to_root
    as redirect_to_root_views,
    accept_license
    as accept_license_views,
    get_textile_files
    as get_textile_files_views,
    reports
    as reports_views,
    reports_month_downloads
    as reports_month_downloads_views,
    reports_month_file_downloads
    as reports_month_file_downloads_views,
    reports_month_country
    as reports_month_country_views,
    reports_month_region
    as reports_month_region_views,
    reports_month_country_details
    as reports_month_country_details_views,
    reports_month_region_details
    as reports_month_region_details_views,
    file_server
    as file_server_views,
    error_view
)

# V1 and V2 not used
# Lets import anyway and delete this at a later date
from license_protected_downloads.api.v1 import (
    list_files_api
    as list_files_api_views,
    get_license_api
    as get_license_api_views
)

from license_protected_downloads.api.v2 import (
    token
    as token_v2_views,
    publish
    as publish_v2_views
    )
from license_protected_downloads.api.v2 import (
    link_latest as
    link_v2_latest_views
)

from license_protected_downloads.api.v3 import token as token_views
from license_protected_downloads.api.v3 import publish as publish_views
from license_protected_downloads.api.v3 import link_latest as link_latest_views



# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^login/$',
        auth_views.login,
        {'template_name': 'login.html'},
        name='login'),

    url(r'^logout/?$',
        auth_views.logout,
        name='logout'),

    # Handle JS libs and CSS.
    url(r'^js/(?P<path>.*)$', serve,
          {'document_root': settings.JS_PATH}),
    url(r'^css/(?P<path>.*)$', serve,
         {'document_root': settings.CSS_PATH}),

    # The license page...
    url(r'^license$',
        show_license_views,
        name='show_license'),

    # Exceptions redirected to root...
    url(r'^license',
        redirect_to_root_views,
        name='redirect_to_root'),

    # Accept the license
    url(r'^accept-license',
        accept_license_views,
        name='accept_license'),

    # Recursively get files for rendering (async calls accepted only).
    url(r'^get-textile-files',
        get_textile_files_views,
        name='get_textile_files'),

    # V1 and V2 API's not used
    url(r'^api/ls/(?P<path>.*)$',
        list_files_api_views),
    url(r'^api/license/(?P<path>.*)$',
        get_license_api_views),
    url(r'^api/v2/token/(?P<token>.*)$',
        token_v2_views),
    url(r'^api/v2/publish/(?P<path>.*)$',
        publish_v2_views),
    url(r'^api/v2/link_latest/(?P<path>.*)$',
        link_v2_latest_views),

    url(r'^api/v3/token/(?P<token>.*)$',
        token_views),
    url(r'^api/v3/publish/(?P<path>.*)$',
        publish_views),
    url(r'^api/v3/link_latest/(?P<path>.*)$',
        link_latest_views),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.TRACK_DOWNLOAD_STATS:
    urlpatterns += [
        url(r'^reports/$',
            reports_views),

        url(r'^reports/(?P<year_month>\d{4}\.\d{2})/downloads/$',
            reports_month_downloads_views),
        url(r'^reports/(?P<year_month>\d{4}\.\d{2})/downloads(?P<name>/.*)',
            reports_month_file_downloads_views),
        url(r'^reports/(?P<year_month>\d{4}\.\d{2})/country/$',
            reports_month_country_views),
        url(r'^reports/(?P<year_month>\d{4}\.\d{2})/region/$',
            reports_month_region_views),
        url(r'^reports/(?P<year_month>\d{4}\.\d{2})/country/(?P<country>.*)/',
            reports_month_country_details_views),
        url(r'^reports/(?P<year_month>\d{4}\.\d{2})/region/(?P<region>.*)/',
            reports_month_region_details_views),
    ]

urlpatterns += [
    # Catch-all. We always return a file (or try to) if it exists.
    # This handler does that.
    url(r'(?P<path>.*)', file_server_views),
]

handler500 = error_view
