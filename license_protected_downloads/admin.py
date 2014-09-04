from django.contrib import admin

from license_protected_downloads import models


class APIKeyStoreAdmin(admin.ModelAdmin):
    list_display = ('description', 'key', 'public', 'last_used')
    fields = ('description', 'key', 'public')
    read_only_fields = ('last_used',)


admin.site.register(models.APIKeyStore, APIKeyStoreAdmin)
admin.site.register(models.APIToken)
admin.site.register(models.APILog)
admin.site.register(models.License)
