import logging

from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.models import Group


log = logging.getLogger("llp.group_auth.openid")


def process_group_auth(request, openid_teams):
        """Returns True if access granted, False if denied and Response
        object if not enough authentication information available and
        user should authenticate first (by following that Response).
        """

        if not openid_teams:
            return True

        for openid_team in openid_teams:
            Group.objects.get_or_create(name=openid_team)

        if not request.user.is_authenticated():
            # Force OpenID login
            return redirect(settings.LOGIN_URL + "?next=" + request.path)

        log.warn("Authenticating using Launchpad OpenID Teams: %s",
                 request.user.username)
        for group in request.user.groups.all():
            if group.name in openid_teams:
                log.warn("Group auth access granted via Launchpad OpenID Teams")
                return True

        return False
