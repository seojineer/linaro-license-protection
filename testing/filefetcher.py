#!/usr/bin/env python

# Changes required to address EULA for the origen hwpacks

import argparse
import os
import pycurl
import re
import urlparse

class LicenseProtectedFileFetcher:
    """Fetch a file from the web that may be protected by a license redirect

    This is designed to run on snapshots.linaro.org. License HTML file are in
    the form:

    <vendor>.html has a link to <vendor>-accept.html

    If self.get is pointed at a file that has to go through one of these
    licenses, it should be able to automatically accept the license and
    download the file.

    Once a license has been accepted, it will be used for all following
    downloads.

    If self.close() is called before the object is deleted, cURL will store
    the license accept cookie to cookies.txt, so it can be used for later
    downloads.

    """
    def __init__(self):
        """Set up cURL"""
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.WRITEFUNCTION, self._write_body)
        self.curl.setopt(pycurl.HEADERFUNCTION, self._write_header)
        self.curl.setopt(pycurl.COOKIEFILE, "cookies.txt")
        self.curl.setopt(pycurl.COOKIEJAR, "cookies.txt")

    def _get(self, url):
        """Clear out header and body storage, fetch URL, filling them in."""
        self.curl.setopt(pycurl.URL, url)

        self.body = ""
        self.header = ""

        self.curl.perform()

    def get(self, url, ignore_license=False, accept_license=True):
        """Fetch the requested URL, ignoring license at all or
        accepting or declining licenses, returns file body.

        Fetches the file at url. If a redirect is encountered, it is
        expected to be to a license that has an accept or decline link.
        Follow that link, then download original file or nolicense notice.

        """
        self._get(url)

        if ignore_license:
            return self.body

        location = self._get_location()
        if location:
            # Off to the races - we have been redirected.
            # Expect to find a link to self.location with -accepted or
            # -declined inserted before the .html,
            # i.e. ste.html -> ste-accepted.html

            # Get the file from the URL (full path)
            file = urlparse.urlparse(location).path

            # Get the file without the rest of the path
            file = os.path.split(file)[-1]

            # Look for a link with accepted.html or declined.html
            # in the page name. Follow it.
            new_file = None
            for line in self.body.splitlines():
                if accept_license:
                    link_search = re.search("""href=.*?["'](.*?-accepted.html)""",
                                        line)
                else:
                    link_search = re.search("""href=.*?["'](.*?-declined.html)""",
                                        line)
                if link_search:
                    # Have found license decline URL!
                    new_file = link_search.group(1)

            if new_file:
                # accept or decline the license...
                next_url = re.sub(file, new_file, location)
                self._get(next_url)

                # The above get *should* take us to the file requested via
                # a redirect. If we manually need to follow that redirect,
                # do that now.

                if accept_license and self._get_location():
                    # If we haven't been redirected to our original file,
                    # we should be able to just download it now.
                    self._get(url)

        return self.body

    def _search_header(self, field):
        """Search header for the supplied field, return field / None"""
        for line in self.header.splitlines():
            search = re.search(field + ":\s+(.*?)$", line)
            if search:
                return search.group(1)
        return None

    def _get_location(self):
        """Return content of Location field in header / None"""
        return self._search_header("Location")

    def _write_body(self, buf):
        """Used by curl as a sink for body content"""
        self.body += buf

    def _write_header(self, buf):
        """Used by curl as a sink for header content"""
        self.header += buf

    def close(self):
        """Wrapper to close curl - this will allow curl to write out cookies"""
        self.curl.close()
