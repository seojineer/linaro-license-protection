# Copyright (c)2012 Linaro.
# Test helpers.

import os
import shutil
import tempfile
import threading
import BaseHTTPServer
import SocketServer


class temporary_directory(object):
    """Creates a context manager for a temporary directory."""

    def __enter__(self):
        self.root = tempfile.mkdtemp()
        return self

    def __exit__(self, *args):
        shutil.rmtree(self.root)

    def make_file(self, name, data=None, with_buildinfo=False):
        """Creates a file in this temporary directory."""
        full_path = os.path.join(self.root, name)
        dir_name = os.path.dirname(full_path)
        try:
            os.makedirs(dir_name)
        except os.error:
            pass
        if with_buildinfo:
            buildinfo_name = os.path.join(dir_name, 'BUILD-INFO.txt')
            base_name = os.path.basename(full_path)
            with open(buildinfo_name, 'w') as buildinfo_file:
                buildinfo_file.write(
                    'Format-Version: 0.1\n\n'
                    'Files-Pattern: %s\n'
                    'License-Type: open\n' % base_name)
        target = open(full_path, "w")
        if data is None:
            return target
        else:
            target.write(data)
            target.close()
            return full_path


class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in self.urls:
            self.send_response(200, "OK")
            self.end_headers()
            self.request.sendall(self.urls[self.path])
        else:
            self.send_error(404, 'URL %s not found' % self.path)
            self.end_headers()


class ThreadedHTTPServer(SocketServer.ThreadingMixIn,
                         BaseHTTPServer.HTTPServer):
    pass


class TestHttpServer(object):
    """Creates a context manager for a temporary directory."""

    def __init__(self, urls):
        self.handler = HttpHandler
        self.handler.urls = urls

    def __enter__(self):
        self.server = ThreadedHTTPServer(
            ("localhost", 0), self.handler)
        self.ip, self.port = self.server.server_address
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()

    @property
    def base_url(self):
        return "http://%s:%s" % (self.ip, self.port)
