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

__all__ = ("FileResourcePath",)

import contextlib
import copy
import logging
import os
import os.path
import posixpath
import re
import shutil
import stat
import urllib.parse
from collections.abc import Iterator
from typing import IO, TYPE_CHECKING

from ._resourceHandles._fileResourceHandle import FileResourceHandle
from ._resourcePath import ResourcePath
from .utils import NoTransaction, ensure_directory_is_writeable, os2posix, posix2os

try:
    import fsspec
    from fsspec.spec import AbstractFileSystem
except ImportError:
    fsspec = None
    AbstractFileSystem = type

if TYPE_CHECKING:
    from .utils import TransactionProtocol


log = logging.getLogger(__name__)


class FileResourcePath(ResourcePath):
    """Path for explicit ``file`` URI scheme."""

    transferModes = ("copy", "link", "symlink", "hardlink", "relsymlink", "auto", "move")
    transferDefault: str = "link"

    # By definition refers to a local file
    isLocal = True

    @property
    def ospath(self) -> str:
        """Path component of the URI localized to current OS.

        Will unquote URI path since a formal URI must include the quoting.
        """
        return urllib.parse.unquote(posix2os(self._uri.path))

    def exists(self) -> bool:
        """Indicate that the file exists."""
        # Uses os.path.exists so if there is a soft link that points
        # to a file that no longer exists this will return False
        return os.path.exists(self.ospath)

    def size(self) -> int:
        """Return the size of the file in bytes."""
        if not os.path.isdir(self.ospath):
            stat = os.stat(self.ospath)
            sz = stat.st_size
        else:
            sz = 0
        return sz

    def remove(self) -> None:
        """Remove the resource."""
        os.remove(self.ospath)

    @contextlib.contextmanager
    def _as_local(
        self, multithreaded: bool = True, tmpdir: ResourcePath | None = None
    ) -> Iterator[ResourcePath]:
        """Return the local path of the file.

        This is an internal helper for ``as_local()``.

        Parameters
        ----------
        multithreaded : `bool`, optional
            Unused.
        tmpdir : `ResourcePath` or `None`, optional
            Unused.

        Returns
        -------
        local_uri : `ResourcePath`
            A local URI. In this case it will be itself.
        """
        yield self

    def read(self, size: int = -1) -> bytes:
        with open(self.ospath, "rb") as fh:
            return fh.read(size)

    def write(self, data: bytes, overwrite: bool = True) -> None:
        dir = os.path.dirname(self.ospath)
        if not os.path.exists(dir):
            _create_directories(dir)
        mode = "wb" if overwrite else "xb"
        with open(self.ospath, mode) as f:
            f.write(data)

    def mkdir(self) -> None:
        """Make the directory associated with this URI.

        An attempt will be made to create the directory even if the URI
        looks like a file.

        Raises
        ------
        NotADirectoryError:
            Raised if a non-directory already exists.
        """
        try:
            _create_directories(self.ospath)
        except FileExistsError:
            raise NotADirectoryError(f"{self.ospath} exists but is not a directory.") from None

    def isdir(self) -> bool:
        """Return whether this URI is a directory.

        Returns
        -------
        isdir : `bool`
            `True` if this URI is a directory or looks like a directory,
            else `False`.
        """
        if self.dirLike is None:
            # Cache state for next time.
            self.dirLike = os.path.isdir(self.ospath)
        return self.dirLike

    def transfer_from(
        self,
        src: ResourcePath,
        transfer: str,
        overwrite: bool = False,
        transaction: TransactionProtocol | None = None,
        multithreaded: bool = True,
    ) -> None:
        """Transfer the current resource to a local file.

        Parameters
        ----------
        src : `ResourcePath`
            Source URI.
        transfer : `str`
            Mode to use for transferring the resource. Supports the following
            options: copy, link, symlink, hardlink, relsymlink.
        overwrite : `bool`, optional
            Allow an existing file to be overwritten. Defaults to `False`.
        transaction : `~lsst.resources.utils.TransactionProtocol`, optional
            If a transaction is provided, undo actions will be registered.
        multithreaded : `bool`, optional
            Whether threads are allowed to be used or not.
        """
        # Fail early to prevent delays if remote resources are requested
        if transfer not in self.transferModes:
            raise ValueError(f"Transfer mode '{transfer}' not supported by URI scheme {self.scheme}")

        # Existence checks can take time so only try if the log message
        # will be issued.
        if log.isEnabledFor(logging.DEBUG):
            log.debug(
                "Transferring %s [exists: %s] -> %s [exists: %s] (transfer=%s)",
                src,
                src.exists(),
                self,
                self.exists(),
                transfer,
            )

        # The output location should not exist unless overwrite=True.
        # Rather than use `exists()`, use os.stat since we might need
        # the full answer later.
        dest_stat: os.stat_result | None
        try:
            # Do not read through links of the file itself.
            dest_stat = os.lstat(self.ospath)
        except FileNotFoundError:
            dest_stat = None

        # It is possible that the source URI and target URI refer
        # to the same file. This can happen for a number of reasons
        # (such as soft links in the path, or they really are the same).
        # In that case log a message and return as if the transfer
        # completed (it technically did). A temporary file download
        # can't be the same so the test can be skipped.
        if dest_stat and src.isLocal and not src.isTemporary:
            # Be consistent and use lstat here (even though realpath
            # has been called). It does not harm.
            local_src_stat = os.lstat(src.ospath)
            if dest_stat.st_ino == local_src_stat.st_ino and dest_stat.st_dev == local_src_stat.st_dev:
                log.debug(
                    "Destination URI %s is the same file as source URI %s, returning immediately."
                    " No further action required.",
                    self,
                    src,
                )
                return

        if not overwrite and dest_stat:
            raise FileExistsError(
                f"Destination path '{self}' already exists. Transfer from {src} cannot be completed."
            )

        # Make the destination path absolute (but don't follow links since
        # that would possibly cause us to end up in the wrong place if the
        # file existed already as a soft link)
        newFullPath = os.path.abspath(self.ospath)
        outputDir = os.path.dirname(newFullPath)

        # We do not have to special case FileResourcePath here because
        # as_local handles that. If remote download, download it to the
        # destination directory to allow an atomic rename but only if that
        # directory exists because we do not want to create a directory
        # but then end up with the download failing.
        tmpdir = outputDir if os.path.exists(outputDir) else None
        with src.as_local(multithreaded=multithreaded, tmpdir=tmpdir) as local_uri:
            is_temporary = local_uri.isTemporary
            local_src = local_uri.ospath

            # Short circuit if the URIs are identical immediately.
            if self == local_uri:
                log.debug(
                    "Target and destination URIs are identical: %s, returning immediately."
                    " No further action required.",
                    self,
                )
                return

            # Default transfer mode depends on whether we have a temporary
            # file or not.
            if transfer == "auto":
                transfer = self.transferDefault if not is_temporary else "copy"

            if not os.path.exists(local_src):
                if is_temporary:
                    if src == local_uri:
                        msg = f"Local temporary file {src} has gone missing."
                    else:
                        # This will not happen in normal scenarios.
                        msg = f"Local file {local_uri} downloaded from {src} has gone missing"
                else:
                    msg = f"Source URI {src} does not exist"
                raise FileNotFoundError(msg)

            # Follow soft links
            local_src = os.path.realpath(os.path.normpath(local_src))

            # Creating a symlink to a local copy of a remote resource
            # should never work. Creating a hardlink will work but should
            # not be allowed since it is highly unlikely that this is ever
            # an intended option and depends on the local target being
            # on the same file system as was used for the temporary file
            # download.
            # If a symlink is being requested for a local temporary file
            # that is likely undesirable but should not be refused.
            if is_temporary and src != local_uri and "link" in transfer:
                raise RuntimeError(
                    f"Can not use local file system transfer mode {transfer} for remote resource ({src})"
                )
            elif is_temporary and src == local_uri and "symlink" in transfer:
                log.debug(
                    "Using a symlink for a temporary resource may lead to unexpected downstream failures."
                )

            # For temporary files we can own them if we created it.
            requested_transfer = transfer
            if src != local_uri and is_temporary and transfer == "copy":
                transfer = "move"

            if not os.path.isdir(outputDir):
                # Must create the directory -- this can not be rolled back
                # since another transfer running concurrently may
                # be relying on this existing.
                _create_directories(outputDir)

            if transaction is None:
                # Use a no-op transaction to reduce code duplication
                transaction = NoTransaction()

            # For links the OS doesn't let us overwrite so if something does
            # exist we have to remove it before we do the actual "transfer"
            # below
            if "link" in transfer and overwrite and dest_stat:
                with contextlib.suppress(Exception):
                    # If this fails we ignore it since it's a problem
                    # that will manifest immediately below with a more relevant
                    # error message
                    self.remove()

            if transfer == "move":
                # If a rename works we try that since that is guaranteed to
                # be atomic. If that fails we copy and rename. We do this
                # in case other processes are trying to move to the same
                # file and we want the "winner" to not be corrupted.
                try:
                    with transaction.undoWith(f"move from {local_src}", os.rename, newFullPath, local_src):
                        os.rename(local_src, newFullPath)
                except OSError:
                    with self.temporary_uri(prefix=self.parent(), suffix=self.getExtension()) as temp_copy:
                        shutil.copy(local_src, temp_copy.ospath)
                        with transaction.undoWith(
                            f"move from {local_src}",
                            shutil.move,
                            newFullPath,
                            local_src,
                            copy_function=shutil.copy,
                        ):
                            os.rename(temp_copy.ospath, newFullPath)
                    os.remove(local_src)
            elif transfer == "copy":
                # We want atomic copies so first copy to a temp location in
                # the same output directory. This at least guarantees that
                # if multiple processes are writing to the same file
                # simultaneously the file we end up with will not be corrupt.
                if overwrite:
                    with self.temporary_uri(prefix=self.parent(), suffix=self.getExtension()) as temp_copy:
                        shutil.copy(local_src, temp_copy.ospath)
                        with transaction.undoWith(f"copy from {local_src}", os.remove, newFullPath):
                            os.rename(temp_copy.ospath, newFullPath)
                else:
                    # Create the file exclusively to ensure that no others are
                    # trying to write.
                    temp_path = newFullPath + ".transfer-tmp"
                    try:
                        with open(temp_path, "x"):
                            pass
                    except FileExistsError:
                        raise FileExistsError(
                            f"Another process is writing to '{self}'."
                            f" Transfer from {src} cannot be completed."
                        )
                    with transaction.undoWith(f"copy from {local_src}", os.remove, temp_path):
                        # Make sure file is writable, no matter the umask.
                        st = os.stat(temp_path)
                        os.chmod(temp_path, st.st_mode | stat.S_IWUSR)
                        shutil.copy(local_src, temp_path)
                    # Use link/remove to atomically and exclusively move the
                    # file into place (only one concurrent linker can win).
                    try:
                        os.link(temp_path, newFullPath)
                    except FileExistsError:
                        raise FileExistsError(
                            f"Another process wrote to '{self}'. Transfer from {src} cannot be completed."
                        )
                    finally:
                        os.remove(temp_path)
            elif transfer == "link":
                # Try hard link and if that fails use a symlink
                with transaction.undoWith(f"link to {local_src}", os.remove, newFullPath):
                    try:
                        os.link(local_src, newFullPath)
                    except OSError:
                        # Read through existing symlinks
                        os.symlink(local_src, newFullPath)
            elif transfer == "hardlink":
                with transaction.undoWith(f"hardlink to {local_src}", os.remove, newFullPath):
                    os.link(local_src, newFullPath)
            elif transfer == "symlink":
                # Read through existing symlinks
                with transaction.undoWith(f"symlink to {local_src}", os.remove, newFullPath):
                    os.symlink(local_src, newFullPath)
            elif transfer == "relsymlink":
                # This is a standard symlink but using a relative path
                # Need the directory name to give to relative root
                # A full file path confuses it into an extra ../
                newFullPathRoot = os.path.dirname(newFullPath)
                relPath = os.path.relpath(local_src, newFullPathRoot)
                with transaction.undoWith(f"relsymlink to {local_src}", os.remove, newFullPath):
                    os.symlink(relPath, newFullPath)
            else:
                raise NotImplementedError(f"Transfer type '{transfer}' not supported.")

            # This was an explicit move requested from a remote resource
            # try to remove that remote resource. We check is_temporary because
            # the local file would have been moved by shutil.move already.
            if requested_transfer == "move" and is_temporary and src != local_uri:
                # Transactions do not work here
                src.remove()

    def walk(
        self, file_filter: str | re.Pattern | None = None
    ) -> Iterator[list | tuple[ResourcePath, list[str], list[str]]]:
        """Walk the directory tree returning matching files and directories.

        Parameters
        ----------
        file_filter : `str` or `re.Pattern`, optional
            Regex to filter out files from the list before it is returned.

        Yields
        ------
        dirpath : `ResourcePath`
            Current directory being examined.
        dirnames : `list` of `str`
            Names of subdirectories within dirpath.
        filenames : `list` of `str`
            Names of all the files within dirpath.
        """
        if not self.isdir():
            raise ValueError("Can not walk a non-directory URI")

        if isinstance(file_filter, str):
            file_filter = re.compile(file_filter)

        for root, dirs, files in os.walk(self.ospath, followlinks=True):
            # Filter by the regex
            if file_filter is not None:
                files = [f for f in files if file_filter.search(f)]
            yield type(self)(root, forceAbsolute=False, forceDirectory=True), dirs, files

    @classmethod
    def _fixupPathUri(
        cls,
        parsed: urllib.parse.ParseResult,
        root: ResourcePath | None = None,
        forceAbsolute: bool = False,
        forceDirectory: bool | None = None,
    ) -> tuple[urllib.parse.ParseResult, bool | None]:
        """Fix up relative paths in URI instances.

        Parameters
        ----------
        parsed : `~urllib.parse.ParseResult`
            The result from parsing a URI using `urllib.parse`.
        root : `ResourcePath`, optional
            Path to use as root when converting relative to absolute.
            If `None`, it will be the current working directory. It is only
            used if a file-scheme is used incorrectly with a relative path.
        forceAbsolute : `bool`, ignored
            Has no effect for this subclass. ``file`` URIs are always
            absolute.
        forceDirectory : `bool`, optional
            If `True` forces the URI to end with a separator, otherwise given
            URI is interpreted as is.

        Returns
        -------
        modified : `~urllib.parse.ParseResult`
            Update result if a URI is being handled.
        dirLike : `bool` or `None`
            `True` if given parsed URI has a trailing separator or
            ``forceDirectory`` is `True`. Otherwise can return the given
            value of ``forceDirectory``.

        Notes
        -----
        Relative paths are explicitly not supported by RFC8089 but `urllib`
        does accept URIs of the form ``file:relative/path.ext``. They need
        to be turned into absolute paths before they can be used.  This is
        always done regardless of the ``forceAbsolute`` parameter.
        """
        # assume we are not dealing with a directory like URI
        dirLike = forceDirectory

        # file URI implies POSIX path separators so split as POSIX,
        # then join as os, and convert to abspath. Do not handle
        # home directories since "file" scheme is explicitly documented
        # to not do tilde expansion.
        sep = posixpath.sep

        # Consistency check.
        if forceDirectory is False and parsed.path.endswith(sep):
            raise ValueError(
                f"URI {parsed.geturl()} ends with {sep} but "
                "forceDirectory parameter declares it to be a file."
            )

        # For an absolute path all we need to do is check if we need
        # to force the directory separator
        if posixpath.isabs(parsed.path):
            if forceDirectory:
                if not parsed.path.endswith(sep):
                    parsed = parsed._replace(path=parsed.path + sep)
                dirLike = True
            return copy.copy(parsed), dirLike

        # Relative path so must fix it to be compliant with the standard

        # Replacement values for the URI
        replacements = {}

        if root is None:
            root_str = os.path.abspath(os.path.curdir)
        else:
            if root.scheme and root.scheme != "file":
                raise RuntimeError(f"The override root must be a file URI not {root.scheme}")
            root_str = os.path.abspath(root.ospath)

        replacements["path"] = posixpath.normpath(posixpath.join(os2posix(root_str), parsed.path))

        # normpath strips trailing "/" so put it back if necessary
        # Acknowledge that trailing separator exists.
        if forceDirectory or (parsed.path.endswith(sep) and not replacements["path"].endswith(sep)):
            replacements["path"] += sep
            dirLike = True

        # ParseResult is a NamedTuple so _replace is standard API
        parsed = parsed._replace(**replacements)

        if parsed.params or parsed.query:
            log.warning("Additional items unexpectedly encountered in file URI: %s", parsed.geturl())

        return parsed, dirLike

    @contextlib.contextmanager
    def _openImpl(
        self,
        mode: str = "r",
        *,
        encoding: str | None = None,
    ) -> Iterator[IO]:
        with FileResourceHandle(mode=mode, log=log, uri=self, encoding=encoding) as buffer:
            yield buffer  # type: ignore

    def to_fsspec(self) -> tuple[AbstractFileSystem, str]:
        """Return an abstract file system and path that can be used by fsspec.

        Returns
        -------
        fs : `fsspec.spec.AbstractFileSystem`
            A file system object suitable for use with the returned path.
        path : `str`
            A path that can be opened by the file system object.
        """
        if fsspec is None:
            raise ImportError("fsspec is not available")
        # fsspec does not like URL encodings in file URIs so pass it the os
        # path instead.
        return fsspec.url_to_fs(self.ospath)


def _create_directories(name: str | bytes) -> None:
    """Create a directory and all of its parent directories that don't yet
    exist.

    Parameters
    ----------
    name : `str` or `bytes`
        Path to the directory to be created

    Notes
    -----
    The code in this function is duplicated from the Python standard library
    function os.makedirs with one change: if the user has set a process umask
    that prevents us from creating/accessing files in the newly created
    directories, the permissions of the directories are altered to allow
    owner-write and owner-traverse so that they can be used.
    """
    # These are optional parameters in the original function, but they can be
    # constant here.
    mode = 0o777
    exist_ok = True

    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if head and tail and not os.path.exists(head):
        try:
            _create_directories(head)
        except FileExistsError:
            # Defeats race condition when another thread created the path
            pass
        cdir: str | bytes = os.curdir
        if isinstance(tail, bytes):
            cdir = bytes(os.curdir, "ASCII")
        if tail == cdir:  # xxx/newdir/. exists if xxx/newdir exists
            return
    try:
        os.mkdir(name, mode)
        # This is the portion that is modified relative to the standard library
        # version of the function.
        ensure_directory_is_writeable(name)
        # end modified portion
    except OSError:
        # Cannot rely on checking for EEXIST, since the operating system
        # could give priority to other errors like EACCES or EROFS
        if not exist_ok or not os.path.isdir(name):
            raise
