import datetime
import mimetypes
import os
import urllib
import time

import boto

from django.conf import settings
from django.http import HttpResponseRedirect

from license_protected_downloads.artifact.base import (
    Artifact,
    cached_prop,
)


class S3Artifact(Artifact):
    bucket = None

    @classmethod
    def get_bucket(cls):
        '''Keeps a single bucket object cached for the duration of a request'''
        if not cls.bucket:
            b = getattr(settings, 'S3_BUCKET', None)
            if b:
                c = boto.connect_s3(
                    settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
                cls.bucket = c.get_bucket(settings.S3_BUCKET)
        return cls.bucket

    def __init__(self, bucket, item, parent, human_readable):
        base = item.name.replace(settings.S3_PREFIX_PATH, '')
        if base:
            base = '/' + os.path.dirname(base)

        if hasattr(item, 'size'):
            file_name = os.path.basename(item.name)
            self.mtype = mimetypes.guess_type(item.name)[0]
            dt = datetime.datetime.strptime(
                item.last_modified, "%Y-%m-%dT%H:%M:%S.000Z")
            item.last_modified = time.mktime(dt.timetuple())
            self.item = item
        else:
            self.mtype = 'folder'
            self.children = []
            if base:
                base = os.path.dirname(base)
                file_name = os.path.basename(item.name[:-1])
            else:
                file_name = ''
            item.size = 0
            item.last_modified = '-'
        file_name = urllib.url2pathname(file_name)
        self.bucket = bucket
        self.parent = parent
        if parent and hasattr(self.parent, 'children'):
            self.parent.children.append(self)
        super(S3Artifact, self).__init__(
            base, file_name, item.size, item.last_modified, human_readable)

    def get_type(self):
        if self.human_readable:
            if self.mtype is None:
                return 'other'
            elif self.mtype.split('/')[0] == 'text':
                return 'text'
        return self.mtype

    def get_file_download_response(self, method='GET'):
        "Return HttpResponse which will send path to user's browser."
        assert not self.isdir()
        return HttpResponseRedirect(self.item.generate_url(90, method=method))

    @cached_prop
    def build_info_buffer(self):
        if self.parent and not self.isdir():
            return self.parent.build_info_buffer

        if self.urlbase == '/':
            key = settings.S3_PREFIX_PATH[:-1]
        else:
            key = settings.S3_PREFIX_PATH + self.urlbase[1:]

        if self.isdir():
            key += '/' + self.file_name
        key += '/BUILD-INFO.txt'

        try:
            key = boto.s3.key.Key(self.bucket, key)
            return key.get_contents_as_string()
        except boto.exception.S3ResponseError:
            pass  # No build-info file, return None - its okay

    @cached_prop
    def _container_eulas(self):
        if not self.isdir() and self.parent:
            return self.parent._container_eulas

        prefix = settings.S3_PREFIX_PATH + self.urlbase[1:]
        if prefix[-1] != '/':
            # s3 listing needs '/' to do a dir listing
            prefix = prefix + '/'

        if self.isdir():
            prefix += self.file_name + '/'

        eulas = []
        for x in self.bucket.list(prefix=prefix, delimiter='/'):
            if isinstance(x, boto.s3.key.Key) and 'EULA.txt' in x.name:
                eulas.append(os.path.basename(x.name))
        return eulas

    def get_eulas(self):
        '''find eulas for this artifact

        if this is a file, it will use the parent container's eula which
        we keep cached, so that we only hit s3 one time
        '''
        return self._container_eulas

    def get_file_contents(self, fname):
        if self.urlbase == '/':
            key = settings.S3_PREFIX_PATH[:-1]
        else:
            key = settings.S3_PREFIX_PATH + self.urlbase[1:]

        if self.isdir():
            key += '/' + self.file_name + '/' + fname
        else:
            key += '/' + os.path.dirname(self.file_name) + fname
        try:
            key = boto.s3.key.Key(self.bucket, urllib.pathname2url(key))
            return key.get_contents_as_string()
        except boto.exception.S3ResponseError:
            pass  # return None - its okay

    def get_textile_files(self):
        assert self.isdir()
        # NOTE: This logic is assuming some optimizations based on how files
        # are currently published. Legacy publishing required more complex
        # searching but all new publishing will work with this logic.
        allowed = settings.ANDROID_FILES + settings.LINUX_FILES
        for x in self.children:
            if not x.isdir() and os.path.basename(x.item.name) in allowed:
                yield (x.item.name, x.item)

    def get_annotated_manifest(self):
        assert self.isdir()
        for x in self.children:
            if not x.isdir() and \
                    os.path.basename(x.item.name) == settings.ANNOTATED_XML:
                return x.item.read()

    def isdir(self):
        return self.mtype == 'folder'

    def get_real_name(self):
        url = self.url()
        path = self.get_file_contents('.s3_linked_from')
        if path:
            path = path.replace(settings.S3_PREFIX_PATH, '/')
            url = url.replace(os.path.dirname(url), path)
        return url
