#!/usr/bin/python

import json
import urlparse
import shutil
import urllib2
import os
from html2text import html2text

# Example of how to use the API to download all files in a directory. This is
# written as one procedural script without functions
directory_url = "http://localhost:8001/build-info"

# Generate the URL that will return the license information. This is the URL
# of the file with /api/license prepended to the path.

# Unfortunately urlsplit returns an immutable object. Convert it to an array
# so we can modify the path section (index 2)
parsed_url = [c for c in urlparse.urlsplit(directory_url)]
url_path_section = parsed_url[2]

parsed_url[2] = "/api/ls" + url_path_section
listing_url = urlparse.urlunsplit(parsed_url)

u = urllib2.urlopen(listing_url)
data = json.loads(u.read())["files"]

for file_info in data:
    if file_info["type"] == "folder":
        # Skip folders...
        continue

    parsed_url[2] = "/api/license" + file_info["url"]
    license_url = urlparse.urlunsplit(parsed_url)

    parsed_url[2] = file_info["url"]
    file_url = urlparse.urlunsplit(parsed_url)

    # Get the licenses. They are returned as a JSON document in the form:
    # {"licenses":
    #  [{"text": "<license text>", "digest": "<digest of license>"},
    #   {"text": "<license text>", "digest": "<digest of license>"},
    #   ...
    # ]}
    # Each license has a digest associated with it.
    u = urllib2.urlopen(license_url)
    data = json.loads(u.read())["licenses"]

    if data[0] == "Open":
        headers = {}
    else:
        # If this were a command line client designed to ask the user to accept
        # each license, you could use this code to ask the user to accept each
        # license in turn. In this example we store which licenses are accepted
        # so the user only has to accept them once.
        if os.path.isfile("accepted_licenses"):
            with open("accepted_licenses") as accepted_licenses_file:
                accepted_licenses = accepted_licenses_file.read().split()
        else:
            accepted_licenses = []

        # Present each license to the user...
        for d in data:
            if d["digest"] not in accepted_licenses:
                # Licenses are stored as HTML. Convert them to markdown (text)
                # and print it to the terminal.
                print html2text(d["text"])

                # Ask the user if they accept the license. If they don't we
                # terminate the script.
                user_response = raw_input("Do you accept this license? (y/N)")
                if user_response != "y":
                    exit(1)

                accepted_licenses.append(d["digest"])

        # Store the licenses that the user accepted
        with open("accepted_licenses", "w") as accepted_licenses_file:
            accepted_licenses_file.write(" ".join(accepted_licenses))

        # To accept a license, place the digest in the LICENSE_ACCEPTED header.
        # For multiple licenses, they are stored space separated.
        digests = [d["digest"] for d in data]
        headers = {"LICENSE_ACCEPTED": " ".join(digests)}

    # Once the header has been generated, just download the file.
    req = urllib2.urlopen(urllib2.Request(file_url, headers=headers))
    with open(os.path.basename(parsed_url[2]), 'wb') as fp:
        shutil.copyfileobj(req, fp)
