# Copyright (c) 2023 Ruud de Jong
# This file is part of the xdrlib2 project which is released under the MIT license.
# See https://github.com/rhjdjong/xdrlib2 for details.
from typing import Any, Literal, Self

XDR_WORD_SIZE = 4
XDR_BYTE_ORDER: Literal["little", "big"] = "big"


class XdrType:
    _abstract = True

    def __init_subclass__(cls, /, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls._abstract:
            raise TypeError(f"Cannot instantiate abstract base class {cls.__name__}")
        return super().__new__(cls, *args, **kwargs)


class XdrInteger(XdrType, int):
    bits = 0
    data_size = 0
    hi = 0
    lo = 0
    padding = b""
    signed = False
    size = 0

    def __init_subclass__(cls, /, bits: int | None = None, signed: bool | None = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls._abstract:
            if bits is None or signed is None:
                raise TypeError("Missing parameters in class definition")
            cls.bits = bits
            cls.signed = signed
            cls.hi = 1 << (bits - int(signed))
            cls.lo = -cls.hi if signed else 0
            cls.data_size = 1 + (bits - 1) // 8
            padding_size = (XDR_WORD_SIZE - (cls.data_size % XDR_WORD_SIZE)) % XDR_WORD_SIZE
            cls.size = cls.data_size + padding_size
            cls.padding = bytes(padding_size)
            cls._abstract = False
        else:
            if bits is not None or signed is not None:
                raise TypeError(f"Type alias for {cls.__name__} cannot redefine type.")

    def __new__(cls, *args: Any) -> Self:
        # Delegate argument validation to the superclass
        instance = super().__new__(cls, *args)
        if cls.lo <= instance < cls.hi:
            return instance
        raise ValueError(f"Invalid value {instance} for class {cls.__name__}")

    def to_bytes(self) -> bytes:  # type: ignore[override]
        return super().to_bytes(self.data_size, XDR_BYTE_ORDER, signed=self.signed) + self.padding

    @classmethod
    def from_bytes(cls, bytestring: bytes) -> Self:  # type: ignore[override]
        v = super().from_bytes(bytestring[: cls.data_size], XDR_BYTE_ORDER, signed=cls.signed)
        return cls(v)

    @classmethod
    def typedef(cls, name: str, **kwargs: Any) -> type[Self]:
        return type(name, (cls,), {}, **kwargs)


Int32 = XdrInteger.typedef("Int32", bits=32, signed=True)
UInt32 = XdrInteger.typedef("UInt32", bits=32, signed=False)
Int64 = XdrInteger.typedef("Int64", bits=64, signed=True)
UInt64 = XdrInteger.typedef("UInt64", bits=64, signed=False)

Integer = Int32.typedef("Integer")
UnsignedInteger = UInt32.typedef("UnsignedInteger")
Hyper = Int64.typedef("Hyper")
UnsignedHyper = UInt64.typedef("UnsignedHyper")
