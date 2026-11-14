"""Parse and validate command-line settings."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

from .fixture import TEST_NAME, load_fixture
from .graph import build_graph
from .registry import NpmRegistry
from .render import ascii_tree, render
from .version import VERSION

NPM_NAME = re.compile(r"(?:@[a-z0-9_.-]+/)?[a-z0-9][a-z0-9_.-]*")


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
    parser.add_argument("--output", default="output")
    parser.add_argument("--no-open", action="store_true")
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
    validate_registry_url(parser, options.repository)


def validate_registry_url(parser, address):
    """Validate the HTTP(S) address of an npm registry."""
    try:
        url = urlsplit(address)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError
        if url.query or url.fragment or url.username is not None:
            raise ValueError
        url.port
    except ValueError:
        parser.error("--repository must be an HTTP(S) registry URL")


def analyze(options):
    """Choose the repository and build the reachable subgraph."""
    if options.test:
        fixture = load_fixture(options.repository)
        root = (options.package, None)
        if root not in fixture:
            raise ValueError(f"test package not found: {options.package}")
        neighbors = fixture.__getitem__
    else:
        registry = NpmRegistry(options.repository)
        root = (options.package, options.version)
        if options.exclude is None or options.exclude not in root[0]:
            registry.dependencies(root)
        def neighbors(package):
            """Resolve dependencies that pass the name filter."""
            return registry.neighbors(package, options.exclude)
    return build_graph(root, neighbors, options.max_depth, options.exclude)


def main():
    """Analyze dependencies and visualize the resulting graph."""
    try:
        options = parse_args()
        graph = analyze(options)
        if options.ascii:
            print(ascii_tree(graph))
        render(graph, options.output, not options.no_open)
    except (OSError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
