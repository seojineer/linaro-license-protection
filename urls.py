from django.conf import settings
from django.conf.urls.defaults import patterns, include, url

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
    url(r'^logout/$', 'django.contrib.auth.views.logout'),

    # Handle JS libs and CSS.
    url(r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.JS_PATH}),
    url(r'^css/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.CSS_PATH}),

    url(r'^get-remote-static',
        'license_protected_downloads.views.get_remote_static',
        name='get_remote_static'),

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

    # Catch-all. We always return a file (or try to) if it exists.
    # This handler does that.
    url(r'(?P<path>.*)', 'license_protected_downloads.views.file_server'),
)
