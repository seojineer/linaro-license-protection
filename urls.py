from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    # Use "linaro-openid" to allow peaceful coexistence of both
    # python-apache-openid and django-openid authentication on the
    # same server.  When we get rid of apache openid protection,
    # we can go back to using just "openid" here.
    url(r'^linaro-openid/', include('django_openid_auth.urls')),
    url(r'^logout/$', 'django.contrib.auth.views.logout'),

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

    # Catch-all. We always return a file (or try to) if it exists.
    # This handler does that.
    url(r'(?P<path>.*)', 'license_protected_downloads.views.file_server'),
)
