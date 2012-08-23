from django.conf import settings
from django.shortcuts import redirect, render_to_response
from django.contrib.auth.models import Group
import bzr_version


class OpenIDAuth:

    @classmethod
    def process_openid_auth(cls, request, openid_teams):

        if not openid_teams:
            return None

        for openid_team in openid_teams:
            Group.objects.get_or_create(name=openid_team)

        if not request.user.is_authenticated():
            # Force OpenID login
            return redirect(settings.LOGIN_URL + "?next=" + request.path)

        for group in request.user.groups.all():
            if group.name in openid_teams:
                return None

        # Construct a nice string of openid teams that will allow access to
        # the requested file
        if len(openid_teams) > 1:
            teams_string = "one of the " + openid_teams.pop(0) + " "
            if len(openid_teams) > 1:
                teams_string += ", ".join(openid_teams[0:-1])

            teams_string += " or " + openid_teams[-1] + " teams"
        else:
            teams_string = "the " + openid_teams[0] + " team"

        response = render_to_response(
            'openid_forbidden_template.html',
            {'login': settings.LOGIN_URL + "?next=" + request.path,
             'authenticated': request.user.is_authenticated(),
             'openid_teams': teams_string,
             'revno': bzr_version.get_my_bzr_revno(),
             })

        response.status_code = 403
        return response
