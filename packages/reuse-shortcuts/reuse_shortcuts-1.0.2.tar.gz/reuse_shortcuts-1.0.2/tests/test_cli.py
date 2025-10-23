# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the command line interface."""

import os
import subprocess as spr

import yaml
from git import Repo


def test_shortcut(tmpdir):
    """Test annotating a shortcut."""
    repo_path = tmpdir / "repo"

    Repo.init(repo_path)

    os.makedirs(repo_path / ".reuse")
    with (repo_path / ".reuse" / "shortcuts.yaml").open("w") as f:
        yaml.dump(
            {
                "test": {
                    "years": ["2019", "2020"],
                    "copyrights": ["Some", "one"],
                    "licenses": ["EUPL-1.2", "GPL-3.0-or-later"],
                }
            },
            f,
        )
    test_file = repo_path / "test.md"
    with test_file.open("w") as f:
        f.write("test file")
    spr.check_call(["reuse-shortcuts", "test", "test.md"], cwd=str(repo_path))
    with test_file.open() as f:
        content = f.read()
        assert "Some" in content
        assert "2019" in content
        assert "EUPL-1.2" in content
