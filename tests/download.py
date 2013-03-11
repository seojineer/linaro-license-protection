#!/usr/bin/python

import json
import urlparse
import shutil
import urllib2
import os

# Example of how to use the API to download a file from a known location
url = "http://localhost:8001/build-info/multi-license.txt"

# Generate the URL that will return the license information. This is the URL
# if the file with /api/license prepended to the path.

# Unfortunately urlsplit returns an immutable object. Convert it to an array
# so we can modify the path section (index 2)
parsed_url = [c for c in urlparse.urlsplit(url)]
parsed_url[2] = "/api/license" + parsed_url[2]
license_url = urlparse.urlunsplit(parsed_url)

# Get the licenses. They are returned as a JSON document in the form:
# {"licenses":
#  [{"text": "<license text>", "digest": "<digest of license>"},
#   {"text": "<license text>", "digest": "<digest of license>"},
#   ...
# ]}
# Each license has a digest associated with it.
u = urllib2.urlopen(license_url)
data = json.loads(u.read())["licenses"]

# If this were a command line client designed to ask the user to accept each
# license, you would print the licenses here and use
# raw_input("Do you accept this license? (y/N)") to get the user's response.

# To accept a license, place the digest in the LICENSE_ACCEPTED header. For
# multiple licenses, they are stored space separated.
digests = [d["digest"] for d in data]
headers = {"LICENSE_ACCEPTED": " ".join(digests)}

# Once the header has been generated, just download the file.
req = urllib2.urlopen(urllib2.Request(url, headers=headers))
with open(os.path.basename(parsed_url[2]), 'wb') as fp:
    shutil.copyfileobj(req, fp)
