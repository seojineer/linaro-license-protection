import fnmatch
import os
import re

import boto

from django.conf import settings
from django.core.cache import cache
from django.http import Http404

from license_protected_downloads import models
from license_protected_downloads.artifact import(
    LocalArtifact,
    S3Artifact,
)


def safe_path_join(base_path, *paths):
    """os.path.join with check that result is inside base_path.

    Checks that the generated path doesn't end up outside the target
    directory, so server accesses stay where we expect them.
    """

    target_path = os.path.join(base_path, *paths)

    if not target_path.startswith(base_path):
        return None

    if not os.path.normpath(target_path) == target_path.rstrip("/"):
        return None

    return target_path


def cached_call(key, func, *args, **kwargs):
    key = func.__name__ + key
    v = cache.get(key)
    if v:
        return v
    v = func(*args, **kwargs)
    cache.set(key, v)
    return v


def _handle_wildcard(request, fullpath):
    path, name = os.path.split(fullpath)

    if not os.path.isdir(path):
        return None

    match = None
    for f in os.listdir(path):
        if fnmatch.fnmatch(f, name):
            if match:
                # change request.path so that the 404.html page can show
                # a descriptive error
                request.path = 'Multiple files match this expression'
                raise Http404
            match = os.path.join(path, f)
    return match


def _handle_s3_wildcard(request, bucket, prefix):
    prefix, base = os.path.split(prefix)
    if '*' in base or '?' in base:
        match = None
        prefix += '/'
        items = list(bucket.list(delimiter='/', prefix=prefix))
        for item in items:
            if fnmatch.fnmatch(os.path.basename(item.name), base):
                if match:
                    request.path = 'Multiple files match this expression'
                    raise Http404
                match = item
        if match:
            return S3Artifact(bucket, match, None, False)


def _find_served_paths(path, request):
    served_paths = settings.SERVED_PATHS
    # if key is in request.GET["key"] then need to mod path and give
    # access to a per-key directory.
    if "key" in request.GET:
        key_details = models.APIKeyStore.objects.filter(key=request.GET["key"])
        if key_details:
            path = os.path.join(request.GET["key"], path)

            # Private uploads are in a separate path (or can be), so set
            # served_paths as needed.
            if not key_details[0].public:
                served_paths = [settings.UPLOAD_PATH]
    return served_paths, path


def _find_s3_artifact(request, path):
    b = S3Artifact.get_bucket()
    if not b:
        return  # s3 isn't configured

    prefix = settings.S3_PREFIX_PATH + S3Artifact.pathname2url(path)
    if prefix[-1] == '/':
        # s3 listing give sub dir, we don't want that
        prefix = prefix[:-1]

    items = b.list(delimiter='/', prefix=prefix)
    for item in items:
        if isinstance(item, boto.s3.prefix.Prefix):
            if item.name == prefix + '/':
                return S3Artifact(b, item, None, False)
        else:
            if item.name == prefix:
                return S3Artifact(b, item, None, False)
    return _handle_s3_wildcard(request, b, prefix)


def find_artifact(request, path):
    """Return a Artifact object representing a directory or file we serve"""
    served_paths, path = _find_served_paths(path, request)
    for basepath in served_paths:
        fullpath = safe_path_join(basepath, path)
        if fullpath is None:
            break
        if os.path.isfile(fullpath) or os.path.isdir(fullpath):
            return LocalArtifact(None, '', path, False, basepath)

        fullpath = _handle_wildcard(request, fullpath)
        if fullpath:
            path = fullpath[len(basepath) + 1:]
            return LocalArtifact(None, '', path, False, basepath)

    r = _find_s3_artifact(request, path)
    if r:
        return r

    raise Http404


def _sort_artifacts(a, b):
    '''Ensures directory listings follow our ordering rules for artifacts.

    If the directory is all numbers it sorts them numerically. The "latest"
    entry will always be the first entry. Else use standard sorting.
    '''
    a = a.file_name
    b = b.file_name
    try:
        # we want listings of build numbers (integers) and releases (floats eg
        # "16.12" to listed in reverse order so they show newest to oldest
        return cmp(float(b), float(a))
    except:
        pass
    # always give preference to make "latest" show first
    if a == 'latest':
        return -1
    elif b == 'latest':
        return 1

    # just do a normal string sort
    return cmp(a, b)

def s3_replace_latest(url, bucket=None):
    ''' read .s3_linked_from file to find out the original directory to read from
    '''
    urlreg = r"^(?P<prefix>.*)/(?P<vers>latest.*)/(?P<target>.*)$"
    m = re.search(urlreg, url)
    if not m:
        return url

    link_from = '/'.join([m.group('prefix'),m.group('vers'), ".s3_linked_from"])

    if bucket is None:
        bucket = S3Artifact.get_bucket()

    s3path = settings.S3_PREFIX_PATH + link_from

    key = boto.s3.key.Key(bucket, s3path)
    # if there's no key already, there's no .s3_linked_from, so we're done here
    if key is None:
        return url
    try:
        redir_loc = key.get_contents_as_string().strip()
        # .s3_linked_from is referencing itself?  Should return original url
        if redir_loc == s3path:
            return url
        # scrub the s3 prefix
        new_url = re.sub("^%s" % settings.S3_PREFIX_PATH, '', redir_loc)
        # reconstruct the url
        if m.group('target') != "":
            new_url = "%s/%s" % (new_url, m.group('target'))
        return new_url
    except:
        # problem gettings contents, so stop trying to intercept the request
        return url


def _s3_list(bucket, url):
    prefix = settings.S3_PREFIX_PATH + url
    if prefix[-1] != '/':
        # s3 listing needs '/' to do a dir listing
        prefix = prefix + '/'
    prefix = s3_replace_latest(prefix, bucket)
    for item in bucket.list(delimiter='/', prefix=prefix):
        if item.name != prefix:
            yield item


def dir_list(artifact, human_readable=True):
    url = artifact.url()
    artifacts = []
    if isinstance(artifact, LocalArtifact):
        fp = artifact.full_path
        artifacts = [LocalArtifact(artifact, url, x, human_readable, fp)
                     for x in os.listdir(fp)]

    b = S3Artifact.get_bucket()
    if b:
        for item in _s3_list(b, url[1:]):
            artifacts.append(S3Artifact(b, item, artifact, human_readable))

    artifacts.sort(_sort_artifacts)

    # s3 and local could return duplicate names. Since the artifacts are sorted
    # we can check if the last names match and skip duplicates if needed. This
    # gives precedence to local artifacts since they show up first in the array
    last_name = None
    listing = []
    for artifact in artifacts:
        if last_name != artifact.file_name and not artifact.hidden():
            listing.append(artifact.get_listing())

        last_name = artifact.file_name
    return listing
