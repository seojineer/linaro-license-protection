#!/usr/bin/env python

import license_protected_downloads.management.commands.setsuperuser \
   as setsuperuser
from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.test import TestCase


class SetsuperuserCommandTest(TestCase):

    def setUp(self):
        self.command = setsuperuser.Command()

    def test_find_and_update_user_non_existing(self):
        self.assertRaises(CommandError,
                          self.command.find_and_update_user,
                          ("non_existing_user"))

    def test_find_and_update_user(self):
        user = User(username="existing_user")
        user.save()
        self.command.find_and_update_user("existing_user")
        user = User.objects.get(username="existing_user")
        self.assertEquals(user.is_staff, True)
        self.assertEquals(user.is_superuser, True)
