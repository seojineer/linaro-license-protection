import uuid

from django.contrib import admin

from license_protected_downloads import models


class APIKeyStoreAdmin(admin.ModelAdmin):
    list_display = ('description', 'key', 'public', 'last_used')
    fields = ('description', 'key', 'public')
    read_only_fields = ('last_used',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(APIKeyStoreAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['key'].initial = str(uuid.uuid4())
        return form


class APITokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'key', 'expires', 'ip')
    read_only_fields = ('key',)


admin.site.register(models.APIKeyStore, APIKeyStoreAdmin)
admin.site.register(models.APIToken, APITokenAdmin)
admin.site.register(models.APILog)
admin.site.register(models.License)
