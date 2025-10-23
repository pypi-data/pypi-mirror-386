<!--
SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH

SPDX-License-Identifier: CC-BY-4.0
-->

# Reuse Shortcut Management

[![CI](https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts/badges/main/pipeline.svg)](https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts/-/pipelines?page=1&scope=all&ref=main)
[![Code coverage](https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts/badges/main/coverage.svg)](https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts/-/graphs/main/charts)
[![Docs](https://readthedocs.org/projects/reuse-shortcuts/badge/?version=latest)](https://reuse-shortcuts.readthedocs.io/en/latest/)
[![Latest Release](https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts/-/badges/release.svg)](https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts)
[![PyPI version](https://img.shields.io/pypi/v/reuse-shortcuts.svg)](https://pypi.python.org/pypi/reuse-shortcuts/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![REUSE status](https://api.reuse.software/badge/codebase.helmholtz.cloud/hcdc/reuse-shortcuts)](https://api.reuse.software/info/codebase.helmholtz.cloud/hcdc/reuse-shortcuts)


Shortcuts Management for reuse license utility

## Installation

Install this package in a dedicated python environment via

```bash
python -m venv venv
source venv/bin/activate
pip install reuse-shortcuts
```

To use this in a development setup, clone the [source code][source code] from
gitlab, start the development server and make your changes::

```bash
git clone https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts
cd reuse-shortcuts
python -m venv venv
source venv/bin/activate
make dev-install
```

More detailed installation instructions my be found in the [docs][docs].


[source code]: https://codebase.helmholtz.cloud/hcdc/reuse-shortcuts
[docs]: https://reuse-shortcuts.readthedocs.io/en/latest/installation.html


## Usage

Installing this package provides you with a `reuse-shortcuts` CLI executable.
When using this command in a repository, it will look for a file named
`.reuse/shortcuts.yaml` in the root of the repository. This file is supposed to
have the following format:

```yaml
<key>:
  copyrights: []
  years: []
  licenses: []
```

where `copyrights`, `years` and `licenses` are what you would usually add with
`reuse annotate --year <year> --copyright <copyright> --license <license [further options]`, and
`<key>` is an identifier you define yourself.

Instead of calling the very verbose `reuse annotate [...] [further options]`
command, you can just run `reuse-shortcuts <key> [further options]` with the
`<key>` you defined in the `shortcuts.yaml` file.

More detailed usage instructions may be found in the [usage docs][usagedocs].

[usagedocs]: https://reuse-shortcuts.readthedocs.io/en/latest/usage.html

## Technical note

This package has been generated from the template
https://codebase.helmholtz.cloud/hcdc/software-templates/python-package-template.git.

See the template repository for instructions on how to update the skeleton for
this package.


## License information

Copyright © 2025 Helmholtz-Zentrum hereon GmbH



Code files in this repository are licensed under the
GPL-3.0-or-later, if not stated otherwise
in the file.

Documentation files in this repository are licensed under CC-BY-4.0, if not stated otherwise in the file.

Supplementary and configuration files in this repository are licensed
under CC0-1.0, if not stated otherwise
in the file.

Please check the header of the individual files for more detailed
information.



### License management

License management is handled with [``reuse``](https://reuse.readthedocs.io/).
If you have any questions on this, please have a look into the
[contributing guide][contributing] or contact the maintainers of
`reuse-shortcuts`.

[contributing]: https://reuse-shortcuts.readthedocs.io/en/latest/contributing.html
