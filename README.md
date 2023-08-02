[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# ``xdrlib2`` -- A toolkit for the XDR standard

The `xdrlib2` module is an alternative for the `xdrlib` package
in Python's standard library.
The differences with the `xdrlib` package are:

- `xdrlib2` implements :rfc:`4506`, which obsoletes :rfc:`1832`, which in turn replaced :rfc:`1014`.
  The standard library's `xdrlib` package on the other hand only partially implements
  the obsolete :rfc:`1014`.
- `xdrlib2` offers a compiler that can convert XDR specifications files to Python
  modules with the appropriate type definitions. This allows
  users of the `xdrlib2` to directly use the high-level XDR data structures
  defined in the specifications. That is not possible with `xdrlib`, because
  that deals only with basic integer, float, and list types.
- `xdrlib2` is extensible. Users can define their own variant of the language, define type definitions and compile
  these specifications into corresponding Python modules. 

## Installation

```shell
pip install xdrlib2
```

This installs the `xdrlib2` library. One of the things it installs is an executable called `xdrc`.
This executable can be used to compile `XDR` specification files into corresponding 
Python modules.
