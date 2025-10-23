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

__all__ = ("ResourcePath", "ResourcePathExpression")

import concurrent.futures
import contextlib
import copy
import io
import locale
import logging
import os
import posixpath
import re
import urllib.parse
from collections import defaultdict
from pathlib import Path, PurePath, PurePosixPath
from random import Random
from typing import TypeAlias

try:
    import fsspec
    from fsspec.spec import AbstractFileSystem
except ImportError:
    fsspec = None
    AbstractFileSystem = type

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, overload

from ._resourceHandles._baseResourceHandle import ResourceHandleProtocol
from .utils import _get_num_workers, get_tempdir

if TYPE_CHECKING:
    from .utils import TransactionProtocol


log = logging.getLogger(__name__)

# Regex for looking for URI escapes
ESCAPES_RE = re.compile(r"%[A-F0-9]{2}")

# Precomputed escaped hash
ESCAPED_HASH = urllib.parse.quote("#")


class MBulkResult(NamedTuple):
    """Report on a bulk operation."""

    success: bool
    exception: Exception | None


_EXECUTOR_TYPE: TypeAlias = type[
    concurrent.futures.ThreadPoolExecutor | concurrent.futures.ProcessPoolExecutor
]

# Cache value for executor class so as not to issue warning multiple
# times but still allow tests to override the value.
_POOL_EXECUTOR_CLASS: _EXECUTOR_TYPE | None = None


def _get_executor_class() -> _EXECUTOR_TYPE:
    """Return the executor class used for parallelized execution.

    Returns
    -------
    cls : `concurrent.futures.Executor`
        The ``Executor`` class. Default is
        `concurrent.futures.ThreadPoolExecutor`. Can be set explicitly by
        setting the ``$LSST_RESOURCES_EXECUTOR`` environment variable to
        "thread" or "process". Returns "thread" pool if the value of the
        variable is not recognized.
    """
    global _POOL_EXECUTOR_CLASS

    if _POOL_EXECUTOR_CLASS is not None:
        return _POOL_EXECUTOR_CLASS

    pool_executor_classes = {
        "threads": concurrent.futures.ThreadPoolExecutor,
        "process": concurrent.futures.ProcessPoolExecutor,
    }
    default_executor = "threads"
    external = os.getenv("LSST_RESOURCES_EXECUTOR", default_executor)
    if not external:
        external = default_executor
    if external not in pool_executor_classes:
        log.warning(
            "Unrecognized value of '%s' for LSST_RESOURCES_EXECUTOR env var. Using '%s'",
            external,
            default_executor,
        )
        external = default_executor
    _POOL_EXECUTOR_CLASS = pool_executor_classes[external]
    return _POOL_EXECUTOR_CLASS


@contextlib.contextmanager
def _patch_environ(new_values: dict[str, str]) -> Iterator[None]:
    """Patch os.environ temporarily using the supplied values.

    Parameters
    ----------
    new_values : `dict` [ `str`, `str` ]
        New values to be stored in the environment.
    """
    old_values: dict[str, str] = {}
    for k, v in new_values.items():
        if k in os.environ:
            old_values[k] = os.environ[k]
        os.environ[k] = v

    try:
        yield
    finally:
        for k in new_values:
            del os.environ[k]
            if k in old_values:
                os.environ[k] = old_values[k]


class ResourcePath:  # numpydoc ignore=PR02
    """Convenience wrapper around URI parsers.

    Provides access to URI components and can convert file
    paths into absolute path URIs. Scheme-less URIs are treated as if
    they are local file system paths and are converted to absolute URIs.

    A specialist subclass is created for each supported URI scheme.

    Parameters
    ----------
    uri : `str`, `pathlib.Path`, `urllib.parse.ParseResult`, or `ResourcePath`
        URI in string form.  Can be scheme-less if referring to a relative
        path or an absolute path on the local file system.
    root : `str` or `ResourcePath`, optional
        When fixing up a relative path in a ``file`` scheme or if scheme-less,
        use this as the root. Must be absolute.  If `None` the current
        working directory will be used. Can be any supported URI scheme.
        Not used if ``forceAbsolute`` is `False`.
    forceAbsolute : `bool`, optional
        If `True`, scheme-less relative URI will be converted to an absolute
        path using a ``file`` scheme. If `False` scheme-less URI will remain
        scheme-less and will not be updated to ``file`` or absolute path unless
        it is already an absolute path, in which case it will be updated to
        a ``file`` scheme.
    forceDirectory : `bool` or `None`, optional
        If `True` forces the URI to end with a separator. If `False` the URI
        is interpreted as a file-like entity. Default, `None`, is that the
        given URI is interpreted as a directory if there is a trailing ``/`` or
        for some schemes the system will check to see if it is a file or a
        directory.
    isTemporary : `bool`, optional
        If `True` indicates that this URI points to a temporary resource.
        The default is `False`, unless ``uri`` is already a `ResourcePath`
        instance and ``uri.isTemporary is True``.

    Notes
    -----
    A non-standard URI of the form ``file:dir/file.txt`` is always converted
    to an absolute ``file`` URI.
    """

    _pathLib: type[PurePath] = PurePosixPath
    """Path library to use for this scheme."""

    _pathModule = posixpath
    """Path module to use for this scheme."""

    transferModes: tuple[str, ...] = ("copy", "auto", "move")
    """Transfer modes supported by this implementation.

    Move is special in that it is generally a copy followed by an unlink.
    Whether that unlink works depends critically on whether the source URI
    implements unlink. If it does not the move will be reported as a failure.
    """

    transferDefault: str = "copy"
    """Default mode to use for transferring if ``auto`` is specified."""

    quotePaths = True
    """True if path-like elements modifying a URI should be quoted.

    All non-schemeless URIs have to internally use quoted paths. Therefore
    if a new file name is given (e.g. to updatedFile or join) a decision must
    be made whether to quote it to be consistent.
    """

    isLocal = False
    """If `True` this URI refers to a local file."""

    # This is not an ABC with abstract methods because the __new__ being
    # a factory confuses mypy such that it assumes that every constructor
    # returns a ResourcePath and then determines that all the abstract methods
    # are still abstract. If they are not marked abstract but just raise
    # mypy is fine with it.

    # mypy is confused without these
    _uri: urllib.parse.ParseResult
    isTemporary: bool
    dirLike: bool | None
    """Whether the resource looks like a directory resource. `None` means that
    the status is uncertain."""

    def __new__(
        cls,
        uri: ResourcePathExpression,
        root: str | ResourcePath | None = None,
        forceAbsolute: bool = True,
        forceDirectory: bool | None = None,
        isTemporary: bool | None = None,
    ) -> ResourcePath:
        """Create and return new specialist ResourcePath subclass."""
        parsed: urllib.parse.ParseResult
        dirLike: bool | None = forceDirectory
        subclass: type[ResourcePath] | None = None

        # Force root to be a ResourcePath -- this simplifies downstream
        # code.
        if root is None:
            root_uri = None
        elif isinstance(root, str):
            root_uri = ResourcePath(root, forceDirectory=True, forceAbsolute=True)
        else:
            root_uri = root

        if isinstance(uri, os.PathLike):
            uri = str(uri)

        # Record if we need to post process the URI components
        # or if the instance is already fully configured
        if isinstance(uri, str):
            # Since local file names can have special characters in them
            # we need to quote them for the parser but we can unquote
            # later. Assume that all other URI schemes are quoted.
            # Since sometimes people write file:/a/b and not file:///a/b
            # we should not quote in the explicit case of file:
            if "://" not in uri and not uri.startswith("file:"):
                if ESCAPES_RE.search(uri):
                    log.warning("Possible double encoding of %s", uri)
                else:
                    # Fragments are generally not encoded so we must search
                    # for the fragment boundary ourselves. This is making
                    # an assumption that the filename does not include a "#"
                    # and also that there is no "/" in the fragment itself.
                    to_encode = uri
                    fragment = ""
                    if "#" in uri:
                        dirpos = uri.rfind("/")
                        trailing = uri[dirpos + 1 :]
                        hashpos = trailing.rfind("#")
                        if hashpos != -1:
                            fragment = trailing[hashpos:]
                            to_encode = uri[: dirpos + hashpos + 1]

                    uri = urllib.parse.quote(to_encode) + fragment

            parsed = urllib.parse.urlparse(uri)
        elif isinstance(uri, urllib.parse.ParseResult):
            parsed = copy.copy(uri)
            # If we are being instantiated with a subclass, rather than
            # ResourcePath, ensure that that subclass is used directly.
            # This could lead to inconsistencies if this constructor
            # is used externally outside of the ResourcePath.replace() method.
            #   S3ResourcePath(urllib.parse.urlparse("file://a/b.txt"))
            # will be a problem.
            # This is needed to prevent a schemeless absolute URI become
            # a file URI unexpectedly when calling updatedFile or
            # updatedExtension
            if cls is not ResourcePath:
                parsed, dirLike = cls._fixDirectorySep(parsed, forceDirectory)
                subclass = cls

        elif isinstance(uri, ResourcePath):
            # Since ResourcePath is immutable we can return the argument
            # unchanged if it already agrees with forceDirectory, isTemporary,
            # and forceAbsolute.
            # We invoke __new__ again with str(self) to add a scheme for
            # forceAbsolute, but for the others that seems more likely to paper
            # over logic errors than do something useful, so we just raise.
            if forceDirectory is not None and uri.dirLike is not None and forceDirectory is not uri.dirLike:
                # Can not force a file-like URI to become a dir-like one or
                # vice versa.
                raise RuntimeError(
                    f"{uri} can not be forced to change directory vs file state when previously declared."
                )
            if isTemporary is not None and isTemporary is not uri.isTemporary:
                raise RuntimeError(
                    f"{uri} is already a {'temporary' if uri.isTemporary else 'permanent'} "
                    f"ResourcePath; cannot make it {'temporary' if isTemporary else 'permanent'}."
                )

            if forceAbsolute and not uri.scheme:
                # Create new absolute from relative.
                return ResourcePath(
                    str(uri),
                    root=root,
                    forceAbsolute=forceAbsolute,
                    forceDirectory=forceDirectory or uri.dirLike,
                    isTemporary=uri.isTemporary,
                )
            elif forceDirectory is not None and uri.dirLike is None:
                # Clone but with a new dirLike status.
                return uri.replace(forceDirectory=forceDirectory)
            return uri
        else:
            raise ValueError(
                f"Supplied URI must be string, Path, ResourcePath, or ParseResult but got '{uri!r}'"
            )

        if subclass is None:
            # Work out the subclass from the URI scheme
            if not parsed.scheme:
                # Root may be specified as a ResourcePath that overrides
                # the schemeless determination.
                if (
                    root_uri is not None
                    and root_uri.scheme != "file"  # file scheme has different code path
                    and not parsed.path.startswith("/")  # Not already absolute path
                ):
                    if root_uri.dirLike is False:
                        raise ValueError(
                            f"Root URI ({root}) was not a directory so can not be joined with"
                            f" path {parsed.path!r}"
                        )
                    # If root is temporary or this schemeless is temporary we
                    # assume this URI is temporary.
                    isTemporary = isTemporary or root_uri.isTemporary
                    joined = root_uri.join(
                        parsed.path, forceDirectory=forceDirectory, isTemporary=isTemporary
                    )

                    # Rather than returning this new ResourcePath directly we
                    # instead extract the path and the scheme and adjust the
                    # URI we were given -- we need to do this to preserve
                    # fragments since join() will drop them.
                    parsed = parsed._replace(scheme=joined.scheme, path=joined.path, netloc=joined.netloc)
                    subclass = type(joined)

                    # Clear the root parameter to indicate that it has
                    # been applied already.
                    root_uri = None
                else:
                    from .schemeless import SchemelessResourcePath

                    subclass = SchemelessResourcePath
            elif parsed.scheme == "file":
                from .file import FileResourcePath

                subclass = FileResourcePath
            elif parsed.scheme == "s3":
                from .s3 import S3ResourcePath

                subclass = S3ResourcePath
            elif parsed.scheme.startswith("http"):
                from .http import HttpResourcePath

                subclass = HttpResourcePath
            elif parsed.scheme in {"dav", "davs"}:
                from .dav import DavResourcePath

                subclass = DavResourcePath
            elif parsed.scheme == "gs":
                from .gs import GSResourcePath

                subclass = GSResourcePath
            elif parsed.scheme == "resource":
                # Rules for scheme names disallow pkg_resource
                from .packageresource import PackageResourcePath

                subclass = PackageResourcePath
            elif parsed.scheme == "mem":
                # in-memory datastore object
                from .mem import InMemoryResourcePath

                subclass = InMemoryResourcePath
            else:
                raise NotImplementedError(
                    f"No URI support for scheme: '{parsed.scheme}' in {parsed.geturl()}"
                )

            parsed, dirLike = subclass._fixupPathUri(
                parsed, root=root_uri, forceAbsolute=forceAbsolute, forceDirectory=forceDirectory
            )

            # It is possible for the class to change from schemeless
            # to file so handle that
            if parsed.scheme == "file":
                from .file import FileResourcePath

                subclass = FileResourcePath

        # Now create an instance of the correct subclass and set the
        # attributes directly
        self = object.__new__(subclass)
        self._uri = parsed
        self.dirLike = dirLike
        if isTemporary is None:
            isTemporary = False
        self.isTemporary = isTemporary
        return self

    @property
    def scheme(self) -> str:
        """Return the URI scheme.

        Notes
        -----
        (``://`` is not part of the scheme).
        """
        return self._uri.scheme

    @property
    def netloc(self) -> str:
        """Return the URI network location."""
        return self._uri.netloc

    @property
    def path(self) -> str:
        """Return the path component of the URI."""
        return self._uri.path

    @property
    def unquoted_path(self) -> str:
        """Return path component of the URI with any URI quoting reversed."""
        return urllib.parse.unquote(self._uri.path)

    @property
    def ospath(self) -> str:
        """Return the path component of the URI localized to current OS."""
        raise AttributeError(f"Non-file URI ({self}) has no local OS path.")

    @property
    def relativeToPathRoot(self) -> str:
        """Return path relative to network location.

        This is the path property with posix separator stripped
        from the left hand side of the path.

        Always unquotes.
        """
        relToRoot = self.path.lstrip("/")
        if relToRoot == "":
            return "./"
        return urllib.parse.unquote(relToRoot)

    @property
    def is_root(self) -> bool:
        """Return whether this URI points to the root of the network location.

        This means that the path components refers to the top level.
        """
        relpath = self.relativeToPathRoot
        if relpath == "./":
            return True
        return False

    @property
    def fragment(self) -> str:
        """Return the fragment component of the URI. May be quoted."""
        return self._uri.fragment

    @property
    def unquoted_fragment(self) -> str:
        """Return unquoted fragment."""
        return urllib.parse.unquote(self.fragment)

    @property
    def params(self) -> str:
        """Return any parameters included in the URI."""
        return self._uri.params

    @property
    def query(self) -> str:
        """Return any query strings included in the URI."""
        return self._uri.query

    def geturl(self) -> str:
        """Return the URI in string form.

        Returns
        -------
        url : `str`
            String form of URI.
        """
        return self._uri.geturl()

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
        # By default give the URL to fsspec and hope.
        return fsspec.url_to_fs(self.geturl())

    def root_uri(self) -> ResourcePath:
        """Return the base root URI.

        Returns
        -------
        uri : `ResourcePath`
            Root URI.
        """
        return self.replace(path="", query="", fragment="", params="", forceDirectory=True)

    def split(self) -> tuple[ResourcePath, str]:
        """Split URI into head and tail.

        Returns
        -------
        head: `ResourcePath`
            Everything leading up to tail, expanded and normalized as per
            ResourcePath rules.
        tail : `str`
            Last path component. Tail will be empty if path ends on a
            separator or if the URI is known to be associated with a directory.
            Tail will never contain separators. It will be unquoted.

        Notes
        -----
        Equivalent to `os.path.split` where head preserves the URI
        components. In some cases this method can result in a file system
        check to verify whether the URI is a directory or not (only if
        ``forceDirectory`` was `None` during construction). For a scheme-less
        URI this can mean that the result might change depending on current
        working directory.
        """
        if self.isdir():
            # This is known to be a directory so must return itself and
            # the empty string.
            return self, ""

        head, tail = self._pathModule.split(self.path)
        headuri = self._uri._replace(path=head, fragment="", query="", params="")

        # The file part should never include quoted metacharacters
        tail = urllib.parse.unquote(tail)

        # Schemeless is special in that it can be a relative path.
        # We need to ensure that it stays that way. All other URIs will
        # be absolute already.
        forceAbsolute = self.isabs()
        return ResourcePath(headuri, forceDirectory=True, forceAbsolute=forceAbsolute), tail

    def basename(self) -> str:
        """Return the base name, last element of path, of the URI.

        Returns
        -------
        tail : `str`
            Last part of the path attribute. Trail will be empty if path ends
            on a separator.

        Notes
        -----
        If URI ends on a slash returns an empty string. This is the second
        element returned by `split()`.

        Equivalent of `os.path.basename`.
        """
        return self.split()[1]

    def dirname(self) -> ResourcePath:
        """Return the directory component of the path as a new `ResourcePath`.

        Returns
        -------
        head : `ResourcePath`
            Everything except the tail of path attribute, expanded and
            normalized as per ResourcePath rules.

        Notes
        -----
        Equivalent of `os.path.dirname`. If this is a directory URI it will
        be returned unchanged. If the parent directory is always required
        use `parent`.
        """
        return self.split()[0]

    def parent(self) -> ResourcePath:
        """Return a `ResourcePath` of the parent directory.

        Returns
        -------
        head : `ResourcePath`
            Everything except the tail of path attribute, expanded and
            normalized as per `ResourcePath` rules.

        Notes
        -----
        For a file-like URI this will be the same as calling `dirname`.
        For a directory-like URI this will always return the parent directory
        whereas `dirname()` will return the original URI. This is consistent
        with `os.path.dirname` compared to the `pathlib.Path` property
        ``parent``.
        """
        if self.dirLike is False:
            # os.path.split() is slightly faster than calling Path().parent.
            return self.dirname()
        # When self is dir-like, returns its parent directory,
        # regardless of the presence of a trailing separator
        originalPath = self._pathLib(self.path)
        parentPath = originalPath.parent
        return self.replace(path=str(parentPath), forceDirectory=True, fragment="", query="", params="")

    def replace(
        self, forceDirectory: bool | None = None, isTemporary: bool = False, **kwargs: Any
    ) -> ResourcePath:
        """Return new `ResourcePath` with specified components replaced.

        Parameters
        ----------
        forceDirectory : `bool` or `None`, optional
            Parameter passed to ResourcePath constructor to force this
            new URI to be dir-like or file-like.
        isTemporary : `bool`, optional
            Indicate that the resulting URI is temporary resource.
        **kwargs
            Components of a `urllib.parse.ParseResult` that should be
            modified for the newly-created `ResourcePath`.

        Returns
        -------
        new : `ResourcePath`
            New `ResourcePath` object with updated values.

        Notes
        -----
        Does not, for now, allow a change in URI scheme.
        """
        # Disallow a change in scheme
        if "scheme" in kwargs:
            raise ValueError(f"Can not use replace() method to change URI scheme for {self}")
        result = self.__class__(
            self._uri._replace(**kwargs), forceDirectory=forceDirectory, isTemporary=isTemporary
        )
        result._copy_extra_attributes(self)
        return result

    def updatedFile(self, newfile: str) -> ResourcePath:
        """Return new URI with an updated final component of the path.

        Parameters
        ----------
        newfile : `str`
            File name with no path component.

        Returns
        -------
        updated : `ResourcePath`
            Updated `ResourcePath` with new updated final component.

        Notes
        -----
        Forces the ``ResourcePath.dirLike`` attribute to be false. The new file
        path will be quoted if necessary. If the current URI is known to
        refer to a directory, the new file will be joined to the current file.
        It is recommended that this behavior no longer be used and a call
        to `isdir` by the caller should be used to decide whether to join or
        replace. In the future this method may be modified to always replace
        the final element of the path.
        """
        if self.dirLike:
            return self.join(newfile, forceDirectory=False)
        return self.parent().join(newfile, forceDirectory=False)

    def updatedExtension(self, ext: str | None) -> ResourcePath:
        """Return a new `ResourcePath` with updated file extension.

        All file extensions are replaced.

        Parameters
        ----------
        ext : `str` or `None`
            New extension. If an empty string is given any extension will
            be removed. If `None` is given there will be no change.

        Returns
        -------
        updated : `ResourcePath`
            URI with the specified extension. Can return itself if
            no extension was specified.
        """
        if ext is None:
            return self

        # Get the extension
        current = self.getExtension()

        # Nothing to do if the extension already matches
        if current == ext:
            return self

        # Remove the current extension from the path
        # .fits.gz counts as one extension do not use os.path.splitext
        path = self.path
        if current:
            path = path.removesuffix(current)

        # Ensure that we have a leading "." on file extension (and we do not
        # try to modify the empty string)
        if ext and not ext.startswith("."):
            ext = "." + ext

        return self.replace(path=path + ext, forceDirectory=False)

    def getExtension(self) -> str:
        """Return the extension(s) associated with this URI path.

        Returns
        -------
        ext : `str`
            The file extension (including the ``.``). Can be empty string
            if there is no file extension. Usually returns only the last
            file extension unless there is a special extension modifier
            indicating file compression, in which case the combined
            extension (e.g. ``.fits.gz``) will be returned.

        Notes
        -----
        Does not distinguish between file and directory URIs when determining
        a suffix. An extension is only determined from the final component
        of the path.
        """
        special = {".gz", ".bz2", ".xz", ".fz"}

        # path lib will ignore any "." in directories.
        # path lib works well:
        # extensions = self._pathLib(self.path).suffixes
        # But the constructor is slow. Therefore write our own implementation.
        # Strip trailing separator if present, do not care if this is a
        # directory or not.
        parts = self.path.rstrip("/").rsplit(self._pathModule.sep, 1)
        _, *extensions = parts[-1].split(".")

        if not extensions:
            return ""
        extensions = ["." + x for x in extensions]

        ext = extensions.pop()

        # Multiple extensions, decide whether to include the final two
        if extensions and ext in special:
            ext = f"{extensions[-1]}{ext}"

        return ext

    def join(
        self, path: str | ResourcePath, isTemporary: bool | None = None, forceDirectory: bool | None = None
    ) -> ResourcePath:
        """Return new `ResourcePath` with additional path components.

        Parameters
        ----------
        path : `str`, `ResourcePath`
            Additional file components to append to the current URI. Will be
            quoted depending on the associated URI scheme. If the path looks
            like a URI referring to an absolute location, it will be returned
            directly (matching the behavior of `os.path.join`). It can
            also be a `ResourcePath`. Fragments are propagated.
        isTemporary : `bool`, optional
            Indicate that the resulting URI represents a temporary resource.
            Default is ``self.isTemporary``.
        forceDirectory : `bool` or `None`, optional
            If `True` forces the URI to end with a separator. If `False` the
            resultant URI is declared to refer to a file. `None` indicates
            that the file directory status is unknown.

        Returns
        -------
        new : `ResourcePath`
            New URI with the path appended.

        Notes
        -----
        Schemeless URIs assume local path separator but all other URIs assume
        POSIX separator if the supplied path has directory structure. It
        may be this never becomes a problem but datastore templates assume
        POSIX separator is being used.

        If an absolute `ResourcePath` is given for ``path`` is is assumed that
        this should be returned directly. Giving a ``path`` of an absolute
        scheme-less URI is not allowed for safety reasons as it may indicate
        a mistake in the calling code.

        It is an error to attempt to join to something that is known to
        refer to a file. Use `updatedFile` if the file is to be
        replaced.

        If an unquoted ``#`` is included in the path it is assumed to be
        referring to a fragment and not part of the file name.

        Raises
        ------
        ValueError
            Raised if the given path object refers to a directory but the
            ``forceDirectory`` parameter insists the outcome should be a file,
            and vice versa. Also raised if the URI being joined with is known
            to refer to a file.
        RuntimeError
            Raised if this attempts to join a temporary URI to a non-temporary
            URI.
        """
        if self.dirLike is False:
            raise ValueError("Can not join a new path component to a file.")
        if isTemporary is None:
            isTemporary = self.isTemporary
        elif not isTemporary and self.isTemporary:
            raise RuntimeError("Cannot join temporary URI to non-temporary URI.")
        # If we have a full URI in path we will use it directly
        # but without forcing to absolute so that we can trap the
        # expected option of relative path.
        path_uri = ResourcePath(
            path, forceAbsolute=False, forceDirectory=forceDirectory, isTemporary=isTemporary
        )
        if forceDirectory is not None and path_uri.dirLike is not forceDirectory:
            raise ValueError(
                "The supplied path URI to join has inconsistent directory state "
                f"with forceDirectory parameter: {path_uri.dirLike} vs {forceDirectory}"
            )
        forceDirectory = path_uri.dirLike

        if path_uri.isabs():
            # Absolute URI so return it directly.
            return path_uri

        # We want to propagate fragments to the joined path and we rely on
        # the ResourcePath parser to find these fragments for us even in plain
        # strings. Must assume there are no `#` characters in filenames.
        if not isinstance(path, str) or path_uri.fragment:
            path = path_uri.unquoted_path

        # Might need to quote the path.
        if self.quotePaths:
            path = urllib.parse.quote(path)

        newpath = self._pathModule.normpath(self._pathModule.join(self.path, path))

        # normpath can strip trailing / so we force directory if the supplied
        # path ended with a /
        has_dir_sep = path.endswith(self._pathModule.sep)
        if forceDirectory is None and has_dir_sep:
            forceDirectory = True
        elif forceDirectory is False and has_dir_sep:
            raise ValueError("Path to join has trailing / but is being forced to be a file.")
        return self.replace(
            path=newpath,
            forceDirectory=forceDirectory,
            isTemporary=isTemporary,
            fragment=path_uri.fragment,
            query=path_uri.query,
            params=path_uri.params,
        )

    def relative_to(self, other: ResourcePath) -> str | None:
        """Return the relative path from this URI to the other URI.

        Parameters
        ----------
        other : `ResourcePath`
            URI to use to calculate the relative path. Must be a parent
            of this URI.

        Returns
        -------
        subpath : `str`
            The sub path of this URI relative to the supplied other URI.
            Returns `None` if there is no parent child relationship.
            Scheme and netloc must match.
        """
        # Scheme-less self is handled elsewhere.
        if self.scheme != other.scheme:
            return None
        if self.netloc != other.netloc:
            # Special case for localhost vs empty string.
            # There can be many variants of localhost.
            local_netlocs = {"", "localhost", "localhost.localdomain", "127.0.0.1"}
            if not {self.netloc, other.netloc}.issubset(local_netlocs):
                return None

        enclosed_path = self._pathLib(self.relativeToPathRoot)
        parent_path = other.relativeToPathRoot
        subpath: str | None
        try:
            subpath = str(enclosed_path.relative_to(parent_path))
        except ValueError:
            subpath = None
        else:
            subpath = urllib.parse.unquote(subpath)
        return subpath

    def exists(self) -> bool:
        """Indicate that the resource is available.

        Returns
        -------
        exists : `bool`
            `True` if the resource exists.
        """
        raise NotImplementedError()

    @classmethod
    def _group_uris(cls, uris: Iterable[ResourcePath]) -> dict[type[ResourcePath], list[ResourcePath]]:
        """Group URIs by class/scheme."""
        grouped: dict[type, list[ResourcePath]] = defaultdict(list)
        for uri in uris:
            grouped[uri.__class__].append(uri)
        return grouped

    @classmethod
    def mexists(
        cls, uris: Iterable[ResourcePath], *, num_workers: int | None = None
    ) -> dict[ResourcePath, bool]:
        """Check for existence of multiple URIs at once.

        Parameters
        ----------
        uris : iterable of `ResourcePath`
            The URIs to test.
        num_workers : `int` or `None`, optional
            The number of parallel workers to use when checking for existence
            If `None`, the default value will be taken from the environment.
            If this number is higher than the default and a thread pool is
            used, there may not be enough cached connections available.

        Returns
        -------
        existence : `dict` of [`ResourcePath`, `bool`]
            Mapping of original URI to boolean indicating existence.
        """
        existence: dict[ResourcePath, bool] = {}
        for uri_class, group in cls._group_uris(uris).items():
            existence.update(uri_class._mexists(group, num_workers=num_workers))

        return existence

    @classmethod
    def _mexists(
        cls, uris: Iterable[ResourcePath], *, num_workers: int | None = None
    ) -> dict[ResourcePath, bool]:
        """Check for existence of multiple URIs at once.

        Implementation helper method for `mexists`.


        Parameters
        ----------
        uris : iterable of `ResourcePath`
            The URIs to test.
        num_workers : `int` or `None`, optional
            The number of parallel workers to use when checking for existence
            If `None`, the default value will be taken from the environment.

        Returns
        -------
        existence : `dict` of [`ResourcePath`, `bool`]
            Mapping of original URI to boolean indicating existence.
        """
        pool_executor_class = _get_executor_class()
        if issubclass(pool_executor_class, concurrent.futures.ProcessPoolExecutor):
            # Patch the environment to make it think there is only one worker
            # for each subprocess.
            with _patch_environ({"LSST_RESOURCES_NUM_WORKERS": "1"}):
                return cls._mexists_pool(pool_executor_class, uris)
        else:
            return cls._mexists_pool(pool_executor_class, uris, num_workers=num_workers)

    @classmethod
    def _mexists_pool(
        cls,
        pool_executor_class: _EXECUTOR_TYPE,
        uris: Iterable[ResourcePath],
        *,
        num_workers: int | None = None,
    ) -> dict[ResourcePath, bool]:
        """Check for existence of multiple URIs at once using specified pool
        executor.

        Implementation helper method for `_mexists`.

        Parameters
        ----------
        pool_executor_class : `type` [ `concurrent.futures.Executor` ]
            Type of executor pool to use.
        uris : iterable of `ResourcePath`
            The URIs to test.
        num_workers : `int` or `None`, optional
            The number of parallel workers to use when checking for existence
            If `None`, the default value will be taken from the environment.

        Returns
        -------
        existence : `dict` of [`ResourcePath`, `bool`]
            Mapping of original URI to boolean indicating existence.
        """
        max_workers = num_workers if num_workers is not None else _get_num_workers()
        with pool_executor_class(max_workers=max_workers) as exists_executor:
            future_exists = {exists_executor.submit(uri.exists): uri for uri in uris}

            results: dict[ResourcePath, bool] = {}
            for future in concurrent.futures.as_completed(future_exists):
                uri = future_exists[future]
                try:
                    exists = future.result()
                except Exception:
                    exists = False
                results[uri] = exists
        return results

    @classmethod
    def mtransfer(
        cls,
        transfer: str,
        from_to: Iterable[tuple[ResourcePath, ResourcePath]],
        overwrite: bool = False,
        transaction: TransactionProtocol | None = None,
        do_raise: bool = True,
    ) -> dict[ResourcePath, MBulkResult]:
        """Transfer many files in bulk.

        Parameters
        ----------
        transfer : `str`
            Mode to use for transferring the resource. Generically there are
            many standard options: copy, link, symlink, hardlink, relsymlink.
            Not all URIs support all modes.
        from_to : `list` [ `tuple` [ `ResourcePath`, `ResourcePath` ] ]
            A sequence of the source URIs and the target URIs.
        overwrite : `bool`, optional
            Allow an existing file to be overwritten. Defaults to `False`.
        transaction : `~lsst.resources.utils.TransactionProtocol`, optional
            A transaction object that can (depending on implementation)
            rollback transfers on error.  Not guaranteed to be implemented.
            The transaction object must be thread safe.
        do_raise : `bool`, optional
            If `True` an `ExceptionGroup` will be raised containing any
            exceptions raised by the individual transfers. If `False`, or if
            there were no exceptions, a dict reporting the status of each
            `ResourcePath` will be returned.

        Returns
        -------
        copy_status : `dict` [ `ResourcePath`, `MBulkResult` ]
            A dict of all the transfer attempts with a value indicating
            whether the transfer succeeded for the target URI. If ``do_raise``
            is `True`, this will only be returned if there are no errors.
        """
        pool_executor_class = _get_executor_class()
        if issubclass(pool_executor_class, concurrent.futures.ProcessPoolExecutor):
            # Patch the environment to make it think there is only one worker
            # for each subprocess.
            with _patch_environ({"LSST_RESOURCES_NUM_WORKERS": "1"}):
                return cls._mtransfer(
                    pool_executor_class,
                    transfer,
                    from_to,
                    overwrite=overwrite,
                    transaction=transaction,
                    do_raise=do_raise,
                )
        return cls._mtransfer(
            pool_executor_class,
            transfer,
            from_to,
            overwrite=overwrite,
            transaction=transaction,
            do_raise=do_raise,
        )

    @classmethod
    def _mtransfer(
        cls,
        pool_executor_class: _EXECUTOR_TYPE,
        transfer: str,
        from_to: Iterable[tuple[ResourcePath, ResourcePath]],
        overwrite: bool = False,
        transaction: TransactionProtocol | None = None,
        do_raise: bool = True,
    ) -> dict[ResourcePath, MBulkResult]:
        """Transfer many files in bulk.

        Parameters
        ----------
        transfer : `str`
            Mode to use for transferring the resource. Generically there are
            many standard options: copy, link, symlink, hardlink, relsymlink.
            Not all URIs support all modes.
        from_to : `list` [ `tuple` [ `ResourcePath`, `ResourcePath` ] ]
            A sequence of the source URIs and the target URIs.
        overwrite : `bool`, optional
            Allow an existing file to be overwritten. Defaults to `False`.
        transaction : `~lsst.resources.utils.TransactionProtocol`, optional
            A transaction object that can (depending on implementation)
            rollback transfers on error.  Not guaranteed to be implemented.
            The transaction object must be thread safe.
        do_raise : `bool`, optional
            If `True` an `ExceptionGroup` will be raised containing any
            exceptions raised by the individual transfers. Else a dict
            reporting the status of each `ResourcePath` will be returned.

        Returns
        -------
        copy_status : `dict` [ `ResourcePath`, `MBulkResult` ]
            A dict of all the transfer attempts with a value indicating
            whether the transfer succeeded for the target URI.
        """
        with pool_executor_class(max_workers=_get_num_workers()) as transfer_executor:
            future_transfers = {
                transfer_executor.submit(
                    to_uri.transfer_from,
                    from_uri,
                    transfer=transfer,
                    overwrite=overwrite,
                    transaction=transaction,
                    multithreaded=False,
                ): to_uri
                for from_uri, to_uri in from_to
            }
            results: dict[ResourcePath, MBulkResult] = {}
            failed = False
            for future in concurrent.futures.as_completed(future_transfers):
                to_uri = future_transfers[future]
                try:
                    future.result()
                except Exception as e:
                    transferred = MBulkResult(False, e)
                    failed = True
                else:
                    transferred = MBulkResult(True, None)
                results[to_uri] = transferred

        if do_raise and failed:
            raise ExceptionGroup(
                f"Errors transferring {len(results)} artifacts",
                tuple(res.exception for res in results.values() if res.exception is not None),
            )

        return results

    def remove(self) -> None:
        """Remove the resource."""
        raise NotImplementedError()

    @classmethod
    def mremove(
        cls, uris: Iterable[ResourcePath], *, do_raise: bool = True
    ) -> dict[ResourcePath, MBulkResult]:
        """Remove multiple URIs at once.

        Parameters
        ----------
        uris : iterable of `ResourcePath`
            URIs to remove.
        do_raise : `bool`, optional
            If `True` an `ExceptionGroup` will be raised containing any
            exceptions raised by the individual transfers. If `False`, or if
            there were no exceptions, a dict reporting the status of each
            `ResourcePath` will be returned.

        Returns
        -------
        results : `dict` [ `ResourcePath`, `MBulkResult` ]
            Dictionary mapping each URI to a result object indicating whether
            the removal succeeded or resulted in an exception. If ``do_raise``
            is `True` this will only be returned if everything succeeded.
        """
        # Group URIs by scheme since some URI schemes support native bulk
        # APIs.
        results: dict[ResourcePath, MBulkResult] = {}
        for uri_class, group in cls._group_uris(uris).items():
            results.update(uri_class._mremove(group))
        if do_raise:
            failed = any(not r.success for r in results.values())
            if failed:
                s = "s" if len(results) != 1 else ""
                raise ExceptionGroup(
                    f"Error{s} removing {len(results)} artifact{s}",
                    tuple(res.exception for res in results.values() if res.exception is not None),
                )

        return results

    @classmethod
    def _mremove(cls, uris: Iterable[ResourcePath]) -> dict[ResourcePath, MBulkResult]:
        """Remove multiple URIs using futures."""
        pool_executor_class = _get_executor_class()
        if issubclass(pool_executor_class, concurrent.futures.ProcessPoolExecutor):
            # Patch the environment to make it think there is only one worker
            # for each subprocess.
            with _patch_environ({"LSST_RESOURCES_NUM_WORKERS": "1"}):
                return cls._mremove_pool(pool_executor_class, uris)
        else:
            return cls._mremove_pool(pool_executor_class, uris)

    @classmethod
    def _mremove_pool(
        cls,
        pool_executor_class: _EXECUTOR_TYPE,
        uris: Iterable[ResourcePath],
        *,
        num_workers: int | None = None,
    ) -> dict[ResourcePath, MBulkResult]:
        """Remove URIs using a futures pool."""
        max_workers = num_workers if num_workers is not None else _get_num_workers()
        results: dict[ResourcePath, MBulkResult] = {}
        with pool_executor_class(max_workers=max_workers) as remove_executor:
            future_remove = {remove_executor.submit(uri.remove): uri for uri in uris}
            for future in concurrent.futures.as_completed(future_remove):
                try:
                    future.result()
                except Exception as e:
                    removed = MBulkResult(False, e)
                else:
                    removed = MBulkResult(True, None)
                uri = future_remove[future]
                results[uri] = removed
        return results

    def isabs(self) -> bool:
        """Indicate that the resource is fully specified.

        For non-schemeless URIs this is always true.

        Returns
        -------
        isabs : `bool`
            `True` in all cases except schemeless URI.
        """
        return True

    def abspath(self) -> ResourcePath:
        """Return URI using an absolute path.

        Returns
        -------
        abs : `ResourcePath`
            Absolute URI. For non-schemeless URIs this always returns itself.
            Schemeless URIs are upgraded to file URIs.
        """
        return self

    @contextlib.contextmanager
    def _as_local(
        self, multithreaded: bool = True, tmpdir: ResourcePath | None = None
    ) -> Iterator[ResourcePath]:
        """Return the location of the (possibly remote) resource as local file.

        This is a helper function for `as_local` context manager.

        Parameters
        ----------
        multithreaded : `bool`, optional
            If `True` the transfer will be allowed to attempt to improve
            throughput by using parallel download streams. This may of no
            effect if the URI scheme does not support parallel streams or
            if a global override has been applied. If `False` parallel
            streams will be disabled.
        tmpdir : `ResourcePath` or `None`, optional
            Explicit override of the temporary directory to use for remote
            downloads.

        Returns
        -------
        local_uri : `ResourcePath`
            A URI to a local POSIX file. This can either be the same resource
            or a local downloaded copy of the resource.
        """
        raise NotImplementedError()

    @contextlib.contextmanager
    def as_local(
        self, multithreaded: bool = True, tmpdir: ResourcePathExpression | None = None
    ) -> Iterator[ResourcePath]:
        """Return the location of the (possibly remote) resource as local file.

        Parameters
        ----------
        multithreaded : `bool`, optional
            If `True` the transfer will be allowed to attempt to improve
            throughput by using parallel download streams. This may of no
            effect if the URI scheme does not support parallel streams or
            if a global override has been applied. If `False` parallel
            streams will be disabled.
        tmpdir : `lsst.resources.ResourcePathExpression` or `None`, optional
            Explicit override of the temporary directory to use for remote
            downloads. This directory must be a local POSIX directory and
            must exist.

        Yields
        ------
        local : `ResourcePath`
            If this is a remote resource, it will be a copy of the resource
            on the local file system, probably in a temporary directory.
            For a local resource this should be the actual path to the
            resource.

        Notes
        -----
        The context manager will automatically delete any local temporary
        file.

        Examples
        --------
        Should be used as a context manager:

        .. code-block:: py

           with uri.as_local() as local:
               ospath = local.ospath
        """
        if self.isdir():
            raise IsADirectoryError(f"Directory-like URI {self} cannot be fetched as local.")
        temp_dir = ResourcePath(tmpdir, forceDirectory=True) if tmpdir is not None else None
        if temp_dir is not None and not temp_dir.isLocal:
            raise ValueError(f"Temporary directory for as_local must be local resource not {temp_dir}")
        with self._as_local(multithreaded=multithreaded, tmpdir=temp_dir) as local_uri:
            yield local_uri

    @classmethod
    @contextlib.contextmanager
    def temporary_uri(
        cls,
        prefix: ResourcePath | None = None,
        suffix: str | None = None,
        delete: bool = True,
    ) -> Iterator[ResourcePath]:
        """Create a temporary file-like URI.

        Parameters
        ----------
        prefix : `ResourcePath`, optional
            Temporary directory to use (can be any scheme). Without this the
            path will be formed as a local file URI in a temporary directory
            obtained from `lsst.resources.utils.get_tempdir`. Ensuring that the
            prefix location exists is the responsibility of the caller.
        suffix : `str`, optional
            A file suffix to be used. The ``.`` should be included in this
            suffix.
        delete : `bool`, optional
            By default the resource will be deleted when the context manager
            is exited. Setting this flag to `False` will leave the resource
            alone.

        Yields
        ------
        uri : `ResourcePath`
            The temporary URI. Will be removed when the context is completed.
        """
        if prefix is None:
            prefix = ResourcePath(get_tempdir(), forceDirectory=True)

        # Need to create a randomized file name. For consistency do not
        # use mkstemp for local and something else for remote. Additionally
        # this method does not create the file to prevent name clashes.
        characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
        rng = Random()
        tempname = "".join(rng.choice(characters) for _ in range(16))
        if suffix:
            tempname += suffix
        temporary_uri = prefix.join(tempname, isTemporary=True)
        if temporary_uri.isdir():
            # If we had a safe way to clean up a remote temporary directory, we
            # could support this.
            raise NotImplementedError("temporary_uri cannot be used to create a temporary directory.")
        try:
            yield temporary_uri
        finally:
            if delete:
                with contextlib.suppress(FileNotFoundError):
                    # It's okay if this does not work because the user
                    # removed the file.
                    temporary_uri.remove()

    def read(self, size: int = -1) -> bytes:
        """Open the resource and return the contents in bytes.

        Parameters
        ----------
        size : `int`, optional
            The number of bytes to read. Negative or omitted indicates
            that all data should be read.
        """
        raise NotImplementedError()

    def write(self, data: bytes, overwrite: bool = True) -> None:
        """Write the supplied bytes to the new resource.

        Parameters
        ----------
        data : `bytes`
            The bytes to write to the resource. The entire contents of the
            resource will be replaced.
        overwrite : `bool`, optional
            If `True` the resource will be overwritten if it exists. Otherwise
            the write will fail.
        """
        raise NotImplementedError()

    def mkdir(self) -> None:
        """For a dir-like URI, create the directory resource if needed."""
        raise NotImplementedError()

    def isdir(self) -> bool:
        """Return True if this URI looks like a directory, else False."""
        return bool(self.dirLike)

    def size(self) -> int:
        """For non-dir-like URI, return the size of the resource.

        Returns
        -------
        sz : `int`
            The size in bytes of the resource associated with this URI.
            Returns 0 if dir-like.
        """
        raise NotImplementedError()

    def __str__(self) -> str:
        """Convert the URI to its native string form."""
        return self.geturl()

    def __repr__(self) -> str:
        """Return string representation suitable for evaluation."""
        return f'ResourcePath("{self.geturl()}")'

    def __eq__(self, other: Any) -> bool:
        """Compare supplied object with this `ResourcePath`."""
        if not isinstance(other, ResourcePath):
            return NotImplemented
        return self.geturl() == other.geturl()

    def __hash__(self) -> int:
        """Return hash of this object."""
        return hash(str(self))

    def __lt__(self, other: ResourcePath) -> bool:
        return self.geturl() < other.geturl()

    def __le__(self, other: ResourcePath) -> bool:
        return self.geturl() <= other.geturl()

    def __gt__(self, other: ResourcePath) -> bool:
        return self.geturl() > other.geturl()

    def __ge__(self, other: ResourcePath) -> bool:
        return self.geturl() >= other.geturl()

    def __copy__(self) -> ResourcePath:
        """Copy constructor.

        Object is immutable so copy can return itself.
        """
        # Implement here because the __new__ method confuses things
        return self

    def __deepcopy__(self, memo: Any) -> ResourcePath:
        """Deepcopy the object.

        Object is immutable so copy can return itself.
        """
        # Implement here because the __new__ method confuses things
        return self

    def __getnewargs__(self) -> tuple:
        """Support pickling."""
        return (str(self),)

    @classmethod
    def _fixDirectorySep(
        cls, parsed: urllib.parse.ParseResult, forceDirectory: bool | None = None
    ) -> tuple[urllib.parse.ParseResult, bool | None]:
        """Ensure that a path separator is present on directory paths.

        Parameters
        ----------
        parsed : `~urllib.parse.ParseResult`
            The result from parsing a URI using `urllib.parse`.
        forceDirectory : `bool` or `None`, optional
            If `True` forces the URI to end with a separator, otherwise given
            URI is interpreted as is. Specifying that the URI is conceptually
            equivalent to a directory can break some ambiguities when
            interpreting the last element of a path.

        Returns
        -------
        modified : `~urllib.parse.ParseResult`
            Update result if a URI is being handled.
        dirLike : `bool` or `None`
            `True` if given parsed URI has a trailing separator or
            ``forceDirectory`` is `True`. Otherwise returns the given value of
            ``forceDirectory``.
        """
        # Assume the forceDirectory flag can give us a clue.
        dirLike = forceDirectory

        # Directory separator
        sep = cls._pathModule.sep

        # URI is dir-like if explicitly stated or if it ends on a separator
        endsOnSep = parsed.path.endswith(sep)

        if forceDirectory is False and endsOnSep:
            raise ValueError(
                f"URI {parsed.geturl()} ends with {sep} but "
                "forceDirectory parameter declares it to be a file."
            )

        if forceDirectory or endsOnSep:
            dirLike = True
            # only add the separator if it's not already there
            if not endsOnSep:
                parsed = parsed._replace(path=parsed.path + sep)

        return parsed, dirLike

    @classmethod
    def _fixupPathUri(
        cls,
        parsed: urllib.parse.ParseResult,
        root: ResourcePath | None = None,
        forceAbsolute: bool = False,
        forceDirectory: bool | None = None,
    ) -> tuple[urllib.parse.ParseResult, bool | None]:
        """Correct any issues with the supplied URI.

        Parameters
        ----------
        parsed : `~urllib.parse.ParseResult`
            The result from parsing a URI using `urllib.parse`.
        root : `ResourcePath`, ignored
            Not used by the this implementation since all URIs are
            absolute except for those representing the local file system.
        forceAbsolute : `bool`, ignored.
            Not used by this implementation. URIs are generally always
            absolute.
        forceDirectory : `bool` or `None`, optional
            If `True` forces the URI to end with a separator, otherwise given
            URI is interpreted as is. Specifying that the URI is conceptually
            equivalent to a directory can break some ambiguities when
            interpreting the last element of a path.

        Returns
        -------
        modified : `~urllib.parse.ParseResult`
            Update result if a URI is being handled.
        dirLike : `bool`
            `True` if given parsed URI has a trailing separator or
            ``forceDirectory`` is `True`. Otherwise returns the given value
            of ``forceDirectory``.

        Notes
        -----
        Relative paths are explicitly not supported by RFC8089 but `urllib`
        does accept URIs of the form ``file:relative/path.ext``. They need
        to be turned into absolute paths before they can be used.  This is
        always done regardless of the ``forceAbsolute`` parameter.

        AWS S3 differentiates between keys with trailing POSIX separators (i.e
        ``/dir`` and ``/dir/``) whereas POSIX does not necessarily.

        Scheme-less paths are normalized.
        """
        return cls._fixDirectorySep(parsed, forceDirectory)

    def transfer_from(
        self,
        src: ResourcePath,
        transfer: str,
        overwrite: bool = False,
        transaction: TransactionProtocol | None = None,
        multithreaded: bool = True,
    ) -> None:
        """Transfer to this URI from another.

        Parameters
        ----------
        src : `ResourcePath`
            Source URI.
        transfer : `str`
            Mode to use for transferring the resource. Generically there are
            many standard options: copy, link, symlink, hardlink, relsymlink.
            Not all URIs support all modes.
        overwrite : `bool`, optional
            Allow an existing file to be overwritten. Defaults to `False`.
        transaction : `~lsst.resources.utils.TransactionProtocol`, optional
            A transaction object that can (depending on implementation)
            rollback transfers on error.  Not guaranteed to be implemented.
        multithreaded : `bool`, optional
            If `True` the transfer will be allowed to attempt to improve
            throughput by using parallel download streams. This may of no
            effect if the URI scheme does not support parallel streams or
            if a global override has been applied. If `False` parallel
            streams will be disabled.

        Notes
        -----
        Conceptually this is hard to scale as the number of URI schemes
        grow.  The destination URI is more important than the source URI
        since that is where all the transfer modes are relevant (with the
        complication that "move" deletes the source).

        Local file to local file is the fundamental use case but every
        other scheme has to support "copy" to local file (with implicit
        support for "move") and copy from local file.
        All the "link" options tend to be specific to local file systems.

        "move" is a "copy" where the remote resource is deleted at the end.
        Whether this works depends on the source URI rather than the
        destination URI.  Reverting a move on transaction rollback is
        expected to be problematic if a remote resource was involved.
        """
        raise NotImplementedError(f"No transfer modes supported by URI scheme {self.scheme}")

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
        raise NotImplementedError()

    @overload
    @classmethod
    def findFileResources(
        cls,
        candidates: Iterable[ResourcePathExpression],
        file_filter: str | re.Pattern | None,
        grouped: Literal[True],
    ) -> Iterator[Iterator[ResourcePath]]: ...

    @overload
    @classmethod
    def findFileResources(
        cls,
        candidates: Iterable[ResourcePathExpression],
        *,
        grouped: Literal[True],
    ) -> Iterator[Iterator[ResourcePath]]: ...

    @overload
    @classmethod
    def findFileResources(
        cls,
        candidates: Iterable[ResourcePathExpression],
        file_filter: str | re.Pattern | None = None,
        grouped: Literal[False] = False,
    ) -> Iterator[ResourcePath]: ...

    @classmethod
    def findFileResources(
        cls,
        candidates: Iterable[ResourcePathExpression],
        file_filter: str | re.Pattern | None = None,
        grouped: bool = False,
    ) -> Iterator[ResourcePath | Iterator[ResourcePath]]:
        """Get all the files from a list of values.

        Parameters
        ----------
        candidates : iterable [`str` or `ResourcePath`]
            The files to return and directories in which to look for files to
            return.
        file_filter : `str` or `re.Pattern`, optional
            The regex to use when searching for files within directories.
            By default returns all the found files.
        grouped : `bool`, optional
            If `True` the results will be grouped by directory and each
            yielded value will be an iterator over URIs. If `False` each
            URI will be returned separately.

        Yields
        ------
        found_file: `ResourcePath`
            The passed-in URIs and URIs found in passed-in directories.
            If grouping is enabled, each of the yielded values will be an
            iterator yielding members of the group. Files given explicitly
            will be returned as a single group at the end.

        Notes
        -----
        If a value is a file it is yielded immediately without checking that it
        exists. If a value is a directory, all the files in the directory
        (recursively) that match the regex will be yielded in turn.
        """
        fileRegex = None if file_filter is None else re.compile(file_filter)

        singles = []

        # Find all the files of interest
        for location in candidates:
            uri = ResourcePath(location)
            if uri.isdir():
                for found in uri.walk(fileRegex):
                    if not found:
                        # This means the uri does not exist and by
                        # convention we ignore it
                        continue
                    root, dirs, files = found
                    if not files:
                        continue
                    if grouped:
                        yield (root.join(name) for name in files)
                    else:
                        for name in files:
                            yield root.join(name)
            else:
                if grouped:
                    singles.append(uri)
                else:
                    yield uri

        # Finally, return any explicitly given files in one group
        if grouped and singles:
            yield iter(singles)

    @contextlib.contextmanager
    def open(
        self,
        mode: str = "r",
        *,
        encoding: str | None = None,
        prefer_file_temporary: bool = False,
    ) -> Iterator[ResourceHandleProtocol]:
        """Return a context manager that wraps an object that behaves like an
        open file at the location of the URI.

        Parameters
        ----------
        mode : `str`
            String indicating the mode in which to open the file.  Values are
            the same as those accepted by `open`, though intrinsically
            read-only URI types may only support read modes, and
            `io.IOBase.seekable` is not guaranteed to be `True` on the returned
            object.
        encoding : `str`, optional
            Unicode encoding for text IO; ignored for binary IO.  Defaults to
            ``locale.getpreferredencoding(False)``, just as `open`
            does.
        prefer_file_temporary : `bool`, optional
            If `True`, for implementations that require transfers from a remote
            system to temporary local storage and/or back, use a temporary file
            instead of an in-memory buffer; this is generally slower, but it
            may be necessary to avoid excessive memory usage by large files.
            Ignored by implementations that do not require a temporary.

        Yields
        ------
        cm : `~contextlib.AbstractContextManager`
            A context manager that wraps a `ResourceHandleProtocol` file-like
            object.

        Notes
        -----
        The default implementation of this method uses a local temporary buffer
        (in-memory or file, depending on ``prefer_file_temporary``) with calls
        to `read`, `write`, `as_local`, and `transfer_from` as necessary to
        read and write from/to remote systems.  Remote writes thus occur only
        when the context manager is exited.  `ResourcePath` implementations
        that can return a more efficient native buffer should do so whenever
        possible (as is guaranteed for local files).  `ResourcePath`
        implementations for which `as_local` does not return a temporary are
        required to reimplement `open`, though they may delegate to `super`
        when ``prefer_file_temporary`` is `False`.
        """
        if self.isdir():
            raise IsADirectoryError(f"Directory-like URI {self} cannot be opened.")
        if "x" in mode and self.exists():
            raise FileExistsError(f"File at {self} already exists.")
        if prefer_file_temporary:
            if "r" in mode or "a" in mode:
                local_cm = self.as_local()
            else:
                local_cm = self.temporary_uri(suffix=self.getExtension())
            with local_cm as local_uri:
                assert local_uri.isTemporary, (
                    "ResourcePath implementations for which as_local is not "
                    "a temporary must reimplement `open`."
                )
                with open(local_uri.ospath, mode=mode, encoding=encoding) as file_buffer:
                    if "a" in mode:
                        file_buffer.seek(0, io.SEEK_END)
                    yield file_buffer
                if "r" not in mode or "+" in mode:
                    self.transfer_from(local_uri, transfer="copy", overwrite=("x" not in mode))
        else:
            with self._openImpl(mode, encoding=encoding) as handle:
                yield handle

    @contextlib.contextmanager
    def _openImpl(self, mode: str = "r", *, encoding: str | None = None) -> Iterator[ResourceHandleProtocol]:
        """Implement opening of a resource handle.

        This private method may be overridden by specific `ResourcePath`
        implementations to provide a customized handle like interface.

        Parameters
        ----------
        mode : `str`
            The mode the handle should be opened with
        encoding : `str`, optional
            The byte encoding of any binary text

        Yields
        ------
        handle : `~._resourceHandles.BaseResourceHandle`
            A handle that conforms to the
            `~._resourceHandles.BaseResourceHandle` interface

        Notes
        -----
        The base implementation of a file handle reads in a files entire
        contents into a buffer for manipulation, and then writes it back out
        upon close. Subclasses of this class may offer more fine grained
        control.
        """
        in_bytes = self.read() if "r" in mode or "a" in mode else b""
        if "b" in mode:
            bytes_buffer = io.BytesIO(in_bytes)
            bytes_buffer.name = str(self)
            if "a" in mode:
                bytes_buffer.seek(0, io.SEEK_END)
            yield bytes_buffer
            out_bytes = bytes_buffer.getvalue()
        else:
            if encoding is None:
                encoding = locale.getpreferredencoding(False)
            str_buffer = io.StringIO(in_bytes.decode(encoding))
            str_buffer.name = str(self)
            if "a" in mode:
                str_buffer.seek(0, io.SEEK_END)
            yield str_buffer
            out_bytes = str_buffer.getvalue().encode(encoding)
        if "r" not in mode or "+" in mode:
            self.write(out_bytes, overwrite=("x" not in mode))

    def generate_presigned_get_url(self, *, expiration_time_seconds: int) -> str:
        """Return a pre-signed URL that can be used to retrieve this resource
        using an HTTP GET without supplying any access credentials.

        Parameters
        ----------
        expiration_time_seconds : `int`
            Number of seconds until the generated URL is no longer valid.

        Returns
        -------
        url : `str`
            HTTP URL signed for GET.
        """
        raise NotImplementedError(f"URL signing is not supported for '{self.scheme}'")

    def generate_presigned_put_url(self, *, expiration_time_seconds: int) -> str:
        """Return a pre-signed URL that can be used to upload a file to this
        path using an HTTP PUT without supplying any access credentials.

        Parameters
        ----------
        expiration_time_seconds : `int`
            Number of seconds until the generated URL is no longer valid.

        Returns
        -------
        url : `str`
            HTTP URL signed for PUT.
        """
        raise NotImplementedError(f"URL signing is not supported for '{self.scheme}'")

    def _copy_extra_attributes(self, original_uri: ResourcePath) -> None:
        # May be overridden by subclasses to transfer attributes when a
        # ResourcePath is constructed using the "clone" version of the
        # ResourcePath constructor by passing in a ResourcePath object.
        pass


ResourcePathExpression = str | urllib.parse.ParseResult | ResourcePath | Path
"""Type-annotation alias for objects that can be coerced to ResourcePath.
"""
