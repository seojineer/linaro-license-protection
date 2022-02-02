import logging

from django.conf import settings
from django.shortcuts import redirect
import linaro_ldap

from group_auth_common import GroupAuthError


log = logging.getLogger("llp.group_auth.ldap")


def process_group_auth(request, required_groups):
    if not required_groups:
        return True
    if not request.user.is_authenticated():
        return redirect(settings.LOGIN_URL + "?next=" + request.path)

    user = request.user.username.split('@').pop(0)
    log.warn("Authenticating using LDAP API: %s", user)

    ldap_groups = linaro_ldap.get_groups_and_users()

    for group in required_groups:
        if user in ldap_groups[group]:
            return True
    return False
