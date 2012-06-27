import sys

from django.conf import settings
from django.shortcuts import redirect

from django.http import HttpResponseForbidden


class OpenIDAuth:

    @classmethod
    def process_openid_auth(cls, request, openid_teams):

        print "openid_teams:", openid_teams

        if not openid_teams:
            return None

        if not request.user.is_authenticated():
            # Force OpenID login
            return redirect(settings.LOGIN_URL + "?next=" +  request.path)

        for group in request.user.groups:
            if group.name in openid_teams:
                return None

        return HttpResponseForbidden("Not Authorized")
