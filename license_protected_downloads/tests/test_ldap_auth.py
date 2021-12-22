
from django.test import TestCase
from django.http import HttpResponse

from mock import Mock

from license_protected_downloads import group_auth_ldap as ldap_auth


FAKE_GROUPS = {
    "foo": ['alpha', 'beta'],
    "bar": ['gamma'],
    "empty": [],
}


class TestLDAPAuth(TestCase):

    def setUp(self):
        try:
            import linaro_ldap
        except KeyError:
            pass

        linaro_ldap.get_groups_and_users = self.mock_get_groups_and_users
        

    def mock_get_groups_and_users(self):
        return FAKE_GROUPS

    def make_mock_request(self):
        mock_request = Mock()
        mock_request.path = '/'
        mock_request.user = Mock()
        mock_request.user.username = Mock()
        mock_request.user.is_authenticated = Mock()
        mock_request.user.groups = Mock()
        mock_request.user.groups.all = Mock()
        return mock_request

    def test_check_team_membership_no_teams(self):
        mock_request = self.make_mock_request()
        ldap_teams = []
        self.assertTrue(
            ldap_auth.process_group_auth(mock_request, ldap_teams))

    def test_check_team_membership_no_authentication(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = False
        ldap_teams = ["foo"]
        response = ldap_auth.process_group_auth(mock_request, ldap_teams)
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(302, response.status_code)

    def test_check_team_membership_authed(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = True
        mock_request.user.username = 'alpha'
        ldap_teams = ["foo"]
        response = ldap_auth.process_group_auth(mock_request, ldap_teams)
        self.assertTrue(response)

    def test_check_no_team_membership_authed(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = True
        mock_request.user.username = 'gamma'
        ldap_teams = ["foo"]
        response = ldap_auth.process_group_auth(mock_request, ldap_teams)
        self.assertFalse(response)

    def test_check_no_team_membership_authed_multi_teams(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = True
        mock_request.user.username = 'delta'
        ldap_teams = ["foo", "bar", "baz"]
        response = ldap_auth.process_group_auth(mock_request, ldap_teams)
        self.assertFalse(response)
#
#    @patch("django.contrib.auth.models.Group.objects.get_or_create")
#    def test_auto_adding_groups(self, get_or_create_mock):
#        mock_request = self.make_mock_request()
#        mock_request.user.is_authenticated.return_value = True
#        mock_request.user.groups.all.return_value = [
#            self.make_mock_group("another-group")]
#
#        openid_teams = ["linaro", "linaro-infrastructure"]
#        openid_auth.process_group_auth(mock_request, openid_teams)
#
#        expected = [
#            ((), {'name': 'linaro'}), ((), {'name': 'linaro-infrastructure'})]
#        self.assertEquals(get_or_create_mock.call_args_list, expected)
