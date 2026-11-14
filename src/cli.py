"""Parse and validate command-line settings."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

from .registry import NpmRegistry
from .version import VERSION

NPM_NAME = re.compile(r"(?:@[a-z0-9_.-]+/)?[a-z0-9][a-z0-9_.-]*")
TEST_NAME = re.compile(r"[A-Z]+")


def depth(value):
    """Accept a nonnegative BFS depth."""
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("expected a nonnegative depth")
    return number


def parse_args(argv=None):
    """Validate the package, repository and analysis options."""
    parser = argparse.ArgumentParser(description="Explore npm dependencies")
    parser.add_argument("--package", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--version", required=True)
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--max-depth", type=depth)
    parser.add_argument("--exclude")
    options = parser.parse_args(argv)
    validate(parser, options)
    return options


def validate(parser, options):
    """Check values that depend on the selected repository mode."""
    pattern = TEST_NAME if options.test else NPM_NAME
    if not pattern.fullmatch(options.package):
        parser.error("invalid --package for the selected mode")
    if not VERSION.fullmatch(options.version):
        parser.error("--version must be an exact semantic version")
    if options.exclude is not None and not options.exclude.strip():
        parser.error("--exclude must contain a nonblank substring")
    if options.test:
        if not Path(options.repository).is_file():
            parser.error("--repository must be an existing test file")
        return
    try:
        url = urlsplit(options.repository)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError
        if url.query or url.fragment or url.username is not None:
            raise ValueError
        url.port
    except ValueError:
        parser.error("--repository must be an HTTP(S) registry URL")


def main():
    """Print direct dependencies for the registry prototype."""
    options = parse_args()
    try:
        if options.test:
            raise ValueError("test repositories are supported from stage 3")
        registry = NpmRegistry(options.repository)
        package = (options.package, options.version)
        for name, spec in sorted(registry.dependencies(package).items()):
            print(f"{name}: {spec}")
    except ValueError as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
