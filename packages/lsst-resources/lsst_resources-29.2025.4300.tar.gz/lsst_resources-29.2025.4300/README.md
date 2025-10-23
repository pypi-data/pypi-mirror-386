# lsst.resources

[![pypi](https://img.shields.io/pypi/v/lsst-resources.svg)](https://pypi.org/project/lsst-resources/)
[![codecov](https://codecov.io/gh/lsst/resources/branch/main/graph/badge.svg?token=jGf63Xc1Ar)](https://codecov.io/gh/lsst/resources)


This package provides a simple interface to local or remote files using URIs.

```
from lsst.resources import ResourcePath

file_uri = ResourcePath("/data/file.txt")
contents = file_uri.read()

s3_uri = ResourcePath("s3://bucket/data/file.txt")
contents = s3_uri.read()
```

The package currently understands `file`, `s3`, `gs`, `http[s]`, and `resource` (Python package resource) URI schemes as well as a scheme-less URI (relative local file path).

The package provides the main file abstraction layer in the [Rubin Observatory Data Butler](https://github.com/lsst/daf_butler) datastore.

PyPI: [lsst-resources](https://pypi.org/project/lsst-resources/)
