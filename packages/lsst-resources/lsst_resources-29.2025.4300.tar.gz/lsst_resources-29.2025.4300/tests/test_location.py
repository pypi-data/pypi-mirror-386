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

import copy
import os.path
import pathlib
import pickle
import posixpath
import unittest

from lsst.resources import ResourcePath
from lsst.resources.location import Location, LocationFactory
from lsst.resources.utils import os2posix, posix2os


class LocationTestCase(unittest.TestCase):
    """Tests for Location within datastore."""

    def testResourcePath(self):
        """Tests whether ResourcePath instantiates correctly given different
        arguments.
        """
        # Root to use for relative paths
        testRoot = "/tempdir/"

        # uriStrings is a list of tuples containing test string, forceAbsolute,
        # forceDirectory as arguments to ResourcePath and scheme, netloc and
        # path as expected attributes. Test asserts constructed equals to
        # expected.
        # 1) no determinable schemes (ensures schema and netloc are not set)
        osRelFilePath = os.path.join(testRoot, "relative/file.ext")
        uriStrings = [
            ("relative/file.ext", True, False, "file", "", osRelFilePath),
            ("relative/file.ext", False, False, "", "", "relative/file.ext"),
            ("test/../relative/file.ext", True, False, "file", "", osRelFilePath),
            ("test/../relative/file.ext", False, False, "", "", "relative/file.ext"),
            ("relative/dir", False, True, "", "", "relative/dir/"),
        ]
        # 2) implicit file scheme, tests absolute file and directory paths
        uriStrings.extend(
            (
                ("/rootDir/absolute/file.ext", True, False, "file", "", "/rootDir/absolute/file.ext"),
                ("~/relative/file.ext", True, False, "file", "", os.path.expanduser("~/relative/file.ext")),
                ("~/relative/file.ext", False, False, "file", "", os.path.expanduser("~/relative/file.ext")),
                ("/rootDir/absolute/", True, None, "file", "", "/rootDir/absolute/"),
                ("/rootDir/absolute", True, True, "file", "", "/rootDir/absolute/"),
                ("~/rootDir/absolute", True, True, "file", "", os.path.expanduser("~/rootDir/absolute/")),
            )
        )
        # 3) explicit file scheme, absolute and relative file and directory URI
        posixRelFilePath = posixpath.join(testRoot, "relative/file.ext")
        uriStrings.extend(
            (
                ("file:///rootDir/absolute/file.ext", True, False, "file", "", "/rootDir/absolute/file.ext"),
                ("file:relative/file.ext", True, False, "file", "", posixRelFilePath),
                ("file:///absolute/directory/", True, None, "file", "", "/absolute/directory/"),
                ("file:///absolute/directory", True, True, "file", "", "/absolute/directory/"),
            )
        )
        # 4) S3 scheme (ensured Keys as dirs and fully specified URIs work)
        uriStrings.extend(
            (
                ("s3://bucketname/rootDir/", True, None, "s3", "bucketname", "/rootDir/"),
                ("s3://bucketname/rootDir", True, True, "s3", "bucketname", "/rootDir/"),
                (
                    "s3://bucketname/rootDir/relative/file.ext",
                    True,
                    False,
                    "s3",
                    "bucketname",
                    "/rootDir/relative/file.ext",
                ),
            )
        )
        # 5) HTTPS scheme
        uriStrings.extend(
            (
                ("https://www.lsst.org/rootDir/", True, None, "https", "www.lsst.org", "/rootDir/"),
                ("https://www.lsst.org/rootDir", True, True, "https", "www.lsst.org", "/rootDir/"),
                (
                    "https://www.lsst.org/rootDir/relative/file.ext",
                    True,
                    False,
                    "https",
                    "www.lsst.org",
                    "/rootDir/relative/file.ext",
                ),
            )
        )

        for uriInfo in uriStrings:
            uri = ResourcePath(uriInfo[0], root=testRoot, forceAbsolute=uriInfo[1], forceDirectory=uriInfo[2])
            with self.subTest(in_uri=repr(uriInfo[0]), out_uri=repr(uri)):
                self.assertEqual(uri.scheme, uriInfo[3], "test scheme")
                self.assertEqual(uri.netloc, uriInfo[4], "test netloc")
                self.assertEqual(uri.path, uriInfo[5], "test path")

        # test root becomes abspath(".") when not specified, note specific
        # file:// scheme case
        uriStrings = (
            # URI, forceAbsolute, forceDirectory, scheme, netloc, path
            ("file://relative/file.ext", True, False, "file", "relative", "/file.ext"),
            ("file:relative/file.ext", False, False, "file", "", os.path.abspath("relative/file.ext")),
            ("file:relative/dir/", True, True, "file", "", os.path.abspath("relative/dir") + "/"),
            ("relative/file.ext", True, False, "file", "", os.path.abspath("relative/file.ext")),
        )

        for uriInfo in uriStrings:
            uri = ResourcePath(uriInfo[0], forceAbsolute=uriInfo[1], forceDirectory=uriInfo[2])
            with self.subTest(in_uri=repr(uriInfo[0]), out_uri=repr(uri)):
                self.assertEqual(uri.scheme, uriInfo[3], "test scheme")
                self.assertEqual(uri.netloc, uriInfo[4], "test netloc")
                # Use ospath here to ensure that we have unquoted any
                # special characters in the parent directories.
                self.assertEqual(uri.ospath, uriInfo[5], "test path")

        # File replacement
        uriStrings = (
            ("relative/file.ext", "newfile.fits", "relative/newfile.fits"),
            ("relative/", "newfile.fits", "relative/newfile.fits"),
            ("https://www.lsst.org/butler/", "butler.yaml", "/butler/butler.yaml"),
            ("s3://amazon/datastore/", "butler.yaml", "/datastore/butler.yaml"),
            ("s3://amazon/datastore/mybutler.yaml", "butler.yaml", "/datastore/butler.yaml"),
        )

        for uriInfo in uriStrings:
            uri = ResourcePath(uriInfo[0], forceAbsolute=False).updatedFile(uriInfo[1])
            with self.subTest(in_uri=repr(uriInfo[0]), out_uri=repr(uri)):
                self.assertEqual(uri.path, uriInfo[2])

        # Check that schemeless can become file scheme.
        schemeless = ResourcePath("relative/path.ext")
        filescheme = ResourcePath("/absolute/path.ext")
        self.assertEqual(schemeless.scheme, "file")
        self.assertEqual(filescheme.scheme, "file")
        self.assertEqual(type(schemeless), type(filescheme))

        # Copy constructor
        uri = ResourcePath("s3://amazon/datastore", forceDirectory=True)
        uri2 = ResourcePath(uri)
        self.assertEqual(uri, uri2)
        uri = ResourcePath("file://amazon/datastore/file.txt")
        uri2 = ResourcePath(uri)
        self.assertEqual(uri, uri2)

        # Copy constructor using subclass
        uri3 = type(uri)(uri)
        self.assertEqual(type(uri), type(uri3))

        # Explicit copy
        uri4 = copy.copy(uri3)
        self.assertEqual(uri4, uri3)
        uri4 = copy.deepcopy(uri3)
        self.assertEqual(uri4, uri3)

    def testUriRoot(self):
        osPathRoot = pathlib.Path(__file__).absolute().root
        rootUris = (osPathRoot, "s3://bucket", "file://localhost/", "https://a.b.com")
        for uri_str in rootUris:
            uri = ResourcePath(uri_str, forceDirectory=True)
            self.assertEqual(uri.relativeToPathRoot, "./", f"Testing uri: {uri}")
            self.assertTrue(uri.is_root, f"Testing URI {uri} is a root URI")

        exampleLocalFile = os.path.join(osPathRoot, "a", "b", "c")
        uriStrings = (
            ("file://localhost/file.ext", "file.ext"),
            (exampleLocalFile, os.path.join("a", "b", "c")),
            ("s3://bucket/path/file.ext", "path/file.ext"),
            ("https://host.com/a/b/c.d", "a/b/c.d"),
        )

        for uri_str, result in uriStrings:
            uri = ResourcePath(uri_str)
            self.assertEqual(uri.relativeToPathRoot, result)

    def testUriJoin(self):
        uri = ResourcePath("a/b/c/d", forceDirectory=True, forceAbsolute=False)
        uri2 = uri.join("e/f/g.txt")
        self.assertEqual(str(uri2), "a/b/c/d/e/f/g.txt", f"Checking joined URI {uri} -> {uri2}")

        uri = ResourcePath("a/b/c/d/", forceAbsolute=False)
        uri2 = uri.join("e/f/g.txt")
        self.assertEqual(str(uri2), "a/b/c/d/e/f/g.txt", f"Checking joined URI {uri} -> {uri2}")

        uri = ResourcePath("a/b/c/d", forceDirectory=True, forceAbsolute=True)
        uri2 = uri.join("e/f/g.txt")
        self.assertTrue(str(uri2).endswith("a/b/c/d/e/f/g.txt"), f"Checking joined URI {uri} -> {uri2}")

        uri = ResourcePath("s3://bucket/a/b/c/d", forceDirectory=True)
        uri2 = uri.join("newpath/newfile.txt")
        self.assertEqual(str(uri2), "s3://bucket/a/b/c/d/newpath/newfile.txt")

        uri = ResourcePath("s3://bucket/a/b/c/d/")
        uri2 = uri.join("newpath/newfile.txt")
        self.assertEqual(str(uri2), "s3://bucket/a/b/c/d/newpath/newfile.txt")

    def testResourcePathSerialization(self):
        """Test that we can pickle and yaml."""
        uri = ResourcePath("a/b/c/d")
        uri2 = pickle.loads(pickle.dumps(uri))
        self.assertEqual(uri, uri2)
        self.assertFalse(uri2.dirLike)

        uri = ResourcePath("a/b/c/d", forceDirectory=True)
        uri2 = pickle.loads(pickle.dumps(uri))
        self.assertEqual(uri, uri2)
        self.assertTrue(uri2.dirLike)

    def testUriExtensions(self):
        """Test extension extraction."""
        files = (
            ("file.fits.gz", ".fits.gz"),
            ("file.fits", ".fits"),
            ("file.fits.xz", ".fits.xz"),
            ("file.fits.tar", ".tar"),
            ("file", ""),
            ("flat_i_sim_1.4_blah.fits.gz", ".fits.gz"),
            ("flat_i_sim_1.4_blah.txt", ".txt"),
            ("flat_i_sim_1.4_blah.fits.fz", ".fits.fz"),
            ("flat_i_sim_1.4_blah.fits.txt", ".txt"),
            ("s3://bucket/c/a.b/", ".b"),
            ("s3://bucket/c/a.b", ".b"),
            ("file://localhost/c/a.b.gz", ".b.gz"),
        )

        for file, expected in files:
            test_string = file
            if ":" not in test_string:
                test_string = f"a/b/{test_string}"
            uri = ResourcePath(test_string)
            self.assertEqual(uri.getExtension(), expected)

    def testFileLocation(self):
        root = os.path.abspath(os.path.curdir)
        factory = LocationFactory(root)
        print(f"Factory created: {factory}")

        pathInStore = "relative/path/file.ext"
        loc1 = factory.fromPath(pathInStore)

        self.assertEqual(loc1.path, os.path.join(root, pathInStore))
        self.assertEqual(loc1.pathInStore.path, pathInStore)
        self.assertTrue(loc1.uri.geturl().startswith("file:///"))
        self.assertTrue(loc1.uri.geturl().endswith("file.ext"))
        loc1.updateExtension("fits")
        self.assertTrue(loc1.uri.geturl().endswith("file.fits"), f"Checking 'fits' extension in {loc1.uri}")
        loc1.updateExtension("fits.gz")
        self.assertEqual(loc1.uri.basename(), "file.fits.gz")
        self.assertTrue(
            loc1.uri.geturl().endswith("file.fits.gz"), f"Checking 'fits.gz' extension in {loc1.uri}"
        )
        self.assertEqual(loc1.getExtension(), ".fits.gz")
        loc1.updateExtension(".jpeg")
        self.assertTrue(loc1.uri.geturl().endswith("file.jpeg"), f"Checking 'jpeg' extension in {loc1.uri}")
        loc1.updateExtension(None)
        self.assertTrue(
            loc1.uri.geturl().endswith("file.jpeg"), f"Checking unchanged extension in {loc1.uri}"
        )
        loc1.updateExtension("")
        self.assertTrue(loc1.uri.geturl().endswith("file"), f"Checking no extension in {loc1.uri}")
        self.assertEqual(loc1.getExtension(), "")

        loc2 = factory.fromPath(pathInStore)
        loc3 = factory.fromPath(pathInStore)
        self.assertEqual(loc2, loc3)

    def testAbsoluteLocations(self):
        """Using a pathInStore that refers to absolute URI."""
        loc = Location(None, "file:///something.txt")
        self.assertEqual(loc.pathInStore.path, "/something.txt")
        self.assertEqual(str(loc.uri), "file:///something.txt")

        with self.assertRaises(ValueError):
            Location(None, "relative.txt")

    def testRelativeRoot(self):
        root = os.path.abspath(os.path.curdir)
        factory = LocationFactory(os.path.curdir)

        pathInStore = "relative/path/file.ext"
        loc1 = factory.fromPath(pathInStore)

        self.assertEqual(loc1.path, os.path.join(root, pathInStore))
        self.assertEqual(loc1.pathInStore.path, pathInStore)
        self.assertEqual(loc1.uri.scheme, "file")

        with self.assertRaises(ValueError):
            factory.fromPath("../something")

    def testQuotedRoot(self):
        """Test we can handle quoted characters."""
        root = "/a/b/c+1/d"
        factory = LocationFactory(root)

        pathInStore = "relative/path/file.ext.gz"

        for pathInStore in (
            "relative/path/file.ext.gz",
            "relative/path+2/file.ext.gz",
            "relative/path+3/file&.ext.gz",
        ):
            loc1 = factory.fromPath(pathInStore)

            self.assertEqual(loc1.pathInStore.path, pathInStore)
            self.assertEqual(loc1.path, os.path.join(root, pathInStore))
            self.assertIn("%", str(loc1.uri))
            self.assertEqual(loc1.getExtension(), ".ext.gz")

    def testHttpLocation(self):
        root = "https://www.lsst.org/butler/datastore"
        factory = LocationFactory(root)
        print(f"Factory created: {factory}")

        pathInStore = "relative/path/file.ext"
        loc1 = factory.fromPath(pathInStore)

        self.assertEqual(loc1.path, posixpath.join("/butler/datastore", pathInStore))
        self.assertEqual(loc1.pathInStore.path, pathInStore)
        self.assertEqual(loc1.uri.scheme, "https")
        self.assertEqual(loc1.uri.basename(), "file.ext")
        loc1.updateExtension("fits")
        self.assertTrue(loc1.uri.basename(), "file.fits")

    def testPosix2OS(self):
        """Test round tripping of the posix to os.path conversion helpers."""
        testPaths = ("/a/b/c.e", "a/b", "a/b/", "/a/b", "/a/b/", "a/b/c.e")
        for p in testPaths:
            with self.subTest(path=repr(p)):
                self.assertEqual(os2posix(posix2os(p)), p)

    def testSplit(self):
        """Tests split functionality."""
        testRoot = "/tempdir/"

        testPaths = (
            "/absolute/file.ext",
            "/absolute/",
            "file:///absolute/file.ext",
            "file:///absolute/",
            "s3://bucket/root/file.ext",
            "s3://bucket/root/",
            "https://www.lsst.org/root/file.ext",
            "https://www.lsst.org/root/",
            "relative/file.ext",
            "relative/",
        )

        osRelExpected = os.path.join(testRoot, "relative")
        expected = (
            ("file:///absolute/", "file.ext"),
            ("file:///absolute/", ""),
            ("file:///absolute/", "file.ext"),
            ("file:///absolute/", ""),
            ("s3://bucket/root/", "file.ext"),
            ("s3://bucket/root/", ""),
            ("https://www.lsst.org/root/", "file.ext"),
            ("https://www.lsst.org/root/", ""),
            (f"file://{osRelExpected}/", "file.ext"),
            (f"file://{osRelExpected}/", ""),
        )

        for p, e in zip(testPaths, expected, strict=True):
            with self.subTest(path=repr(p)):
                uri = ResourcePath(p, testRoot)
                head, tail = uri.split()
                self.assertEqual((head.geturl(), tail), e)

        # explicit file scheme should force posixpath, check os.path is ignored
        posixRelFilePath = posixpath.join(testRoot, "relative")
        uri = ResourcePath("file:relative/file.ext", testRoot)
        head, tail = uri.split()
        self.assertEqual((head.geturl(), tail), (f"file://{posixRelFilePath}/", "file.ext"))

        # check head can be empty and we do not get an absolute path back
        uri = ResourcePath("file.ext", forceAbsolute=False)
        head, tail = uri.split()
        self.assertEqual((head.geturl(), tail), ("./", "file.ext"))

        # ensure empty path splits to a directory URL
        uri = ResourcePath("", forceAbsolute=False)
        head, tail = uri.split()
        self.assertEqual((head.geturl(), tail), ("./", ""))

        uri = ResourcePath(".", forceAbsolute=False, forceDirectory=True)
        head, tail = uri.split()
        self.assertEqual((head.geturl(), tail), ("./", ""))


if __name__ == "__main__":
    unittest.main()
