from pathlib import Path

import tomli


def test_package_discovery_excludes_runtime_directory():
    config = tomli.loads(Path("pyproject.toml").read_text())

    find_config = config["tool"]["setuptools"]["packages"]["find"]
    assert find_config["include"] == ["app*"]
    assert "runtime*" in find_config["exclude"]
