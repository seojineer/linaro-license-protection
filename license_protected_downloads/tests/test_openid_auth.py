import os
import unittest
from django.test import Client, TestCase
from django.http import HttpResponse



from license_protected_downloads.openid_auth import OpenIDAuth


class MockRequest():

    def __init__(self, authenticated, groups=[]):
        self.user = MockRequestUser(authenticated, groups)
        self.path = "/"


class MockRequestUser():

    def __init__(self, authenticated, groups):
        self.authenticated = authenticated
        mock_groups = []
        for group in groups:
            mock_group = MockRequestGroup(group)
            mock_groups.append(mock_group)
        self.groups = mock_groups

    def is_authenticated(self):
        return self.authenticated

class MockRequestGroup():

    def __init__(self, name):
        self.name = name


class TestOpenIDAuth(TestCase):

    def setUp(self):
        pass


    def test_check_team_membership_no_teams(self):
        mock_request = MockRequest(False)
        openid_teams = []
        self.assertIsNone(OpenIDAuth.process_openid_auth(mock_request, openid_teams))


    def test_check_team_membership_no_authentication(self):
        mock_request = MockRequest(False)
        openid_teams = ["linaro"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(302, response.status_code)


    def test_check_team_membership_authed(self):
        mock_request = MockRequest(True, ["linaro"])
        openid_teams = ["linaro"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)
        self.assertIsNone(response)


    def test_check_no_team_membership_authed(self):
        mock_request = MockRequest(True, ["another_group"])
        openid_teams = ["linaro"]
        response = OpenIDAuth.process_openid_auth(mock_request, openid_teams)
        self.assertIsNotNone(response)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(403, response.status_code)
