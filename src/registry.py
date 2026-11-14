"""Read versioned npm package metadata over HTTP."""

import json
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


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

    def neighbors(self, package):
        """Resolve each declared dependency against registry versions."""
        from .version import select_version

        for name, spec in sorted(self.dependencies(package).items()):
            if spec.startswith("npm:"):
                name, separator, alias_spec = spec[4:].rpartition("@")
                if not separator or not name:
                    name, alias_spec = spec[4:], "*"
                spec = alias_spec
            document = self.document(name)
            tags = document.get("dist-tags", {})
            try:
                version = tags.get(spec) or select_version(
                    document.get("versions", {}), spec
                )
            except ValueError as error:
                raise ValueError(f"{name}: {error}") from error
            yield name, version
