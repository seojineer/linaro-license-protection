from django.conf import settings
from django.views.generic import RedirectView

try:
    from django.conf.urls.defaults import patterns, include, url
except:
    # django >= 1.6
    from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),

    # Use "linaro-openid" to allow peaceful coexistence of both
    # python-apache-openid and django-openid authentication on the
    # same server.  When we get rid of apache openid protection,
    # we can go back to using just "openid" here.
    url(r'^linaro-openid/', include('django_openid_auth.urls')),
    url(r'^login/?$', RedirectView.as_view(url='/linaro-openid/login/')),
    url(r'^logout/?$', 'django.contrib.auth.views.logout'),

    # Handle JS libs and CSS.
    url(r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.JS_PATH}),
    url(r'^css/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.CSS_PATH}),

    # The license page...
    url(r'^license$',
        'license_protected_downloads.views.show_license',
        name='show_license'),

    # Exceptions redirected to root...
    url(r'^license',
        'license_protected_downloads.views.redirect_to_root',
        name='redirect_to_root'),

    # Accept the license
    url(r'^accept-license',
        'license_protected_downloads.views.accept_license',
        name='accept_license'),

    # Recursively get files for rendering (async calls accepted only).
    url(r'^get-textile-files',
        'license_protected_downloads.views.get_textile_files',
        name='get_textile_files'),

    url(r'^api/ls/(?P<path>.*)$',
        'license_protected_downloads.api.v1.list_files_api'),

    url(r'^api/license/(?P<path>.*)$',
        'license_protected_downloads.api.v1.get_license_api'),

    url(r'^api/v2/token/(?P<token>.*)$',
        'license_protected_downloads.api.v2.token'),

    url(r'^api/v2/publish/(?P<path>.*)$',
        'license_protected_downloads.api.v2.publish'),

    url(r'^api/v2/link_latest/(?P<path>.*)$',
        'license_protected_downloads.api.v2.link_latest'),

    url(r'^api/v3/token/(?P<token>.*)$',
        'license_protected_downloads.api.v3.token'),
    url(r'^api/v3/publish/(?P<path>.*)$',
        'license_protected_downloads.api.v3.publish'),
    url(r'^api/v3/link_latest/(?P<path>.*)$',
        'license_protected_downloads.api.v3.link_latest'),

    url(r'^reports/$',
        'license_protected_downloads.views.reports'),

    url(r'^reports/(?P<year_month>\d{4}\.\d{2})/downloads/',
        'license_protected_downloads.views.reports_month_downloads'),
    url(r'^reports/(?P<year_month>\d{4}\.\d{2})/country/$',
        'license_protected_downloads.views.reports_month_country'),
    url(r'^reports/(?P<year_month>\d{4}\.\d{2})/region/$',
        'license_protected_downloads.views.reports_month_region'),

    # Catch-all. We always return a file (or try to) if it exists.
    # This handler does that.
    url(r'(?P<path>.*)', 'license_protected_downloads.views.file_server'),
)

handler500 = 'license_protected_downloads.views.error_view'
