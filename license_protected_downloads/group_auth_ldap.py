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

    user = request.user.username
    log.warn("Authenticating using LDAP API: %s", user)

    ldap_groups = linaro_ldap.get_groups_and_users()
    user_groups = [g for g in ldap_groups if user in ldap_groups[g]]

    log.info("User groups are: %s", user_groups)

    for user_group in user_groups:
        if user_group in required_groups:
            return True
    return False
