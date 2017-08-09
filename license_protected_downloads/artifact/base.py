import datetime
import hashlib
import logging
import os
import re
import traceback

from BeautifulSoup import BeautifulSoup
from django.conf import settings

from license_protected_downloads import(
    buildinfo,
    models,
)
from license_protected_downloads.render_text_files import RenderTextFiles

log = logging.getLogger("llp.views")


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


def _insert_license_into_db(digest, text, theme):
    if not models.License.objects.filter(digest=digest):
        l = models.License(digest=digest, text=text, theme=theme)
        l.save()


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
            if type(mtime) == float:
                mtime = datetime.datetime.fromtimestamp(mtime)
                self.mtime = mtime.strftime('%d-%b-%Y %H:%M')

    def isdir(self):
        raise RuntimeError()

    def hidden(self):
        hidden_files = ["BUILD-INFO.txt", "EULA.txt", "HEADER.html",
                        "HEADER.textile", "HOWTO_", "textile", ".htaccess",
                        "licenses", ".s3_linked_from"]
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

    def get_file_download_response(self, method='GET', force_http=False):
        raise NotImplementedError()

    def get_textile_files(self):
        raise NotImplementedError()

    def get_real_name(self):
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
                    self.url, repr(e)))
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
        """Read HEADER.html or HEADER.textile in current directory

        If exists and return contents of <div id="content"> block
        """
        assert self.isdir()

        content = ''
        body = self.get_file_contents('HEADER.textile')
        if body:
            content = RenderTextFiles.render_buff(body)
            if content:
                return content

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
