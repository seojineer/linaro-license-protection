import glob
import mimetypes
import os

from django.http import HttpResponse
from django.utils.encoding import smart_str

from license_protected_downloads import(
    buildinfo,
    render_text_files,
)
from license_protected_downloads.artifact.base import (
    Artifact,
    cached_prop,
)


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
        response = HttpResponse(content_type=mime)
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

    def get_real_name(self):
        base_len = len(self.full_path) - len(self.file_name)
        rp = os.path.realpath(self.full_path)
        return '/' + rp[base_len:]
