# Minecraft Mapping MCP Server

A FastMCP server for searching Minecraft mappings across different namespaces (Mojang, Yarn).

## Features

- **Automatic Downloads**: Fetches mappings from Mojang and Yarn repositories on-demand
- **Search Tool**: `search_mappings` - Search for classes, methods, and fields
- **Multiple Namespaces**: Support for Mojang (ProGuard) and Yarn (TinyV2) mappings
- **Fuzzy Matching**: Exact match first, then fuzzy search if no results
- **Caching**: File and in-memory caching for fast repeated searches

## Installation

```bash
uv sync
uv pip install -e .
```

## Usage

Run the server:

```bash
uv run python -m mappingmcp
```

Or with MCP Inspector for testing:

```bash
npx @modelcontextprotocol/inspector uv run python -m mappingmcp
```

## Tool: search_mappings

Search for Minecraft mappings with automatic download.

**Parameters:**
- `query` (string, required): Class, method, or field name to search
- `version` (string, required): Minecraft version (e.g., "1.20.4", "1.21")
- `namespace` (string, default: "mojang"): "mojang" or "yarn"
- `limit` (int, default: 10, max: 100): Maximum results

**Example:**
```json
{
  "query": "Block",
  "version": "1.21",
  "namespace": "mojang",
  "limit": 5
}
```

## How It Works

1. First request downloads mappings from official sources
2. Mappings are cached in `~/.cache/mappingmcp/`
3. Subsequent requests use cached data
4. Search uses exact matching first, then fuzzy matching

## Architecture

- `download.py`: Downloads from Mojang/Yarn repositories
- `mappings.py`: TinyV2 (Yarn) and ProGuard (Mojang) parsers
- `server.py`: FastMCP server with search_mappings tool

## Data Sources

- **Mojang**: https://piston-meta.mojangapis.com/
- **Yarn**: https://maven.fabricmc.net/net/fabricmc/yarn
