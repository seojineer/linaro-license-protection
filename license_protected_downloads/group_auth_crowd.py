import logging

from django.conf import settings
from django.shortcuts import redirect

import requests


log = logging.getLogger(__file__)


def upgrade_requests():
    """Ubuntu 12.04 comes with pretty old requests version. Add convenience
    methods of newer versions straight to it, to avoid client-side
    workarounds."""
    if "json" not in dir(requests.models.Response):
        def patchy_json(self):
            import json
            return json.loads(self.content)
        requests.models.Response.json = patchy_json

# We monkey-patch requests module on first load
upgrade_requests()


class GroupAuthError(Exception):
    pass


def process_group_auth(request, required_groups):
    if not required_groups:
        return True
    if not request.user.is_authenticated():
        # Force OpenID login
        return redirect(settings.LOGIN_URL + "?next=" + request.path)

    log.warn("Authenticating using Crowd API: %s",
             request.user.username)

    auth = (settings.ATLASSIAN_CROWD_API_USERNAME,
            settings.ATLASSIAN_CROWD_API_PASSWORD)
    params = {"username": request.user.username}
    r = requests.get(settings.ATLASSIAN_CROWD_API_URL
                     + "/user/group/nested.json", params=params, auth=auth)
    if r.status_code != 200:
        raise GroupAuthError(r.status_code)
    data = r.json()
    user_groups = set([x["name"] for x in data["groups"]])

    # If groups don't intersect, access denied
    return not user_groups.isdisjoint(required_groups)
