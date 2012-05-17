#!/usr/bin/env python

import argparse
import os
import pycurl
import re
import urlparse
import html2text
from BeautifulSoup import BeautifulSoup


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
    def __init__(self, cookie_file="cookies.txt"):
        """Set up cURL"""
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.WRITEFUNCTION, self._write_body)
        self.curl.setopt(pycurl.HEADERFUNCTION, self._write_header)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.COOKIEFILE, cookie_file)
        self.curl.setopt(pycurl.COOKIEJAR, cookie_file)
        self.file_out = None

    def _get(self, url):
        """Clear out header and body storage, fetch URL, filling them in."""
        url = url.encode("ascii")
        self.curl.setopt(pycurl.URL, url)

        self.body = ""
        self.header = ""

        if self.file_name:
            self.file_out = open(self.file_name, 'w')
        else:
            self.file_out = None

        self.curl.perform()
        self._parse_headers(url)

        if self.file_out:
            self.file_out.close()

    def _parse_headers(self, url):
        header = {}
        for line in self.header.splitlines():
            # Header lines typically are of the form thing: value...
            test_line = re.search("^(.*?)\s*:\s*(.*)$", line)

            if test_line:
                header[test_line.group(1)] = test_line.group(2)

        # The location attribute is sometimes relative, but we would
        # like to have it as always absolute...
        if 'Location' in header:
            parsed_location = urlparse.urlparse(header["Location"])

            # If not an absolute location...
            if not parsed_location.netloc:
                parsed_source_url = urlparse.urlparse(url)
                new_location = ["", "", "", "", ""]

                new_location[0] = parsed_source_url.scheme
                new_location[1] = parsed_source_url.netloc
                new_location[2] = header["Location"]

                # Update location with absolute URL
                header["Location"] = urlparse.urlunsplit(new_location)

        self.header_text = self.header
        self.header = header

    def get_headers(self, url):
        url = url.encode("ascii")
        self.curl.setopt(pycurl.URL, url)

        self.body = ""
        self.header = ""

        # Setting NOBODY causes CURL to just fetch the header.
        self.curl.setopt(pycurl.NOBODY, True)
        self.curl.perform()
        self.curl.setopt(pycurl.NOBODY, False)

        self._parse_headers(url)

        return self.header

    def get_or_return_license(self, url, file_name=None):
        """Get file at the requested URL or, if behind a license, return that.

        If the URL provided does not redirect us to a license, then return the
        body of that file. If we are redirected to a license click through
        then return (the license as plain text, url to accept the license).

        If the user of this function accepts the license, then they should
        call get_protected_file."""

        self.file_name = file_name

        # Get the license details. If this returns None, the file isn't license
        # protected and we can just return the file we started to get in the
        # function (self.body).
        license_details = self._get_license(url)

        if license_details:
            return license_details

        return self.body

    def get(self, url, file_name=None, ignore_license=False,
            accept_license=True):
        """Fetch the requested URL, accepting licenses

        Fetches the file at url. If a redirect is encountered, it is
        expected to be to a license that has an accept link. Follow that link,
        then download the original file. Returns the fist 1MB of the file
        (see _write_body).

        """

        self.file_name = file_name
        if ignore_license:
            self._get(url)
            return self.body

        license_details = self._get_license(url)

        if license_details:
            # Found a license.
            if accept_license:
                # Accept the license without looking at it and
                # start fetching the file we originally wanted.
                accept_url = license_details[1]
                self.get_protected_file(accept_url, url)
            else:
                # We want to decline the license and return the notice.
                decline_url = license_details[2]
                self._get(decline_url)

        else:
            # If we got here, there wasn't a license protecting the file
            # so we just fetch it.
            self._get(url)

        return self.body

    def _get_license(self, url):
        """Return (license, accept URL, decline URL) if found,
        else return None.

        """

        self.get_headers(url)

        if "Location" in self.header and self.header["Location"] != url:
            # We have been redirected to a new location - the license file
            location = self.header["Location"]

            # Fetch the license HTML
            self._get(location)

            # Get the file from the URL (full path)
            file = urlparse.urlparse(location).path

            # Get the file without the rest of the path
            file = os.path.split(file)[-1]

            # Look for a link with accepted.html in the page name. Follow it.
            accept_search, decline_search = None, None
            for line in self.body.splitlines():
                if not accept_search:
                    accept_search = re.search(
                    """href=.*?["'](.*?-accepted.html)""",
                    line)
                if not decline_search:
                    decline_search = re.search(
                    """href=.*?["'](.*?-declined.html)""",
                    line)

            if accept_search and decline_search:
                # Have found license accept URL!
                new_file = accept_search.group(1)
                accept_url = re.sub(file, new_file, location)

                # Found decline URL as well.
                new_file_decline = decline_search.group(1)
                decline_url = re.sub(file, new_file_decline, location)

                # Parse the HTML using BeautifulSoup
                soup = BeautifulSoup(self.body)

                # The license is in a div with the ID license-text, so we
                # use this to pull just the license out of the HTML.
                html_license = u""
                for chunk in soup.findAll(id="license-text"):
                    # Output of chunk.prettify is UTF8, but comes back
                    # as a str, so convert it here.
                    html_license += chunk.prettify().decode("utf-8")

                text_license = html2text.html2text(html_license)

                return text_license, accept_url, decline_url

        return None

    def get_protected_file(self, accept_url, url):
        """Gets the file redirected to by the accept_url"""

        self._get(accept_url)  # Accept the license

        if not("Location" in self.header and self.header["Location"] == url):
            # If we got here, we don't have the file yet (weren't redirected
            # to it). Fetch our target file. This should work now that we have
            # the right cookie.
            self._get(url)  # Download the target file

        return self.body

    def _write_body(self, buf):
        """Used by curl as a sink for body content"""

        # If we have a target file to write to, write to it
        if self.file_out:
            self.file_out.write(buf)

        # Only buffer first 1MB of body. This should be plenty for anything
        # we wish to parse internally.
        if len(self.body) < 1024 * 1024 * 1024:
            # XXX Would be nice to stop keeping the file in RAM at all and
            # passing large buffers around. Perhaps only keep in RAM if
            # file_name == None? (used for getting directory listings
            # normally).
            self.body += buf

    def _write_header(self, buf):
        """Used by curl as a sink for header content"""
        self.header += buf

    def register_progress_callback(self, callback):
        self.curl.setopt(pycurl.NOPROGRESS, 0)
        self.curl.setopt(pycurl.PROGRESSFUNCTION, callback)

    def close(self):
        """Wrapper to close curl - this will allow curl to write out cookies"""
        self.curl.close()


def main():
    """Download file specified on command line"""
    parser = argparse.ArgumentParser(description="Download a file, accepting "
                                    "any licenses required to do so.")

    parser.add_argument('url', metavar="URL", type=str, nargs=1,
                        help="URL of file to download.")

    args = parser.parse_args()

    fetcher = LicenseProtectedFileFetcher()

    # Get file name from URL
    file_name = os.path.basename(urlparse.urlparse(args.url[0]).path)
    if not file_name:
        file_name = "downloaded"
    fetcher.get(args.url[0], file_name)

    fetcher.close()

if __name__ == "__main__":
    main()
