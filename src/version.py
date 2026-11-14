"""Define the syntax of an exact npm semantic version."""

import re

NUMBER = r"(?:0|[1-9][0-9]*)"
IDENT = r"[0-9A-Za-z-]+"
PRE = rf"(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
    rf"(?:-{PRE}(?:\.{PRE})*)?(?:\+{IDENT}(?:\.{IDENT})*)?"
)

PARTIAL = re.compile(
    rf"({NUMBER}|[xX*])(?:\.({NUMBER}|[xX*]))?"
    rf"(?:\.({NUMBER}|[xX*]))?(-{IDENT}(?:\.{IDENT})*)?"
    rf"(?:\+{IDENT}(?:\.{IDENT})*)?"
)
COMPARATOR = re.compile(r"(<=|>=|<|>|=|~>?|\^)?\s*([^\s]+)")
HYPHEN = re.compile(r"^([^\s]+)\s+-\s+([^\s]+)$")


def version_key(version):
    """Order SemVer releases and prereleases, ignoring build metadata."""
    core, separator, prerelease = version.split("+", 1)[0].partition("-")
    identifiers = tuple(
        (0, int(part)) if part.isdecimal() else (1, part)
        for part in prerelease.split(".")
    )
    return tuple(map(int, core.split("."))), not separator, identifiers


def partial(value):
    """Expand a partial version to its floor and count specified parts."""
    match = PARTIAL.fullmatch(value.lstrip("v"))
    if not match:
        raise ValueError(f"unsupported npm version range component: {value}")
    parts = []
    for part in match.groups()[:3]:
        if part is None or part in "xX*":
            break
        parts.append(part)
    count = len(parts)
    parts.extend(["0"] * (3 - count))
    floor = ".".join(parts) + (match[4] or "")
    if not VERSION.fullmatch(floor):
        raise ValueError(f"invalid version in range: {value}")
    return version_key(floor), count


def next_boundary(floor, position):
    """Create the exclusive upper bound for a numeric prefix."""
    parts = list(floor[0])
    parts[position] += 1
    parts[position + 1:] = [0] * (2 - position)
    return tuple(parts), False, ((0, 0),)


def expand(operator, value):
    """Convert one npm comparator to exact comparisons."""
    floor, count = partial(value)
    if not count:
        if operator in ("<", ">"):
            return [("<", floor)]
        return []
    if operator in ("~", "~>", "^"):
        index = min(count - 1, 1)
        if operator == "^":
            index = next(
                (i for i in range(count) if floor[0][i]), count - 1
            )
        return [(">=", floor), ("<", next_boundary(floor, index))]
    if count == 3:
        return [(operator or "=", floor)]
    ceiling = next_boundary(floor, count - 1)
    return {
        "": [(">=", floor), ("<", ceiling)],
        "=": [(">=", floor), ("<", ceiling)],
        ">": [(">=", ceiling)],
        ">=": [(">=", floor)],
        "<": [("<", (floor[0], False, ((0, 0),)))],
        "<=": [("<", ceiling)],
    }[operator]


def comparator_set(expression):
    """Parse a conjunction or an npm hyphen range."""
    hyphen = HYPHEN.fullmatch(expression)
    if hyphen:
        return expand(">=", hyphen[1]) + expand("<=", hyphen[2])
    comparisons = []
    while expression:
        match = COMPARATOR.match(expression)
        if not match:
            raise ValueError(f"invalid npm version range: {expression}")
        comparisons.extend(expand(match[1] or "", match[2]))
        expression = expression[match.end():].lstrip()
    return comparisons


def matches(key, comparisons):
    """Apply a comparator set and npm's prerelease opt-in rule."""
    from operator import eq, ge, gt, le, lt

    operations = {"=": eq, ">=": ge, ">": gt, "<=": le, "<": lt}
    if not key[1] and not any(
        key[0] == target[0] and not target[1] and operation != "<"
        for operation, target in comparisons
    ):
        return False
    return all(operations[op](key, target) for op, target in comparisons)


def select_version(versions, expression):
    """Return the greatest available version satisfying an npm range."""
    groups = [comparator_set(part.strip()) for part in expression.split("||")]
    candidates = sorted(
        ((version_key(value), value) for value in versions
         if VERSION.fullmatch(value)),
        reverse=True,
    )
    for key, value in candidates:
        if any(matches(key, group) for group in groups):
            return value
    raise ValueError(f"no version satisfies {expression!r}")
