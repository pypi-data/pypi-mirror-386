# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reuse Shortcut Management

Shortcuts Management for reuse license utility

This script can be used to apply the licenses and default copyright holders
to files in the repository.

It uses the short cuts from the ``.reuse/shortcuts.yaml`` file in the current
project root and adds them to the call of ``reuse annotate``. Any command line
option however overwrites the config in ``shortcuts.yaml``
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, TypedDict

import reuse
import yaml
from packaging.version import Version
from reuse.project import Project

from . import _version

# isort: off
try:
    from reuse.cli.annotate import annotate, click
    from reuse.cli.common import ClickObj
except ImportError:
    try:
        from reuse._annotate import (  # type: ignore[no-redef, attr-defined]
            add_arguments as _orig_add_arguments,
        )
        from reuse._annotate import run  # type: ignore[no-redef, attr-defined]
    except ImportError:
        # reuse < 3.0
        from reuse.header import (  # type: ignore[no-redef, attr-defined]
            add_arguments as _orig_add_arguments,
        )
        from reuse.header import run  # type: ignore[no-redef, attr-defined]
        from reuse.vcs import find_root
# isort: on

REUSE_VERSION = Version(reuse.__version__)


__version__ = _version.get_versions()["version"]

__author__ = "Philipp S. Sommer"
__copyright__ = "2025 Helmholtz-Zentrum hereon GmbH"
__credits__ = [
    "Philipp S. Sommer",
]
__license__ = "GPL-3.0-or-later"

__maintainer__ = "Philipp S. Sommer"
__email__ = "philipp.sommer@hereon.de"

__status__ = "Pre-Alpha"


class LicenseShortCut(TypedDict):
    """Shortcut to add a copyright statement"""

    #: The copyright statement
    copyrights: Optional[List[str]]

    #: year of copyright statement
    years: Optional[List[str]]

    #: SPDX Identifier of the license
    licenses: Optional[List[str]]


def load_shortcuts(project: Path) -> Dict[str, LicenseShortCut]:
    """Load the ``shortcuts.yaml`` file."""

    with (project / ".reuse" / "shortcuts.yaml").open() as f:
        return yaml.safe_load(f)


if REUSE_VERSION >= Version("5"):

    def add_annotate_arguments(command):
        command.params.extend(annotate.params)
        return command

    @add_annotate_arguments
    @click.command()
    @click.argument(
        "shortcut",
        required=True,
    )
    @click.pass_context
    def main(ctx, shortcut, **kwargs):
        ctx.obj = ClickObj()

        shortcuts = load_shortcuts(ctx.obj.project.root)

        shortcut_data = shortcuts[shortcut]

        params = ctx.params

        del params["shortcut"]

        if params.get("years") is None:
            params["years"] = ()
        if params.get("copyrights") is None:
            params["copyrights"] = ()

        if not params.get("licenses") and shortcut_data.get("licenses"):
            params["licenses"] = tuple(shortcut_data["licenses"])
        elif params.get("licenses") and shortcut_data.get("licenses"):
            params["licenses"] = tuple(shortcut_data["license"])
        params["years"] = params["years"] + tuple(shortcut_data["years"])
        params["copyrights"] = params["copyrights"] + tuple(
            shortcut_data["copyrights"]
        )
        if REUSE_VERSION >= Version("6"):
            params["years"] = ", ".join(map(str, params["years"]))
        ctx.invoke(annotate, **params)

else:

    def add_arguments(
        parser: ArgumentParser, shortcuts: Dict[str, LicenseShortCut]
    ):
        parser.add_argument(
            "shortcut",
            choices=[key for key in shortcuts if not key.startswith(".")],
            help=(
                "What license should be applied? Shortcuts are loaded from "
                ".reuse/shortcuts.yaml. Possible shortcuts are %(choices)s"
            ),
        )

        _orig_add_arguments(parser)

        parser.set_defaults(func=run)
        parser.set_defaults(parser=parser)

    def main(argv=None):
        parser = ArgumentParser(
            prog=".reuse/add_license.py",
            description=dedent(
                """
                Add copyright and licensing into the header of files with shortcuts

                This script uses the ``reuse annotate`` command to add copyright
                and licensing information into the header the specified files.

                It accepts the same arguments as ``reuse annotate``, plus an
                additional required `shortcuts` argument. The given `shortcut`
                comes from the file at ``.reuse/shortcuts.yaml`` to fill in
                copyright, year and license identifier.

                For further information, please type ``reuse annotate --help``"""
            ),
        )

        if REUSE_VERSION > Version("2") and REUSE_VERSION < Version("3"):
            project = Project(root=find_root(Path.cwd()))
        else:
            project = Project.from_directory(Path.cwd())

        shortcuts = load_shortcuts(project.root)

        add_arguments(parser, shortcuts)

        args = parser.parse_args(argv)

        shortcut = shortcuts[args.shortcut]

        if args.year is None:
            args.year = []
        if args.copyright is None:
            args.copyright = []

        if args.license is None and shortcut.get("licenses"):
            args.license = shortcut["licenses"]
        elif args.license and shortcut.get("licenses"):
            args.license.extend(shortcut["licenses"])
        args.year.extend(shortcut["years"])
        args.copyright.extend(shortcut["copyrights"])

        args.func(args, project)


if __name__ == "__main__":
    main()
