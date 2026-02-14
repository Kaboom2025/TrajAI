import os

def test_directory_structure():
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
