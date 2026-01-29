from fastmcp import FastMCP
from pathlib import Path
import json
from typing import Optional
from .mappings import MappingContainer, TinyV2Provider, ProGuardProvider, SearchResult, ClassMapping, MethodMapping, FieldMapping
from .download import MappingDownloader

mcp = FastMCP("Mapping MCP")

# Cache directory
CACHE_DIR = Path.home() / ".cache" / "mappingmcp"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory cache
_mapping_cache: dict[str, MappingContainer] = {}

# Downloader instance
_downloader = MappingDownloader(CACHE_DIR)


def get_cache_path(namespace: str, version: str) -> Path:
    """Get cache file path for namespace and version."""
    return CACHE_DIR / f"{namespace}_{version}.json"


def format_result(result: SearchResult) -> dict:
    """Format a search result for MCP response."""
    entry = result.entry
    
    if isinstance(entry, ClassMapping):
        return {
            "type": "class",
            "obf_name": entry.obf_name,
            "intermediary": entry.intermediary_name,
            "mapped": entry.mapped_name,
            "score": result.score,
            "fuzzy": result.fuzzy
        }
    elif isinstance(entry, MethodMapping):
        return {
            "type": "method",
            "obf_name": entry.obf_name,
            "intermediary": entry.intermediary_name,
            "mapped": entry.mapped_name,
            "descriptor": entry.descriptor,
            "owner_obf": result.owner.obf_name if result.owner else None,
            "owner_intermediary": result.owner.intermediary_name if result.owner else None,
            "owner_mapped": result.owner.mapped_name if result.owner else None,
            "score": result.score,
            "fuzzy": result.fuzzy
        }
    elif isinstance(entry, FieldMapping):
        return {
            "type": "field",
            "obf_name": entry.obf_name,
            "intermediary": entry.intermediary_name,
            "mapped": entry.mapped_name,
            "descriptor": entry.descriptor,
            "owner_obf": result.owner.obf_name if result.owner else None,
            "owner_intermediary": result.owner.intermediary_name if result.owner else None,
            "owner_mapped": result.owner.mapped_name if result.owner else None,
            "score": result.score,
            "fuzzy": result.fuzzy
        }
    return {}


@mcp.tool()
def search_mappings(
    query: str,
    version: str,
    namespace: str = "mojang",
    limit: int = 10
) -> str:
    """Search for Minecraft mappings across different namespaces.
    
    Args:
        query: The class, method, or field name to search for
        version: Minecraft version (e.g., "1.20.4", "1.21")
        namespace: Mapping namespace - "mojang" or "yarn" (default: "mojang")
        limit: Maximum number of results to return (default: 10, max: 100)
    
    Returns:
        JSON string containing search results with mappings information
    """
    # Validate inputs
    if limit < 1 or limit > 100:
        return json.dumps({"error": "Limit must be between 1 and 100"})
    
    if namespace not in ["mojang", "yarn"]:
        return json.dumps({"error": f"Invalid namespace '{namespace}'. Must be 'mojang' or 'yarn'"})
    
    cache_key = f"{namespace}_{version}"
    
    # Check if mappings are already in memory
    if cache_key not in _mapping_cache:
        # Download mappings
        if namespace == "mojang":
            content = _downloader.download_mojang_mappings(version)
            if not content:
                return json.dumps({
                    "error": "Failed to download Mojang mappings",
                    "message": f"Could not find or download Mojang mappings for version {version}",
                    "suggestion": "Check that the version exists and is a valid Minecraft version"
                })
            provider = ProGuardProvider()
        else:  # yarn
            content = _downloader.download_yarn_mappings(version)
            if not content:
                return json.dumps({
                    "error": "Failed to download Yarn mappings",
                    "message": f"Could not find or download Yarn mappings for version {version}",
                    "suggestion": "Check that the version exists and has Yarn mappings available"
                })
            provider = TinyV2Provider()
        
        # Parse mappings
        try:
            container = provider.parse(content)
            _mapping_cache[cache_key] = container
        except Exception as e:
            return json.dumps({
                "error": "Failed to parse mappings",
                "message": str(e)
            })
    
    # Get container from cache
    container = _mapping_cache[cache_key]
    
    # Perform search
    results, fuzzy = container.search(query, limit=limit)
    
    # Format results
    formatted_results = [format_result(r) for r in results]
    
    return json.dumps({
        "query": query,
        "version": version,
        "namespace": namespace,
        "fuzzy": fuzzy,
        "results": formatted_results,
        "total": len(formatted_results)
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
