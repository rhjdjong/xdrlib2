# Copyright (c) 2023 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.
from typing import Self


class Integer(int):
    def __bytes__(self) -> bytes:
        return self.to_bytes(4, "big", signed=True)

    @classmethod
    def _decode(cls, bytestring: bytes) -> Self:
        v = cls.from_bytes(bytestring, "big", signed=True)
        return cls(v)
