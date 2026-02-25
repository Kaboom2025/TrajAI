import os


def test_directory_structure() -> None:
    expected_dirs = [
        "trajai",
        "trajai/core",
        "trajai/mock",
        "trajai/runner",
        "trajai/adapters",
        "trajai/pytest_plugin",
        "trajai/cli",
        "trajai/ci",
    ]

    for d in expected_dirs:
        assert os.path.isdir(d), f"Directory {d} does not exist"
        init_file = os.path.join(d, "__init__.py")
        assert os.path.isfile(init_file), f"__init__.py missing in {d}"

    expected_files = [
        "pyproject.toml",
        ".gitignore",
        ".github/workflows/ci.yml",
    ]

    for f in expected_files:
        assert os.path.isfile(f), f"Configuration file {f} does not exist"
