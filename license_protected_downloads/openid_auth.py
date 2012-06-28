import sys

from django.conf import settings
from django.shortcuts import redirect

from django.http import HttpResponseForbidden
from django.contrib.auth.models import User, Group

class OpenIDAuth:

    @classmethod
    def process_openid_auth(cls, request, openid_teams):

        print "openid_teams:", openid_teams

        if not openid_teams:
            return None

        for openid_team in openid_teams:
            Group.objects.get_or_create(name=openid_team)

        if not request.user.is_authenticated():
            # Force OpenID login
            return redirect(settings.LOGIN_URL + "?next=" +  request.path)

        for group in request.user.groups.all():
            if group.name in openid_teams:
                return None

        return HttpResponseForbidden("Not Authorized")
