from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    args = '<username username ...>'
    help = 'Sets specified user as superuser of the ' + \
      'license_protected_downloads admin app'

    def handle(self, *args, **options):
        for username in args:
            self.find_and_update_user(username)
            self.stdout.write('Successfully updated user "%s" \n' % username)

    def find_and_update_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError('User "%s" does not exist' % username)

        user.is_staff = True
        user.is_superuser = True
        user.save()
