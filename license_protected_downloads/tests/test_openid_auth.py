import os
import unittest
from django.test import Client, TestCase
from license_protected_downloads.openid_auth import OpenIDAuth


class MockRequest():

    def __init__(self, authenticated):
        self.user = MockRequestUser(authenticated)

        
class MockRequestUser():

    def __init__(self, authenticated):
        self.authenticated = authenticated

    def is_authenticated():
        return self.authenticated

class TestOpenIDAuth(TestCase):

    def setUp(self):
        

    def test_check_team_membership_no_teams(self):
        mock_request = MockRequest(False)
        openid_teams = []
        self.assertIsNone(OpenIDAuth.check_team_membership(mock_request, openid_teams))

    def test_check_team_membership_no_authentication(self):
        mock_request = MockRequest(False)
        openid_teams = "linaro"
        self.assertIsNone(OpenIDAuth.check_team_membership(mock_request, openid_teams))

