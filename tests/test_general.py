# Copyright (c) 2018 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.

import sys


def test_import_xdrlib2():
    import xdrlib2  # noqa: F401

    assert "xdrlib2" in sys.modules
