"""Generate D2 diagrams, render SVG, and print ASCII trees."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser

from .graph import label


def d2_source(graph):
    """Declare all vertices and edges with stable D2 identifiers."""
    ids = {package: f"p{index}" for index, package in enumerate(graph)}
    lines = ["direction: right"]
    for package, name in ids.items():
        quoted = json.dumps(label(package), ensure_ascii=False)
        lines.append(f"{name}: {quoted}")
    for package, edges in graph.items():
        for target in edges:
            lines.append(f"{ids[package]} -> {ids[target]}")
    return "\n".join(lines) + "\n"


def ascii_tree(graph):
    """Show repeated targets without following their children again."""
    if not graph:
        return "(empty graph)"
    root = next(iter(graph))
    lines = []
    seen = set()
    stack = [(root, "", "", "")]
    while stack:
        package, prefix, branch, continuation = stack.pop()
        repeated = package in seen
        suffix = " [seen]" if repeated else ""
        lines.append(f"{prefix}{branch}{label(package)}{suffix}")
        if repeated:
            continue
        seen.add(package)
        edges = graph[package]
        for index, target in reversed(list(enumerate(edges, start=1))):
            last = index == len(edges)
            stack.append((
                target, prefix + continuation,
                "`-- " if last else "|-- ",
                "    " if last else "|   ",
            ))
    return "\n".join(lines)


def render(graph, directory, open_image):
    """Write D2 and SVG files and open the SVG in the default viewer."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "graph.d2"
    image = directory / "graph.svg"
    source.write_text(d2_source(graph), encoding="utf-8")
    executable = shutil.which("d2")
    if executable is None:
        raise ValueError(f"D2 CLI is required to render SVG; source: {source}")
    result = subprocess.run(
        [executable, str(source), str(image)], check=False,
    )
    if result.returncode:
        raise ValueError(f"D2 failed to render {source}")
    print(image)
    if open_image and not show_image(image):
        print("Open the printed SVG path in a browser.", file=sys.stderr)


def show_image(image):
    """Open a local SVG on macOS or in the default browser."""
    if sys.platform == "darwin":
        return subprocess.run(
            ["open", str(image)], check=False,
        ).returncode == 0
    return webbrowser.open(image.as_uri())
