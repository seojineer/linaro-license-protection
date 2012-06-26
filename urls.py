from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # The license page...
    url(r'^license$', 'linaro_license_protection_2.license_protected_downloads.views.show_license', name='show_license'),

    # Exceptions redirected to root...
    url(r'^license', 'linaro_license_protection_2.license_protected_downloads.views.redirect_to_root', name='redirect_to_root'),

    # Accept the license
    url(r'^accept-license', 'linaro_license_protection_2.license_protected_downloads.views.accept_license', name='accept_license'),

    # Catch-all. We always return a file (or try to) if it exists.
    # This handler does that.
    url(r'(?P<path>.*)', 'linaro_license_protection_2.license_protected_downloads.views.file_server'),
)
