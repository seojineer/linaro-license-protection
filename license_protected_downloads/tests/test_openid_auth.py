import os
import unittest
from django.test import Client, TestCase
from django.http import HttpResponse
from mock import Mock, patch

from license_protected_downloads.openid_auth import OpenIDAuth


class TestOpenIDAuth(TestCase):

    def setUp(self):
        pass


    def make_mock_request(self):
        mock_request = Mock()
        mock_request.path = '/'
        mock_request.user = Mock()
        mock_request.user.is_authenticated = Mock()
        mock_request.user.groups = Mock()
        mock_request.user.groups.all = Mock()
        return mock_request


    def make_mock_group(self, name):
        mock_group = Mock()
        mock_group.name = name
        return mock_group


    def test_check_team_membership_no_teams(self):
        mock_request = self.make_mock_request()
        openid_teams = []
        self.assertIsNone(OpenIDAuth.process_openid_auth(mock_request, openid_teams))


    def test_check_team_membership_no_authentication(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = False
        openid_teams = ["linaro"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(302, response.status_code)


    def test_check_team_membership_authed(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = True
        mock_request.user.groups.all.return_value = [self.make_mock_group("linaro")]
        openid_teams = ["linaro"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)
        self.assertIsNone(response)


    def test_check_no_team_membership_authed(self):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = True
        mock_request.user.groups.all.return_value = [self.make_mock_group("another-group")]
        openid_teams = ["linaro"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(403, response.status_code)

    @patch("django.contrib.auth.models.Group.objects.get_or_create")
    def test_auto_adding_groups(self, get_or_create_mock):
        mock_request = self.make_mock_request()
        mock_request.user.is_authenticated.return_value = True
        mock_request.user.groups.all.return_value = [self.make_mock_group("another-group")]

        openid_teams = ["linaro", "linaro-infrastructure"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)

        expected = [((), {'name': 'linaro'}), ((), {'name': 'linaro-infrastructure'})]
        self.assertEquals(get_or_create_mock.call_args_list, expected)
