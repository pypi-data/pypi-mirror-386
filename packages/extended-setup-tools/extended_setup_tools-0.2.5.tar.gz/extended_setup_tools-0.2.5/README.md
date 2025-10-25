# Extended SetupTools
Python tool for helping in making shorter and smarter `setup.py` scripts.

### Features
 - Automatically extracts application meta-info from the root `__init__.py` file:
   * Name
   * Version
   * License
 - Automatically finds packages
 - Finds and attaches ReadMe file
 - Handles requirements files and maps to the respective `requires` setup arguments:
   * `setup_requires`: `setup-requirements.txt` and `requirements/setup-requirements.txt`
   * `install_requires`: `requirements.txt` and `requirements/requirements.txt`
   * `tests_require`: `test-requirements.txt` and `requirements/test-requirements.txt`
   * `extras_require`: `requirements/requirements-*.txt`
   * Also creates extras `all` that contains all available features
 - Creates test runner with HTML reports
 - Inserts link to the repository as the homepage

### Usage
#### Modern Style
In your `pyproject.toml`, add the following:
```toml
[build-system]
requires = [ 'setuptools', 'extended-setup-tools >= 0.2.2' ]
build-backend = 'setuptools.build_meta'
```

#### Legacy Style
Install package:
```bash
python -m pip install extended-setup-tools
```

Instead of installing to the current scope,
it is possible to install this package as `setup_requires` step:
```python
from setuptools import _install_setup_requires
_install_setup_requires(dict(setup_requires=[ 'extended-setup-tools' ]))
```

#### `src/python_package_name/__init__.py`
```python
from collections import namedtuple

__title__ = 'my-package'
__author__ = 'Peter Zaitcev / USSX Hares'
__license__ = 'BSD 2-clause'
__copyright__ = 'Copyright 2021 Peter Zaitcev'
__version__ = '0.1.0'

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')
version_info = VersionInfo(*__version__.split('.'), releaselevel='alpha', serial=0)

__all__ = \
[
    'version_info',
    '__title__',
    '__author__',
    '__license__',
    '__copyright__',
    '__version__',
]
```

#### `setup.py`
```python
from extended_setup import ExtendedSetupManager
ExtendedSetupManager('python_package_name').setup \
(
    short_description = "Some short description",
    classifiers = [ 'Programming Language :: Python :: 3.7' ],
)
```
