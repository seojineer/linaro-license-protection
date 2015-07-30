import fnmatch
import glob
import hashlib
import logging
import mimetypes
import os
import re
import traceback

from datetime import datetime

from BeautifulSoup import BeautifulSoup
from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.encoding import smart_str

from license_protected_downloads import(
    buildinfo,
    models,
    render_text_files,
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


def _insert_license_into_db(digest, text, theme):
    if not models.License.objects.filter(digest=digest):
        l = models.License(digest=digest, text=text, theme=theme)
        l.save()


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


def find_artifact(request, path):
    """Return a Artifact object representing a directory or file we serve"""
    served_paths, path = _find_served_paths(path, request)
    for basepath in served_paths:
        fullpath = safe_path_join(basepath, path)
        if fullpath is None:
            raise Http404
        if os.path.isfile(fullpath) or os.path.isdir(fullpath):
            return LocalArtifact(None, '', path, False, basepath)

        fullpath = _handle_wildcard(request, fullpath)
        if fullpath:
            basepath, path = os.path.split(fullpath)
            return LocalArtifact(None, '', path, False, basepath)

    raise Http404


def _sort_artifacts(a, b):
    '''Ensures directory listings follow our ordering rules for artifacts.

    If the directory is all numbers it sorts them numerically. The "latest"
    entry will always be the first entry. Else use standard sorting.
    '''
    a = a.file_name
    b = b.file_name
    try:
        return cmp(int(a), int(b))
    except:
        pass
    if a == 'latest':
        return -1
    elif b == 'latest':
        return 1

    return cmp(a, b)


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


def cached_prop(fn):
    attr_name = '_cached_' + fn.__name__

    @property
    def _cached_prop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _cached_prop


class Artifact(object):
    LINARO_INCLUDE_FILE_RE = re.compile(
        r'<linaro:include file="(?P<file_name>.*)"[ ]*/>')
    LINARO_INCLUDE_FILE_RE1 = re.compile(
        r'<linaro:include file="(?P<file_name>.*)">(.*)</linaro:include>')

    def __init__(self, urlbase, file_name, size, mtime, human_readable):
        self.urlbase = urlbase
        self.file_name = file_name
        self.size = size
        self.mtime = mtime
        self.human_readable = human_readable

        if human_readable:
            self.size = _sizeof_fmt(size)
            mtime = datetime.fromtimestamp(mtime)
            self.mtime = mtime.strftime('%d-%b-%Y %H:%M')

    def isdir(self):
        raise RuntimeError()

    def hidden(self):
        hidden_files = ["BUILD-INFO.txt", "EULA.txt", "HEADER.html",
                        "HOWTO_", "textile", ".htaccess", "licenses"]
        for pattern in hidden_files:
            if re.search(pattern, self.file_name):
                return True
        return False

    def url(self):
        url = self.urlbase
        if url:
            if url[0] != '/':
                url = '/' + url
            if url[-1] != '/':
                url += '/'
        else:
            url = '/'
        url = url + self.file_name
        if self.isdir() and url[-1] != '/':
            url += '/'
        return url

    def get_type(self):
        raise NotImplementedError()

    def get_eulas(self):
        raise NotImplementedError()

    def get_file_download_response(self):
        raise NotImplementedError()

    def get_textile_files(self):
        raise NotImplementedError()

    def get_build_info(self):
        buf = self.build_info_buffer
        if buf:
            # directory listings are handled specially, the build-info logic
            # will get license-digests for *all* files iff you pass no
            # file-name to its constructor
            if self.isdir():
                return buildinfo.BuildInfoBase('', buf)
            return buildinfo.BuildInfoBase(self.file_name, buf)

    def get_listing(self):
        if self.isdir():
            ldl = []
        else:
            try:
                ldl = self.get_license_digests()
            except Exception as e:
                print("Invalid BUILD-INFO.txt for %s: %s" % (
                    self.full_path, repr(e)))
                traceback.print_exc()
                ldl = "INVALID"
        ll = models.License.objects.all_with_hashes(ldl)
        return {
            'name': self.file_name,
            'size': self.size,
            'mtime': self.mtime,
            'license_digest_list': ldl,
            'license_list': ll,
            'type': self.get_type(),
            'url': self.url(),
        }

    def get_digest(self, lic_type, lic_text, theme, auth_groups):
        if lic_type == 'open' or (auth_groups and not lic_text):
            return 'OPEN'

        if not lic_text:
            log.info('No license text or auth groups found: check the '
                     'BUILD-INFO file.')
            return

        digest = hashlib.md5(lic_text).hexdigest()
        _insert_license_into_db(digest, lic_text, theme)
        return digest

    def get_build_info_digests(self, bi):
        digests = []

        lic_type = bi.get('license-type')
        auth_groups = bi.get('auth-groups')
        for i in range(bi.max_index):
            lic_txt = bi.get('license-text', i)
            theme = bi.get('theme', i)
            d = self.get_digest(lic_type, lic_txt, theme, auth_groups)
            if d == 'OPEN':
                return d
            elif d:
                digests.append(d)
        return digests

    def get_eula_digests(self):
        path = self.urlbase + self.file_name
        theme = 'linaro'
        if 'snowball' in path:
            theme = 'stericsson'
        elif 'origen' in path:
            theme = 'samsung'
        lic_type = 'protected'
        lic_file = os.path.join(
            settings.PROJECT_ROOT, 'templates/licenses/' + theme + '.txt')
        with open(lic_file) as f:
            lic_txt = f.read()
            return [self.get_digest(lic_type, lic_txt, theme, None)]

    def get_license_digests(self):
        bi = self.get_build_info()
        if bi:
            return self.get_build_info_digests(bi)

        eulas = self.get_eulas()

        if self.has_open_eula(eulas):
            return 'OPEN'

        if self.has_eula(eulas):
            return self.get_eula_digests()

        theme = self.get_eula_per_file_theme(eulas)
        if theme:
            lic_file = os.path.join(settings.PROJECT_ROOT,
                                    'templates/licenses/' + theme + '.txt')
            with open(lic_file) as f:
                lic_txt = f.read()
            return [self.get_digest('protected', lic_txt, theme, None)]

        if self.has_per_file_eulas(eulas):
            return 'OPEN'

        return []

    def has_open_eula(self, eulas):
        for x in eulas:
            if 'OPEN-EULA.txt' in x:
                return True

    def has_eula(self, eulas):
        for x in eulas:
            if x == 'EULA.txt':
                return True

    def get_eula_per_file_theme(self, eulas):
        eula_pat = os.path.basename(self.file_name) + '.EULA.txt'
        for x in eulas:
            if eula_pat in x:
                vendor = os.path.splitext(x)[1]
                return vendor[1:]

    def has_per_file_eulas(self, eulas):
        return len(eulas) > 0

    def get_file_contents(self, fname):
        raise NotImplementedError

    def _process_include_tags(self, content):
        """Replaces <linaro:include file="README" /> or
        <linaro:include file="README">text to show</linaro:include> tags
        with content of README file or empty string if file not found or
        not allowed.
        """
        def read_func(matchobj):
            fname = matchobj.group('file_name')
            if os.path.normpath(fname) == os.path.basename(fname):
                return self.get_file_contents(fname)

        content = re.sub(self.LINARO_INCLUDE_FILE_RE, read_func, content)
        content = re.sub(self.LINARO_INCLUDE_FILE_RE1, read_func, content)
        return content

    def get_header_html(self):
        """Read HEADER.html in current directory

        If exists and return contents of <div id="content"> block
        """
        assert self.isdir()

        content = ''
        body = self.get_file_contents('HEADER.html')
        if body:
            body = self._process_include_tags(body)
            soup = BeautifulSoup(body)
            for chunk in soup.findAll(id='content'):
                content += chunk.prettify().decode('utf-8')

            content = '\n'.join(content.split('\n')[1:-1])
        return content

    def get_annotated_manifest(self):
        assert self.isdir()
        return self.get_file_contents(settings.ANNOTATED_XML)


class LocalArtifact(Artifact):
    '''An artifact that lives on the local filesystem'''
    def __init__(self, parent, urlbase, file_name, human_readable, path):
        self.parent = parent
        self.full_path = os.path.join(path, file_name)

        size = mtime = 0
        # ensure the file we are looking at exists (not broken symlink)
        if os.path.exists(self.full_path):
            size = os.path.getsize(self.full_path)
            mtime = os.path.getmtime(self.full_path)
        super(LocalArtifact, self).__init__(
            urlbase, file_name, size, mtime, human_readable)

    def get_type(self):
        if self.isdir():
            return 'folder'
        else:
            mtype = mimetypes.guess_type(self.full_path)[0]
            if self.human_readable:
                if mtype is None:
                    mtype = 'other'
                elif mtype.split('/')[0] == 'text':
                    mtype = 'text'
            return mtype

    def get_file_download_response(self):
        "Return HttpResponse which will send path to user's browser."
        assert not self.isdir()
        file_name = os.path.basename(self.full_path)
        mime = mimetypes.guess_type(file_name)[0]
        if mime is None:
            mime = "application/force-download"
        response = HttpResponse(mimetype=mime)
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           smart_str(file_name))
        response['X-Sendfile'] = smart_str(self.full_path)
        return response

    @cached_prop
    def build_info_buffer(self):
        if self.parent and not self.isdir():
            return self.parent.build_info_buffer

        p = buildinfo.BuildInfo.get_search_path(self.full_path)
        p = os.path.join(p, 'BUILD-INFO.txt')
        if os.path.exists(p):
            with open(p) as f:
                return f.read()

    def get_eulas(self):
        if self.isdir():
            path = self.full_path
        else:
            path = os.path.dirname(self.full_path)
        eulas = glob.glob(path + '/*EULA.txt*')
        return [os.path.basename(x) for x in eulas]

    def get_file_contents(self, fname):
        fname = os.path.join(self.full_path, fname)
        if os.path.isfile(fname) and not os.path.islink(fname):
            with open(fname, 'r') as f:
                return f.read()

    def get_textile_files(self):
        assert self.isdir()
        files = render_text_files.RenderTextFiles.find_relevant_files(
            self.full_path)
        for f in files:
            with open(f) as fd:
                yield f, fd

    def isdir(self):
        return os.path.isdir(self.full_path)


def dir_list(artifact, human_readable=True):
    path = artifact.full_path
    url = artifact.url()
    artifacts = [LocalArtifact(artifact, url, x, human_readable, path)
                 for x in os.listdir(path)]
    artifacts.sort(_sort_artifacts)

    listing = []
    for artifact in artifacts:
        if not artifact.hidden():
            listing.append(artifact.get_listing())
    return listing
