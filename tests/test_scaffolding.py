import os


def test_directory_structure() -> None:
    expected_dirs = [
        "unitai",
        "unitai/core",
        "unitai/mock",
        "unitai/runner",
        "unitai/adapters",
        "unitai/pytest_plugin",
        "unitai/cli",
        "unitai/ci",
        "unitai/config",
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
