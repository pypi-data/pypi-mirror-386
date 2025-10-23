# This file is part of lsst-resources.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.

from __future__ import annotations

__all__ = ("HttpReadResourceHandle",)

import io
import logging
import re
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, AnyStr, NamedTuple

import requests

from lsst.utils.timer import time_this

from ._baseResourceHandle import BaseResourceHandle, CloseStatus

if TYPE_CHECKING:
    from ..http import HttpResourcePath


# Prevent circular import by copying this code. Can be removed as soon
# as separate dav implementation is implemented.
def _dav_to_http(url: str) -> str:
    """Convert dav scheme in URL to http scheme."""
    if url.startswith("dav"):
        url = "http" + url.removeprefix("dav")
    return url


class HttpReadResourceHandle(BaseResourceHandle[bytes]):
    """HTTP-based specialization of `.BaseResourceHandle`.

    Parameters
    ----------
    mode : `str`
        Handle modes as described in the python `io` module.
    log : `~logging.Logger`
        Logger to used when writing messages.
    uri : `lsst.resources.http.HttpResourcePath`
        URI of remote resource.
    timeout : `tuple` [`int`, `int`]
        Timeout to use for connections: connection timeout and read timeout
        in a tuple.
    newline : `str` or `None`, optional
        When doing multiline operations, break the stream on given character.
        Defaults to newline. If a file is opened in binary mode, this argument
        is not used, as binary files will only split lines on the binary
        newline representation.
    """

    def __init__(
        self,
        mode: str,
        log: logging.Logger,
        uri: HttpResourcePath,
        *,
        timeout: tuple[float, float] | None = None,
        newline: AnyStr | None = None,
    ) -> None:
        super().__init__(mode, log, uri, newline=newline)
        self._url = uri.geturl()
        self._session = uri.data_session

        if timeout is None:
            raise ValueError("timeout must be specified when constructing this object")
        self._timeout = timeout

        self._completeBuffer: io.BytesIO | None = None

        self._closed = CloseStatus.OPEN
        self._current_position = 0
        self._eof = False
        self._total_size = -1  # Unknown

    def close(self) -> None:
        self._closed = CloseStatus.CLOSED
        self._completeBuffer = None
        self._eof = True

    @property
    def closed(self) -> bool:
        return self._closed == CloseStatus.CLOSED

    def fileno(self) -> int:
        raise io.UnsupportedOperation("HttpReadResourceHandle does not have a file number")

    def flush(self) -> None:
        modes = set(self._mode)
        if {"w", "x", "a", "+"} & modes:
            raise io.UnsupportedOperation("HttpReadResourceHandles are read only")

    @property
    def isatty(self) -> bool | Callable[[], bool]:
        return False

    def readable(self) -> bool:
        return True

    def readline(self, size: int = -1) -> bytes:
        raise io.UnsupportedOperation("HttpReadResourceHandles Do not support line by line reading")

    def readlines(self, size: int = -1) -> Iterable[bytes]:
        raise io.UnsupportedOperation("HttpReadResourceHandles Do not support line by line reading")

    def _size(self) -> int:
        if self._total_size == -1:
            self._total_size = self._uri.size()
        return self._total_size

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        self._eof = False
        if whence == io.SEEK_CUR and (self._current_position + offset) >= 0:
            self._current_position += offset
        elif whence == io.SEEK_SET and offset >= 0:
            self._current_position = offset
        elif whence == io.SEEK_END:
            self._current_position = self._size() + offset
        else:
            raise io.UnsupportedOperation("Seek value is incorrect, or whence mode is unsupported")

        # handle if the complete file has be read already
        if self._completeBuffer is not None:
            self._completeBuffer.seek(self._current_position, whence)
        return self._current_position

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._current_position

    def truncate(self, size: int | None = None) -> int:
        raise io.UnsupportedOperation("HttpReadResourceHandles Do not support truncation")

    def writable(self) -> bool:
        return False

    def write(self, b: bytes, /) -> int:
        raise io.UnsupportedOperation("HttpReadResourceHandles are read only")

    def writelines(self, b: Iterable[bytes], /) -> None:
        raise io.UnsupportedOperation("HttpReadResourceHandles are read only")

    def read(self, size: int = -1) -> bytes:
        if self._eof:
            # At EOF so always return an empty byte string.
            return b""

        # branch for if the complete file has been read before
        if self._completeBuffer is not None:
            result = self._completeBuffer.read(size)
            self._current_position += len(result)
            return result

        if self._completeBuffer is None and size == -1 and self._current_position == 0:
            # The whole file has been requested, read it into a buffer and
            # return the result
            self._completeBuffer = io.BytesIO()
            with time_this(self._log, msg="Read from remote resource %s", args=(self._url,)):
                with self._session as session:
                    resp = session.get(_dav_to_http(self._url), stream=False, timeout=self._timeout)

            if (code := resp.status_code) not in (requests.codes.ok, requests.codes.partial):
                raise FileNotFoundError(f"Unable to read resource {self._url}; status code: {code}")
            self._completeBuffer.write(resp.content)
            self._current_position = self._completeBuffer.tell()

            return self._completeBuffer.getbuffer().tobytes()

        # A partial read is required, either because a size has been specified,
        # or a read has previously been done. Any time we specify a byte range
        # we must disable the gzip compression on the server since we want
        # to address ranges in the uncompressed file. If we send ranges that
        # are interpreted by the server as offsets into the compressed file
        # then that is at least confusing and also there is no guarantee that
        # the bytes can be uncompressed.

        end_pos = self._current_position + (size - 1) if size >= 0 else ""
        headers = {"Range": f"bytes={self._current_position}-{end_pos}", "Accept-Encoding": "identity"}

        with time_this(
            self._log, msg="Read from remote resource %s using headers %s", args=(self._url, headers)
        ):
            with self._session as session:
                resp = session.get(
                    _dav_to_http(self._url), stream=False, timeout=self._timeout, headers=headers
                )

        if resp.status_code == requests.codes.range_not_satisfiable:
            # Must have run off the end of the file. A standard file handle
            # will treat this as EOF so be consistent with that. Do not change
            # the current position.
            self._eof = True
            return b""

        if (code := resp.status_code) not in (requests.codes.ok, requests.codes.partial):
            raise FileNotFoundError(
                f"Unable to read resource {self._url}, or bytes are out of range; status code: {code}"
            )

        # The response header should tell us the total number of bytes
        # in the file and also the current position we have got to in the
        # server.
        if "Content-Range" in resp.headers:
            content_range = parse_content_range_header(resp.headers["Content-Range"])
            if content_range.total is not None:
                # Store in case we need this later.
                self._total_size = content_range.total
            if (
                content_range.total is not None
                and content_range.range_end is not None
                and content_range.range_end >= content_range.total - 1
            ):
                self._eof = True

        # Try to guess that we overran the end. This will not help if we
        # read exactly the number of bytes to get us to the end and so we
        # will need to do one more read and get a 416.
        len_content = len(resp.content)
        if len_content < size:
            self._eof = True

        self._current_position += len_content
        return resp.content


class ContentRange(NamedTuple):
    """Represents the data in an HTTP Content-Range header."""

    range_start: int | None
    """First byte of the zero-indexed, inclusive range returned by this
    response.  `None` if the range was not available in the header.
    """
    range_end: int | None
    """Last byte of the zero-indexed, inclusive range returned by this
    response. `None` if the range was not available in the header.
    """
    total: int | None
    """Total size of the file in bytes. `None` if the file size was not
    available in the header.
    """


def parse_content_range_header(header: str) -> ContentRange:
    """Parse an HTTP 'Content-Range' header.

    Parameters
    ----------
    header : `str`
        Value of an HTTP Content-Range header to be parsed.

    Returns
    -------
    content_range : `ContentRange`
        The byte range included in the response and the total file size.

    Raises
    ------
    ValueError
        If the header was not in the expected format.
    """
    # There are three possible formats for Content-Range. All of them start
    # with optional whitespace and a unit, which for our purposes should always
    # be "bytes".
    prefix = r"^\s*bytes\s+"

    # Content-Range: <unit> <range-start>-<range-end>/<size>
    if (case1 := re.match(prefix + r"(\d+)-(\d+)/(\d+)", header)) is not None:
        return ContentRange(
            range_start=int(case1.group(1)), range_end=int(case1.group(2)), total=int(case1.group(3))
        )

    # Content-Range: <unit> <range-start>-<range-end>/*
    if (case2 := re.match(prefix + r"(\d+)-(\d+)/\*", header)) is not None:
        return ContentRange(range_start=int(case2.group(1)), range_end=int(case2.group(2)), total=None)

    # Content-Range: <unit> */<size>
    if (case3 := re.match(prefix + r"\*/(\d+)", header)) is not None:
        return ContentRange(range_start=None, range_end=None, total=int(case3.group(1)))

    raise ValueError(f"Content-Range header in unexpected format: '{header}'")
