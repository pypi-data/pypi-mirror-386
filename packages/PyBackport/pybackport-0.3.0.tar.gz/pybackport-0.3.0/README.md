![tests_badge](https://github.com/Jtachan/PyBackport/actions/workflows/unittests.yml/badge.svg)
[![PyPI Version](https://img.shields.io/pypi/v/PyBackport)](https://pypi.org/project/PyBackport/)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/) 
[![MIT License](https://img.shields.io/github/license/Jtachan/PyBackport)](https://github.com/Jtachan/PyBackport/blob/master/LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/PyBackport)](https://pypi.org/project/PyBackport/) 
[![Docs](https://img.shields.io/badge/Read_the_docs-blue)](https://Jtachan.github.io/PyBackport/)

# Python Backport

The `py_back` modules serve the next purposes of importing features from newer python releases into older versions.

For example, `enum.StrEnum` is new in Python 3.11, but `py_back` allows users to use it on previous versions.

```python
from py_back import enum

class Animal(enum.StrEnum):
    DOG = "dog"
    CAT = "cat"
```


## Setup

Install the package via pip.

```shell
pip install PyBackport
```

## 📖 Documentation

Documentation can be found:

- At the released [mkdocs page](https://Jtachan.github.io/PyBackport/).
- Within the [`docs`](https://github.com/Jtachan/PyBackport/blob/main/docs/index.md) folder.
