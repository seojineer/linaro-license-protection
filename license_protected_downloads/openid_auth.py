import sys

from django.shortcuts import redirect

class OpenIDAuth:

    @classmethod
    def process_openid_authentication(cls, request, openid_teams):

        print "openid_teams:", openid_teams

        if not openid_teams:
            return None

        if not request.user.is_authenticated():
            # Force OpenID login
            return redirect(settings.LOGIN_URL + "?next=/" +  request.path)
        else:
            
        
        return None

