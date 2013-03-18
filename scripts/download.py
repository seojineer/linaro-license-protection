#!/usr/bin/python

import json
import urlparse
import shutil
import urllib2
import os
from html2text import html2text
import sys
import xdg.BaseDirectory as xdgBaseDir


def download(api_urls, accepted_licenses):
    """Example of how to use the API to download a/all files in a directory."""

    # Get listing for file(s) pointed to by URL we were given
    request = urllib2.urlopen(api_urls.ls())
    listing = json.loads(request.read())["files"]

    for file_info in listing:
        if file_info["type"] == "folder":
            # Skip folders...
            continue

        # Get the licenses. They are returned as a JSON document in the form:
        # {"licenses":
        #  [{"text": "<license text>", "digest": "<digest of license>"},
        #   {"text": "<license text>", "digest": "<digest of license>"},
        #   ...
        # ]}
        # Each license has a digest associated with it.
        request = urllib2.urlopen(api_urls.license(file_info["url"]))
        licenses = json.loads(request.read())["licenses"]

        if licenses[0] == "Open":
            headers = {}
        else:
            # Present each license to the user...
            for lic in licenses:
                if lic["digest"] not in accepted_licenses:
                    # Licenses are stored as HTML. Convert them to markdown
                    # (text) and print it to the terminal.
                    print html2text(lic["text"])

                    # Ask the user if they accept the license. If they don't we
                    # terminate the script.
                    user_response = raw_input(
                                        "Do you accept this license? (y/N)")
                    if user_response != "y":
                        exit(1)

                    # Remember this license acceptance for another download.
                    accepted_licenses.append(lic["digest"])

            # To accept a license, place the digest in the LICENSE_ACCEPTED
            # header. For multiple licenses, they are stored space separated.
            digests = [lic["digest"] for lic in licenses]
            headers = {"LICENSE_ACCEPTED": " ".join(digests)}

        # Once the header has been generated, just download the file.
        req = urllib2.urlopen(urllib2.Request(api_urls.file(file_info["url"]),
                                              headers=headers))
        with open(os.path.basename(file_info["url"]), 'wb') as fp:
            shutil.copyfileobj(req, fp)


class ApiUrls():
    """Since we want to manipulate URLS, but urlsplit returns an immutable
    object this is a convenience object to perform the manipulations for us"""
    def __init__(self, input_url):
        self.parsed_url = [c for c in urlparse.urlsplit(input_url)]
        self.path = self.parsed_url[2]

    def ls(self, path=None):
        if not path:
            path = self.path
        self.parsed_url[2] = "/api/ls" + path
        return urlparse.urlunsplit(self.parsed_url)

    def license(self, path):
        self.parsed_url[2] = "/api/license" + path
        return urlparse.urlunsplit(self.parsed_url)

    def file(self, path):
        self.parsed_url[2] = path
        return urlparse.urlunsplit(self.parsed_url)


if __name__ == '__main__':
    if len(sys.argv) != 2:
    # Check that a URL has been supplied.
        print >> sys.stderr, "Usage: download.py <URL>"
        exit(1)

    accepted_licenses_path = os.path.join(xdgBaseDir.xdg_data_home,
                                          "linaro",
                                          "accepted_licenses")

    # Later we ask the user to accept each license in turn. Store which
    # licenses are accepted so the user only has to accept them once.
    if os.path.isfile(accepted_licenses_path):
        with open(accepted_licenses_path) as accepted_licenses_file:
            accepted_licenses = accepted_licenses_file.read().split()
    else:
        accepted_licenses = []

    api_urls = ApiUrls(sys.argv[1])

    download(api_urls, accepted_licenses)

    # Store the licenses that the user accepted
    with open(accepted_licenses_path, "w") as accepted_licenses_file:
        accepted_licenses_file.write(" ".join(accepted_licenses))
