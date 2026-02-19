"""UnitAI CLI — `unitai` command entrypoint."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional


def _cmd_test(args: argparse.Namespace) -> int:
    """Run tests via pytest with UnitAI integration."""
    import pytest  # type: ignore[import]
    
    from unitai.config import get_config

    config = get_config()

    # Map CLI flags to UNITAI_* env vars (highest priority)
    if args.n is not None:
        os.environ["UNITAI_DEFAULT_N"] = str(args.n)
    if args.threshold is not None:
        os.environ["UNITAI_DEFAULT_THRESHOLD"] = str(args.threshold)
    if args.budget is not None:
        os.environ["UNITAI_COST_BUDGET_PER_TEST"] = str(args.budget)
    if args.model is not None:
        os.environ["UNITAI_MODEL"] = args.model
    
    # Cache flags
    if args.record:
        os.environ["UNITAI_CACHE_ENABLED"] = "true"
        os.environ["UNITAI_CACHE_MODE"] = "record"
    elif args.replay:
        os.environ["UNITAI_CACHE_ENABLED"] = "true"
        os.environ["UNITAI_CACHE_MODE"] = "replay"
    elif args.no_cache:
        os.environ["UNITAI_CACHE_ENABLED"] = "false"
    elif config.cache_enabled:
        # Use config default
        os.environ["UNITAI_CACHE_ENABLED"] = "true"

    pytest_args: List[str] = []

    if args.path:
        pytest_args.append(args.path)

    if args.verbose or config.verbose:
        pytest_args.append("-v")

    # JUnit XML output
    xml_path = args.xml or os.environ.get("UNITAI_JUNIT_XML", config.junit_xml)
    Path(xml_path).parent.mkdir(parents=True, exist_ok=True)
    pytest_args += [f"--junitxml={xml_path}"]

    exit_code: int = pytest.main(pytest_args)

    # Print summary from JUnit XML after pytest finishes
    try:
        from unitai.cli.results import display_results
        display_results(xml_path)
    except Exception:
        pass

    return int(exit_code)


def _cmd_init(args: argparse.Namespace) -> int:
    """Scaffold unitai.toml and an example test file."""
    from unitai.cli.templates import EXAMPLE_TEST_TEMPLATE, UNITAI_TOML_TEMPLATE

    cwd = Path.cwd()
    created: List[str] = []

    # unitai.toml
    toml_path = cwd / "unitai.toml"
    if not toml_path.exists():
        toml_path.write_text(UNITAI_TOML_TEMPLATE)
        created.append(str(toml_path))
        print(f"  Created: {toml_path}")
    else:
        print(f"  Skipped (exists): {toml_path}")

    # Example test
    tests_dir = cwd / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    example_path = tests_dir / "test_agent_example.py"
    if not example_path.exists():
        example_path.write_text(EXAMPLE_TEST_TEMPLATE)
        created.append(str(example_path))
        print(f"  Created: {example_path}")
    else:
        print(f"  Skipped (exists): {example_path}")

    # .gitignore — append .unitai/ if file exists and entry missing
    gitignore_path = cwd / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if ".unitai/" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# UnitAI cache and artifacts\n.unitai/\n")
            print(f"  Updated: {gitignore_path} (added .unitai/)")
        else:
            print(f"  Skipped (already present): .unitai/ in {gitignore_path}")

    if created:
        print("\nDone! Run `unitai test` to execute your tests.")
    return 0


def _cmd_results(args: argparse.Namespace) -> int:
    """Display results from the last JUnit XML run."""
    from unitai.cli.results import display_results

    xml_path: str = args.xml or os.environ.get(
        "UNITAI_JUNIT_XML", "test-results/unitai.xml"
    )
    display_results(xml_path)
    return 0


def _cmd_cache(args: argparse.Namespace) -> int:
    """Cache management."""
    from unitai.config import get_config
    from unitai.runner.replay import ReplayCache
    
    config = get_config()
    cache = ReplayCache(
        directory=config.cache_directory,
        ttl_hours=config.cache_ttl_hours,
    )
    
    subcommand: str = args.cache_cmd or "stats"
    if subcommand == "clear":
        cache.clear()
        print("[UnitAI] Cache cleared.")
        return 0
    elif subcommand == "stats":
        stats = cache.stats()
        print(f"[UnitAI] Cache Statistics:")
        print(f"  Entries: {stats.entry_count}")
        print(f"  Size: {stats.total_size_bytes / 1024:.2f} KB")
        print(f"  Hits: {stats.hit_count}")
        print(f"  Misses: {stats.miss_count}")
        if stats.hit_count + stats.miss_count > 0:
            print(f"  Hit Rate: {stats.hit_rate * 100:.1f}%")
        return 0
    else:
        print(f"[UnitAI] Unknown cache subcommand: {subcommand}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unitai",
        description="UnitAI — testing framework for AI agents.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- test ---
    test_parser = subparsers.add_parser("test", help="Run UnitAI tests.")
    test_parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help=(
            "Path to test file or directory "
            "(default: pytest discovers automatically)."
        ),
    )
    test_parser.add_argument(
        "--n", type=int, default=None, help="Number of statistical runs."
    )
    test_parser.add_argument(
        "--threshold", type=float, default=None, help="Pass rate threshold (0.0–1.0)."
    )
    test_parser.add_argument(
        "--budget", type=float, default=None, help="Per-test cost budget in USD."
    )
    test_parser.add_argument(
        "--model", type=str, default=None, help="LLM model to use."
    )
    test_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output."
    )
    test_parser.add_argument(
        "--xml",
        default=None,
        help="Path to JUnit XML output file.",
    )
    test_parser.add_argument(
        "--record",
        action="store_true",
        help="Force fresh API calls and save responses to cache.",
    )
    test_parser.add_argument(
        "--replay",
        action="store_true",
        help="Use cache only, fail if cache misses.",
    )
    test_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cache entirely (default).",
    )

    # --- init ---
    subparsers.add_parser("init", help="Scaffold config and example test.")

    # --- results ---
    results_parser = subparsers.add_parser("results", help="Display last test results.")
    results_parser.add_argument(
        "--xml",
        default=None,
        help="Path to JUnit XML file (default: test-results/unitai.xml).",
    )

    # --- cache ---
    cache_parser = subparsers.add_parser("cache", help="Cache management.")
    cache_parser.add_argument(
        "cache_cmd",
        nargs="?",
        choices=["clear", "stats"],
        default="stats",
        help="Cache subcommand.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "test": _cmd_test,
        "init": _cmd_init,
        "results": _cmd_results,
        "cache": _cmd_cache,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
