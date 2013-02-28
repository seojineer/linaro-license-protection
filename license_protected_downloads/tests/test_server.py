__author__ = 'danilo'

from django.test import Client, TestCase
import urllib2

from license_protected_downloads.tests.helpers import TestHttpServer


THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TESTSERVER_ROOT = os.path.join(THIS_DIRECTORY, "testserver_root")


class HttpForwardingViewTest(TestCase):
    def test_http(self):
        pages = {"/": "pera", "/style.css": "some CSS"}
        with TestHttpServer(pages) as http_server:
            print "Opening %s..." % http_server.base_url
            data = urllib2.urlopen(http_server.base_url + '/style.css').read()
            self.assertEqual('some CSS', data)

