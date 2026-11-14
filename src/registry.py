"""Read versioned npm package metadata over HTTP."""

import json
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .version import select_version


def dependency_target(name, spec):
    """Return the package name and version range behind an npm alias."""
    if not spec.startswith("npm:"):
        return name, spec
    target = spec.removeprefix("npm:")
    name, separator, alias_spec = target.rpartition("@")
    if not separator or not name:
        return target, "*"
    return name, alias_spec


class NpmRegistry:
    """Retrieve and cache package documents from an npm registry."""

    def __init__(self, url):
        self.url = url.rstrip("/")
        self.documents = {}

    def document(self, name):
        """Fetch the packument for a package, including scoped names."""
        if name not in self.documents:
            self.documents[name] = self.fetch(name)
        return self.documents[name]

    def fetch(self, name):
        """Decode a registry JSON response."""
        request = Request(
            f"{self.url}/{quote(name, safe='@')}",
            headers={"Accept": "application/vnd.npm.install-v1+json"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                data = json.load(response)
        except (OSError, URLError, ValueError) as error:
            raise ValueError(f"cannot load {name}: {error}") from error
        if not isinstance(data, dict):
            raise ValueError(f"invalid registry metadata for {name}")
        return data

    def dependencies(self, package):
        """Return runtime dependency declarations for an exact version."""
        name, version = package
        versions = self.document(name).get("versions", {})
        if version not in versions:
            raise ValueError(f"version not found: {name}@{version}")
        metadata = versions[version]
        dependencies = metadata.get("dependencies", {})
        optional = metadata.get("optionalDependencies", {})
        return dependencies | optional

    def neighbors(self, package, exclude=None):
        """Resolve each declared dependency against registry versions."""
        for name, spec in sorted(self.dependencies(package).items()):
            if exclude is not None and exclude in name:
                continue
            name, spec = dependency_target(name, spec)
            if exclude is not None and exclude in name:
                continue
            yield name, self.resolve_version(name, spec)

    def resolve_version(self, name, spec):
        """Resolve a registry tag or select a version matching a range."""
        document = self.document(name)
        tags = document.get("dist-tags", {})
        try:
            return tags.get(spec) or select_version(
                document.get("versions", {}), spec
            )
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
