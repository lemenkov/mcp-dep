# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Peter Lemenkov <lemenkov@gmail.com>

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("dep")

HEADERS = {"User-Agent": "mcp-dep/0.1 (https://github.com/lemenkov/mcp-dep)"}


def _get(url: str) -> dict[str, Any] | None:
    """Simple synchronous HTTP GET returning parsed JSON or None."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True}, tags={"read"})
def hex_package(name: str) -> dict[str, Any]:
    """Get package metadata from Hex.pm (Elixir/Erlang packages).

    Args:
        name: Package name (e.g. 'phoenix', 'ecto', 'plug')
    """
    data = _get(f"https://hex.pm/api/packages/{name}")
    if not data:
        return {"error": f"Package '{name}' not found on Hex.pm"}

    latest = data.get("latest_stable_version") or data.get("latest_version", "unknown")
    releases = [r["version"] for r in data.get("releases", [])[:5]]

    return {
        "name": data.get("name"),
        "latest_version": latest,
        "recent_versions": releases,
        "description": data.get("meta", {}).get("description"),
        "licenses": data.get("meta", {}).get("licenses", []),
        "links": data.get("meta", {}).get("links", {}),
        "downloads": data.get("downloads", {}).get("all"),
        "url": f"https://hex.pm/packages/{name}",
    }


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True}, tags={"read"})
def pypi_package(name: str) -> dict[str, Any]:
    """Get package metadata from PyPI (Python packages).

    Args:
        name: Package name (e.g. 'fastmcp', 'requests', 'django')
    """
    data = _get(f"https://pypi.org/pypi/{name}/json")
    if not data:
        return {"error": f"Package '{name}' not found on PyPI"}

    info = data.get("info", {})
    releases = sorted(data.get("releases", {}).keys())[-5:]

    return {
        "name": info.get("name"),
        "latest_version": info.get("version"),
        "recent_versions": list(reversed(releases)),
        "description": info.get("summary"),
        "license": info.get("license"),
        "requires_python": info.get("requires_python"),
        "home_page": info.get("home_page") or info.get("project_url"),
        "url": f"https://pypi.org/project/{name}/",
    }


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True}, tags={"read"})
def rubygems_package(name: str) -> dict[str, Any]:
    """Get package metadata from RubyGems (Ruby packages).

    Args:
        name: Gem name (e.g. 'rails', 'sinatra', 'rspec')
    """
    data = _get(f"https://rubygems.org/api/v1/gems/{name}.json")
    if not data:
        return {"error": f"Gem '{name}' not found on RubyGems"}

    return {
        "name": data.get("name"),
        "latest_version": data.get("version"),
        "description": data.get("info"),
        "licenses": data.get("licenses", []),
        "homepage_uri": data.get("homepage_uri"),
        "source_code_uri": data.get("source_code_uri"),
        "downloads": data.get("downloads"),
        "url": f"https://rubygems.org/gems/{name}",
    }


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True}, tags={"read"})
def npm_package(name: str) -> dict[str, Any]:
    """Get package metadata from NPM (JavaScript/Node.js packages).

    Args:
        name: Package name (e.g. 'react', 'express', 'typescript')
        Use '@scope/name' for scoped packages (e.g. '@modelcontextprotocol/sdk')
    """
    # Use abbreviated metadata endpoint — much lighter than /latest
    data = _get(f"https://registry.npmjs.org/{name}")
    if not data:
        return {"error": f"Package '{name}' not found on NPM"}

    latest_version = data.get("dist-tags", {}).get("latest", "unknown")
    versions = list(data.get("versions", {}).keys())[-5:]
    latest_info = data.get("versions", {}).get(latest_version, {})

    return {
        "name": data.get("name"),
        "latest_version": latest_version,
        "recent_versions": list(reversed(versions)),
        "description": data.get("description"),
        "license": latest_info.get("license"),
        "engines": latest_info.get("engines", {}),
        "homepage": data.get("homepage"),
        "repository": data.get("repository", {}).get("url")
        if isinstance(data.get("repository"), dict)
        else data.get("repository"),
        "url": f"https://www.npmjs.com/package/{name}",
    }


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True}, tags={"read"})
def crates_package(name: str) -> dict[str, Any]:
    """Get package metadata from crates.io (Rust packages).

    Args:
        name: Crate name (e.g. 'tokio', 'serde', 'axum')
    """
    data = _get(f"https://crates.io/api/v1/crates/{name}")
    if not data:
        return {"error": f"Crate '{name}' not found on crates.io"}

    krate = data.get("crate", {})
    versions = [v["num"] for v in data.get("versions", [])[:5]]

    return {
        "name": krate.get("name"),
        "latest_version": krate.get("newest_version"),
        "recent_versions": versions,
        "description": krate.get("description"),
        "license": data.get("versions", [{}])[0].get("license"),
        "repository": krate.get("repository"),
        "downloads": krate.get("downloads"),
        "url": f"https://crates.io/crates/{name}",
    }


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport="streamable-http", host=host, port=port)
