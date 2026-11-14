"""Build a dependency graph with recursive breadth-first traversal."""


def build_graph(root, neighbors, max_depth=None, exclude=None):
    """Expand each reachable package once at its shortest distance."""
    if exclude is not None and exclude in root[0]:
        return {}
    graph = {root: ()}
    try:
        visit_layer([root], graph, neighbors, max_depth, exclude)
    except RecursionError as error:
        raise ValueError("graph is too deep; set --max-depth") from error
    return graph


def visit_layer(layer, graph, neighbors, remaining, exclude):
    """Record one BFS layer and recurse into the next frontier."""
    if not layer or remaining == 0:
        return
    following = []
    for package in layer:
        edges = tuple(
            target for target in dict.fromkeys(neighbors(package))
            if exclude is None or exclude not in target[0]
        )
        graph[package] = edges
        for target in edges:
            if target not in graph:
                graph[target] = ()
                following.append(target)
    limit = None if remaining is None else remaining - 1
    visit_layer(following, graph, neighbors, limit, exclude)


def label(package):
    """Format a versioned package or a test graph node."""
    name, version = package
    return f"{name}@{version}" if version else name
