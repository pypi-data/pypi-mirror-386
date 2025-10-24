# test_web.py -- Tests for the git HTTP server
# Copyright (C) 2010 Google, Inc.
#
# SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-or-later
# Dulwich is dual-licensed under the Apache License, Version 2.0 and the GNU
# General Public License as published by the Free Software Foundation; version 2.0
# or (at your option) any later version. You can redistribute it and/or
# modify it under the terms of either of these two licenses.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You should have received a copy of the licenses; if not, see
# <http://www.gnu.org/licenses/> for a copy of the GNU General Public License
# and <http://www.apache.org/licenses/LICENSE-2.0> for a copy of the Apache
# License, Version 2.0.
#

"""Tests for the Git HTTP server."""

import gzip
import os
import re
from io import BytesIO
from typing import NoReturn

from dulwich.object_store import MemoryObjectStore
from dulwich.objects import Blob
from dulwich.repo import BaseRepo, MemoryRepo
from dulwich.server import DictBackend
from dulwich.tests.utils import make_object, make_tag
from dulwich.web import (
    HTTP_ERROR,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_OK,
    GunzipFilter,
    HTTPGitApplication,
    HTTPGitRequest,
    _LengthLimitedFile,
    get_idx_file,
    get_info_packs,
    get_info_refs,
    get_loose_object,
    get_pack_file,
    get_text_file,
    handle_service_request,
    send_file,
)

from . import TestCase


class MinimalistWSGIInputStream:
    """WSGI input stream with no 'seek()' and 'tell()' methods."""

    def __init__(self, data) -> None:
        self.data = data
        self.pos = 0

    def read(self, howmuch):
        start = self.pos
        end = self.pos + howmuch
        if start >= len(self.data):
            return b""
        self.pos = end
        return self.data[start:end]


class MinimalistWSGIInputStream2(MinimalistWSGIInputStream):
    """WSGI input stream with no *working* 'seek()' and 'tell()' methods."""

    def seek(self, pos) -> NoReturn:
        raise NotImplementedError

    def tell(self) -> NoReturn:
        raise NotImplementedError


class TestHTTPGitRequest(HTTPGitRequest):
    """HTTPGitRequest with overridden methods to help test caching."""

    def __init__(self, *args, **kwargs) -> None:
        HTTPGitRequest.__init__(self, *args, **kwargs)
        self.cached = None

    def nocache(self) -> None:
        self.cached = False

    def cache_forever(self) -> None:
        self.cached = True


class WebTestCase(TestCase):
    """Base TestCase with useful instance vars and utility functions."""

    _req_class: type[HTTPGitRequest] = TestHTTPGitRequest

    def setUp(self) -> None:
        super().setUp()
        self._environ = {}
        self._req = self._req_class(
            self._environ, self._start_response, handlers=self._handlers()
        )
        self._status = None
        self._headers = []
        self._output = BytesIO()

    def _start_response(self, status, headers):
        self._status = status
        self._headers = list(headers)
        return self._output.write

    def _handlers(self) -> None:
        return None

    def assertContentTypeEquals(self, expected) -> None:
        self.assertIn(("Content-Type", expected), self._headers)


def _test_backend(objects, refs=None, named_files=None):
    if not refs:
        refs = {}
    if not named_files:
        named_files = {}
    repo = MemoryRepo.init_bare(objects, refs)
    for path, contents in named_files.items():
        repo._put_named_file(path, contents)
    return DictBackend({"/": repo})


class DumbHandlersTestCase(WebTestCase):
    def test_send_file_not_found(self) -> None:
        list(send_file(self._req, None, "text/plain"))
        self.assertEqual(HTTP_NOT_FOUND, self._status)

    def test_send_file(self) -> None:
        f = BytesIO(b"foobar")
        output = b"".join(send_file(self._req, f, "some/thing"))
        self.assertEqual(b"foobar", output)
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("some/thing")
        self.assertTrue(f.closed)

    def test_send_file_buffered(self) -> None:
        bufsize = 10240
        xs = b"x" * bufsize
        f = BytesIO(2 * xs)
        self.assertEqual([xs, xs], list(send_file(self._req, f, "some/thing")))
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("some/thing")
        self.assertTrue(f.closed)

    def test_send_file_error(self) -> None:
        class TestFile:
            def __init__(self, exc_class) -> None:
                self.closed = False
                self._exc_class = exc_class

            def read(self, size=-1) -> NoReturn:
                raise self._exc_class

            def close(self) -> None:
                self.closed = True

        f = TestFile(IOError)
        list(send_file(self._req, f, "some/thing"))
        self.assertEqual(HTTP_ERROR, self._status)
        self.assertTrue(f.closed)
        self.assertFalse(self._req.cached)

        # non-IOErrors are reraised
        f = TestFile(AttributeError)
        self.assertRaises(AttributeError, list, send_file(self._req, f, "some/thing"))
        self.assertTrue(f.closed)
        self.assertFalse(self._req.cached)

    def test_get_text_file(self) -> None:
        backend = _test_backend([], named_files={"description": b"foo"})
        mat = re.search(".*", "description")
        output = b"".join(get_text_file(self._req, backend, mat))
        self.assertEqual(b"foo", output)
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("text/plain")
        self.assertFalse(self._req.cached)

    def test_get_loose_object(self) -> None:
        blob = make_object(Blob, data=b"foo")
        backend = _test_backend([blob])
        mat = re.search("^(..)(.{38})$", blob.id.decode("ascii"))
        output = b"".join(get_loose_object(self._req, backend, mat))
        self.assertEqual(blob.as_legacy_object(), output)
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("application/x-git-loose-object")
        self.assertTrue(self._req.cached)

    def test_get_loose_object_missing(self) -> None:
        mat = re.search("^(..)(.{38})$", "1" * 40)
        list(get_loose_object(self._req, _test_backend([]), mat))
        self.assertEqual(HTTP_NOT_FOUND, self._status)

    def test_get_loose_object_error(self) -> None:
        blob = make_object(Blob, data=b"foo")
        backend = _test_backend([blob])
        mat = re.search("^(..)(.{38})$", blob.id.decode("ascii"))

        def as_legacy_object_error(self) -> NoReturn:
            raise OSError

        self.addCleanup(setattr, Blob, "as_legacy_object", Blob.as_legacy_object)
        Blob.as_legacy_object = as_legacy_object_error
        list(get_loose_object(self._req, backend, mat))
        self.assertEqual(HTTP_ERROR, self._status)

    def test_get_pack_file(self) -> None:
        pack_name = os.path.join("objects", "pack", "pack-%s.pack" % ("1" * 40))
        backend = _test_backend([], named_files={pack_name: b"pack contents"})
        mat = re.search(".*", pack_name)
        output = b"".join(get_pack_file(self._req, backend, mat))
        self.assertEqual(b"pack contents", output)
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("application/x-git-packed-objects")
        self.assertTrue(self._req.cached)

    def test_get_idx_file(self) -> None:
        idx_name = os.path.join("objects", "pack", "pack-%s.idx" % ("1" * 40))
        backend = _test_backend([], named_files={idx_name: b"idx contents"})
        mat = re.search(".*", idx_name)
        output = b"".join(get_idx_file(self._req, backend, mat))
        self.assertEqual(b"idx contents", output)
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("application/x-git-packed-objects-toc")
        self.assertTrue(self._req.cached)

    def test_get_info_refs(self) -> None:
        self._environ["QUERY_STRING"] = ""

        blob1 = make_object(Blob, data=b"1")
        blob2 = make_object(Blob, data=b"2")
        blob3 = make_object(Blob, data=b"3")

        tag1 = make_tag(blob2, name=b"tag-tag")

        objects = [blob1, blob2, blob3, tag1]
        refs = {
            b"HEAD": b"000",
            b"refs/heads/master": blob1.id,
            b"refs/tags/tag-tag": tag1.id,
            b"refs/tags/blob-tag": blob3.id,
        }
        backend = _test_backend(objects, refs=refs)

        mat = re.search(".*", "//info/refs")
        self.assertEqual(
            [
                blob1.id + b"\trefs/heads/master\n",
                blob3.id + b"\trefs/tags/blob-tag\n",
                tag1.id + b"\trefs/tags/tag-tag\n",
                blob2.id + b"\trefs/tags/tag-tag^{}\n",
            ],
            list(get_info_refs(self._req, backend, mat)),
        )
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("text/plain")
        self.assertFalse(self._req.cached)

    def test_get_info_refs_not_found(self) -> None:
        self._environ["QUERY_STRING"] = ""

        objects = []
        refs = {}
        backend = _test_backend(objects, refs=refs)

        mat = re.search("info/refs", "/foo/info/refs")
        self.assertEqual(
            [b"No git repository was found at /foo"],
            list(get_info_refs(self._req, backend, mat)),
        )
        self.assertEqual(HTTP_NOT_FOUND, self._status)
        self.assertContentTypeEquals("text/plain")

    def test_get_info_packs(self) -> None:
        class TestPackData:
            def __init__(self, sha) -> None:
                self.filename = f"pack-{sha}.pack"

        class TestPack:
            def __init__(self, sha) -> None:
                self.data = TestPackData(sha)

        packs = [TestPack(str(i) * 40) for i in range(1, 4)]

        class TestObjectStore(MemoryObjectStore):
            # property must be overridden, can't be assigned
            @property
            def packs(self):
                return packs

        store = TestObjectStore()
        repo = BaseRepo(store, None)
        backend = DictBackend({"/": repo})
        mat = re.search(".*", "//info/packs")
        output = b"".join(get_info_packs(self._req, backend, mat))
        expected = b"".join(
            [(b"P pack-" + s + b".pack\n") for s in [b"1" * 40, b"2" * 40, b"3" * 40]]
        )
        self.assertEqual(expected, output)
        self.assertEqual(HTTP_OK, self._status)
        self.assertContentTypeEquals("text/plain")
        self.assertFalse(self._req.cached)


class SmartHandlersTestCase(WebTestCase):
    class _TestUploadPackHandler:
        def __init__(
            self,
            backend,
            args,
            proto,
            stateless_rpc=None,
            advertise_refs=False,
        ) -> None:
            self.args = args
            self.proto = proto
            self.stateless_rpc = stateless_rpc
            self.advertise_refs = advertise_refs

        def handle(self) -> None:
            self.proto.write(b"handled input: " + self.proto.recv(1024))

    def _make_handler(self, *args, **kwargs):
        self._handler = self._TestUploadPackHandler(*args, **kwargs)
        return self._handler

    def _handlers(self):
        return {b"git-upload-pack": self._make_handler}

    def test_handle_service_request_unknown(self) -> None:
        mat = re.search(".*", "/git-evil-handler")
        content = list(handle_service_request(self._req, "backend", mat))
        self.assertEqual(HTTP_FORBIDDEN, self._status)
        self.assertNotIn(b"git-evil-handler", b"".join(content))
        self.assertFalse(self._req.cached)

    def _run_handle_service_request(self, content_length=None) -> None:
        self._environ["wsgi.input"] = BytesIO(b"foo")
        if content_length is not None:
            self._environ["CONTENT_LENGTH"] = content_length
        mat = re.search(".*", "/git-upload-pack")

        class Backend:
            def open_repository(self, path) -> None:
                return None

        handler_output = b"".join(handle_service_request(self._req, Backend(), mat))
        write_output = self._output.getvalue()
        # Ensure all output was written via the write callback.
        self.assertEqual(b"", handler_output)
        self.assertEqual(b"handled input: foo", write_output)
        self.assertContentTypeEquals("application/x-git-upload-pack-result")
        self.assertFalse(self._handler.advertise_refs)
        self.assertTrue(self._handler.stateless_rpc)
        self.assertFalse(self._req.cached)

    def test_handle_service_request(self) -> None:
        self._run_handle_service_request()

    def test_handle_service_request_with_length(self) -> None:
        self._run_handle_service_request(content_length="3")

    def test_handle_service_request_empty_length(self) -> None:
        self._run_handle_service_request(content_length="")

    def test_get_info_refs_unknown(self) -> None:
        self._environ["QUERY_STRING"] = "service=git-evil-handler"

        class Backend:
            def open_repository(self, url) -> None:
                return None

        mat = re.search(".*", "/git-evil-pack")
        content = list(get_info_refs(self._req, Backend(), mat))
        self.assertNotIn(b"git-evil-handler", b"".join(content))
        self.assertEqual(HTTP_FORBIDDEN, self._status)
        self.assertFalse(self._req.cached)

    def test_get_info_refs(self) -> None:
        self._environ["wsgi.input"] = BytesIO(b"foo")
        self._environ["QUERY_STRING"] = "service=git-upload-pack"

        class Backend:
            def open_repository(self, url) -> None:
                return None

        mat = re.search(".*", "/git-upload-pack")
        handler_output = b"".join(get_info_refs(self._req, Backend(), mat))
        write_output = self._output.getvalue()
        self.assertEqual(
            (
                b"001e# service=git-upload-pack\n"
                b"0000"
                # input is ignored by the handler
                b"handled input: "
            ),
            write_output,
        )
        # Ensure all output was written via the write callback.
        self.assertEqual(b"", handler_output)
        self.assertTrue(self._handler.advertise_refs)
        self.assertTrue(self._handler.stateless_rpc)
        self.assertFalse(self._req.cached)


class LengthLimitedFileTestCase(TestCase):
    def test_no_cutoff(self) -> None:
        f = _LengthLimitedFile(BytesIO(b"foobar"), 1024)
        self.assertEqual(b"foobar", f.read())

    def test_cutoff(self) -> None:
        f = _LengthLimitedFile(BytesIO(b"foobar"), 3)
        self.assertEqual(b"foo", f.read())
        self.assertEqual(b"", f.read())

    def test_multiple_reads(self) -> None:
        f = _LengthLimitedFile(BytesIO(b"foobar"), 3)
        self.assertEqual(b"fo", f.read(2))
        self.assertEqual(b"o", f.read(2))
        self.assertEqual(b"", f.read())


class HTTPGitRequestTestCase(WebTestCase):
    # This class tests the contents of the actual cache headers
    _req_class = HTTPGitRequest

    def test_not_found(self) -> None:
        self._req.cache_forever()  # cache headers should be discarded
        message = "Something not found"
        self.assertEqual(message.encode("ascii"), self._req.not_found(message))
        self.assertEqual(HTTP_NOT_FOUND, self._status)
        self.assertEqual({("Content-Type", "text/plain")}, set(self._headers))

    def test_forbidden(self) -> None:
        self._req.cache_forever()  # cache headers should be discarded
        message = "Something not found"
        self.assertEqual(message.encode("ascii"), self._req.forbidden(message))
        self.assertEqual(HTTP_FORBIDDEN, self._status)
        self.assertEqual({("Content-Type", "text/plain")}, set(self._headers))

    def test_respond_ok(self) -> None:
        self._req.respond()
        self.assertEqual([], self._headers)
        self.assertEqual(HTTP_OK, self._status)

    def test_respond(self) -> None:
        self._req.nocache()
        self._req.respond(
            status=402,
            content_type="some/type",
            headers=[("X-Foo", "foo"), ("X-Bar", "bar")],
        )
        self.assertEqual(
            {
                ("X-Foo", "foo"),
                ("X-Bar", "bar"),
                ("Content-Type", "some/type"),
                ("Expires", "Fri, 01 Jan 1980 00:00:00 GMT"),
                ("Pragma", "no-cache"),
                ("Cache-Control", "no-cache, max-age=0, must-revalidate"),
            },
            set(self._headers),
        )
        self.assertEqual(402, self._status)


class HTTPGitApplicationTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._app = HTTPGitApplication("backend")

        self._environ = {
            "PATH_INFO": "/foo",
            "REQUEST_METHOD": "GET",
        }

    def _test_handler(self, req, backend, mat) -> str:
        # tests interface used by all handlers
        self.assertEqual(self._environ, req.environ)
        self.assertEqual("backend", backend)
        self.assertEqual("/foo", mat.group(0))
        return "output"

    def _add_handler(self, app) -> None:
        req = self._environ["REQUEST_METHOD"]
        app.services = {
            (req, re.compile("/foo$")): self._test_handler,
        }

    def test_call(self) -> None:
        self._add_handler(self._app)
        self.assertEqual("output", self._app(self._environ, None))

    def test_fallback_app(self) -> None:
        def test_app(environ, start_response) -> str:
            return "output"

        app = HTTPGitApplication("backend", fallback_app=test_app)
        self.assertEqual("output", app(self._environ, None))


class GunzipTestCase(HTTPGitApplicationTestCase):
    __doc__ = """TestCase for testing the GunzipFilter, ensuring the wsgi.input
    is correctly decompressed and headers are corrected.
    """
    example_text = __doc__.encode("ascii")

    def setUp(self) -> None:
        super().setUp()
        self._app = GunzipFilter(self._app)
        self._environ["HTTP_CONTENT_ENCODING"] = "gzip"
        self._environ["REQUEST_METHOD"] = "POST"

    def _get_zstream(self, text):
        zstream = BytesIO()
        zfile = gzip.GzipFile(fileobj=zstream, mode="wb")
        zfile.write(text)
        zfile.close()
        zlength = zstream.tell()
        zstream.seek(0)
        return zstream, zlength

    def _test_call(self, orig, zstream, zlength) -> None:
        self._add_handler(self._app.app)
        self.assertLess(zlength, len(orig))
        self.assertEqual(self._environ["HTTP_CONTENT_ENCODING"], "gzip")
        self._environ["CONTENT_LENGTH"] = zlength
        self._environ["wsgi.input"] = zstream
        self._app(self._environ, None)
        buf = self._environ["wsgi.input"]
        self.assertIsNot(buf, zstream)
        buf.seek(0)
        self.assertEqual(orig, buf.read())
        self.assertIs(None, self._environ.get("CONTENT_LENGTH"))
        self.assertNotIn("HTTP_CONTENT_ENCODING", self._environ)

    def test_call(self) -> None:
        self._test_call(self.example_text, *self._get_zstream(self.example_text))

    def test_call_no_seek(self) -> None:
        """This ensures that the gunzipping code doesn't require any methods on
        'wsgi.input' except for '.read()'.  (In particular, it shouldn't
        require '.seek()'. See https://github.com/jelmer/dulwich/issues/140.).
        """
        zstream, zlength = self._get_zstream(self.example_text)
        self._test_call(
            self.example_text,
            MinimalistWSGIInputStream(zstream.read()),
            zlength,
        )

    def test_call_no_working_seek(self) -> None:
        """Similar to 'test_call_no_seek', but this time the methods are available
        (but defunct).  See https://github.com/jonashaag/klaus/issues/154.
        """
        zstream, zlength = self._get_zstream(self.example_text)
        self._test_call(
            self.example_text,
            MinimalistWSGIInputStream2(zstream.read()),
            zlength,
        )
