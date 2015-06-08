import fnmatch
import glob
import hashlib
import logging
import mimetypes
import os
import re
import traceback

from datetime import datetime

from django.conf import settings
from django.http import Http404

from license_protected_downloads import(
    buildinfo,
    models,
)


log = logging.getLogger("llp.views")


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


def _check_special_eula(path):
    if glob.glob(path + ".EULA.txt.*"):
        return True


def _get_theme(path):
    eula = glob.glob(path + ".EULA.txt.*")
    vendor = os.path.splitext(eula[0])[1]
    return vendor[1:]


def _insert_license_into_db(digest, text, theme):
    if not models.License.objects.filter(digest=digest):
        l = models.License(digest=digest, text=text, theme=theme)
        l.save()


def is_protected(path):
    build_info = None
    max_index = 1
    base_path = path
    if not os.path.isdir(base_path):
        base_path = os.path.dirname(base_path)

    buildinfo_path = os.path.join(base_path, "BUILD-INFO.txt")
    open_eula_path = os.path.join(base_path, "OPEN-EULA.txt")
    eula_path = os.path.join(base_path, "EULA.txt")

    if os.path.isfile(buildinfo_path):
        try:
            build_info = buildinfo.BuildInfo(path)
        except buildinfo.IncorrectDataFormatException:
            # If we can't parse the BuildInfo, return [], which indicates no
            # license in dir_list and will trigger a 403 error in file_server.
            return []

        license_type = build_info.get("license-type")
        license_text = build_info.get("license-text")
        theme = build_info.get("theme")
        auth_groups = build_info.get("auth-groups")
        max_index = build_info.max_index
    elif os.path.isfile(open_eula_path):
        return "OPEN"
    elif os.path.isfile(eula_path):
        if re.search("snowball", path):
            theme = "stericsson"
        elif re.search("origen", path):
            theme = "samsung"
        else:
            theme = "linaro"
        license_type = "protected"
        license_file = os.path.join(settings.PROJECT_ROOT,
                                    'templates/licenses/' + theme + '.txt')
        auth_groups = False
        with open(license_file, "r") as infile:
            license_text = infile.read()
    elif _check_special_eula(path):
        theme = _get_theme(path)
        license_type = "protected"
        license_file = os.path.join(settings.PROJECT_ROOT,
                                    'templates/licenses/' + theme + '.txt')
        auth_groups = False
        with open(license_file, "r") as infile:
            license_text = infile.read()
    elif _check_special_eula(base_path + "/*"):
        return "OPEN"
    else:
        return []

    digests = []

    if license_type:
        if license_type == "open":
            return "OPEN"

        if auth_groups and not license_text:
            return "OPEN"
        elif license_text:
            for i in range(max_index):
                if build_info:
                    license_text = build_info.get("license-text", i)
                    theme = build_info.get("theme", i)
                digest = hashlib.md5(license_text).hexdigest()
                digests.append(digest)
                _insert_license_into_db(digest, license_text, theme)
        else:
            log.info("No license text or auth groups found: check the "
                     "BUILD-INFO file.")

    return digests


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


def test_path(path, request):
    """Check that path points to something we can serve up.
    """
    served_paths, path = _find_served_paths(path, request)
    for basepath in served_paths:
        fullpath = safe_path_join(basepath, path)
        if fullpath is None:
            raise Http404
        if os.path.isfile(fullpath):
            return ("file", fullpath)
        if os.path.isdir(fullpath):
            return ("dir", fullpath)

        fullpath = _handle_wildcard(request, fullpath)
        if fullpath:
            return ('file', fullpath)

    raise Http404


def _hidden_file(file_name):
    hidden_files = ["BUILD-INFO.txt", "EULA.txt", "HEADER.html",
                    "HOWTO_", "textile", ".htaccess", "licenses"]
    for pattern in hidden_files:
        if re.search(pattern, file_name):
            return True
    return False


def _listdir(path):
    '''Lists the contents of a directory sorted to our requirements.

    If the directory is all numbers it sorts them numerically. The "latest"
    entry will always be the first entry. Else use standard sorting.
    '''
    def _sort(a, b):
        try:
            return cmp(int(a), int(b))
        except:
            pass
        if a == 'latest':
            return -1
        elif b == 'latest':
            return 1

        return cmp(a, b)
    files = os.listdir(path)
    files.sort(_sort)
    return files


def _sizeof_fmt(num):
    ''' Returns in human readable format for num.
    '''
    if num < 1024 and num > -1024:
        return str(num)
    num /= 1024.0
    for x in ['K', 'M', 'G']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'T')


class Artifact(object):
    def __init__(self, urlbase, file_name, human_readable, local_path):
        self.human_readable = human_readable
        self.file_name = file_name
        self.urlbase = urlbase
        self.full_path = os.path.join(local_path, file_name)

    def url(self):
        url = self.urlbase
        if url:
            if url[0] != '/':
                url = '/' + url
            if url[-1] != '/':
                url += '/'
        else:
            url = '/'
        return url + self.file_name

    def get_type(self):
        if os.path.isdir(self.full_path):
            return 'folder'
        else:
            mtype = mimetypes.guess_type(self.full_path)[0]
            if self.human_readable:
                if mtype is None:
                    mtype = 'other'
                elif mtype.split('/')[0] == 'text':
                    mtype = 'text'
            return mtype

    def get_size(self):
        size = 0
        # ensure the file we are looking at exists (not broken symlink)
        if os.path.exists(self.full_path):
            size = os.path.getsize(self.full_path)
            if self.human_readable:
                size = _sizeof_fmt(size)
        return size

    def get_mtime(self):
        mtime = 0
        # ensure the file we are looking at exists (not broken symlink)
        if os.path.exists(self.full_path):
            mtime = os.path.getmtime(self.full_path)
            if self.human_readable:
                mtime = datetime.fromtimestamp(mtime)
                mtime = mtime.strftime('%d-%b-%Y %H:%M')
        return mtime

    def get_listing(self):
        if os.path.isdir(self.full_path):
            ldl = []
        else:
            try:
                ldl = is_protected(self.full_path)
            except Exception as e:
                print("Invalid BUILD-INFO.txt for %s: %s" % (
                    self.full_path, repr(e)))
                traceback.print_exc()
                ldl = "INVALID"
        ll = models.License.objects.all_with_hashes(ldl)
        return {
            'name': self.file_name,
            'size': self.get_size(),
            'type': self.get_type(),
            'mtime': self.get_mtime(),
            'license_digest_list': ldl,
            'license_list': ll,
            'url': self.url(),
        }


def dir_list(url, path, human_readable=True):
    files = _listdir(path)
    listing = []

    for file_name in files:
        if not _hidden_file(file_name):
            artifact = Artifact(url, file_name, human_readable, path)
            listing.append(artifact.get_listing())
    return listing
