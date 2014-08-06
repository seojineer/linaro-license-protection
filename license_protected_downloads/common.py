import glob
import hashlib
import logging
import mimetypes
import os
import re

from datetime import datetime

from django.conf import settings

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


def test_path(path, request):
    """Check that path points to something we can serve up.
    """
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

    for basepath in served_paths:
        fullpath = safe_path_join(basepath, path)
        if fullpath is None:
            return None
        if os.path.isfile(fullpath):
            return ("file", fullpath)
        if os.path.isdir(fullpath):
            return ("dir", fullpath)


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


def dir_list(url, path, human_readable=True):
    files = _listdir(path)
    listing = []

    for file_name in files:
        if _hidden_file(file_name):
            continue

        name = file_name
        file_name = os.path.join(path, file_name)

        if os.path.exists(file_name):
            mtime = os.path.getmtime(file_name)
        else:
            # If the file we are looking at doesn't exist (broken symlink for
            # example), it doesn't have a mtime.
            mtime = 0

        if os.path.isdir(file_name):
            target_type = "folder"
        else:
            target_type = mimetypes.guess_type(name)[0]

        if os.path.exists(file_name):
            size = os.path.getsize(file_name)
        else:
            # If the file we are looking at doesn't exist (broken symlink for
            # example), it doesn't have a size
            size = 0

        if not re.search(r'^/', url) and url != '':
            url = '/' + url

        # Since the code below assume no trailing slash, make sure that
        # there isn't one.
        url = re.sub(r'/$', '', url)

        if human_readable:
            if mtime:
                mtime = datetime.fromtimestamp(mtime)
                mtime = mtime.strftime('%d-%b-%Y %H:%M')
            if target_type:
                if target_type.split('/')[0] == "text":
                    target_type = "text"
            else:
                target_type = "other"

            size = _sizeof_fmt(size)

        pathname = os.path.join(path, name)
        license_digest_list = is_protected(pathname)
        license_list = models.License.objects.all_with_hashes(
            license_digest_list)
        listing.append({'name': name,
                        'size': size,
                        'type': target_type,
                        'mtime': mtime,
                        'license_digest_list': license_digest_list,
                        'license_list': license_list,
                        'url': url + '/' + name})
    return listing
