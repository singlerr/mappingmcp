"""Quick test script for mapping downloads and search."""

from mappingmcp.download import MappingDownloader
from mappingmcp.mappings import ProGuardProvider, TinyV2Provider
from pathlib import Path

def test_mojang():
    print("Testing Mojang mappings download...")
    cache_dir = Path.home() / ".cache" / "mappingmcp"
    downloader = MappingDownloader(cache_dir)
    
    # Try 1.21 (recent version)
    content = downloader.download_mojang_mappings("1.21")
    if content:
        print(f"✓ Downloaded Mojang 1.21 mappings ({len(content)} bytes)")
        
        # Parse and test search
        provider = ProGuardProvider()
        container = provider.parse(content)
        print(f"✓ Parsed {len(container.classes)} classes")
        
        # Search test
        results, fuzzy = container.search("Block", limit=5)
        print(f"✓ Found {len(results)} results for 'Block' (fuzzy={fuzzy})")
        for r in results[:3]:
            print(f"  - {r.entry.mapped_name or r.entry.intermediary_name}")
    else:
        print("✗ Failed to download Mojang mappings")

def test_yarn():
    print("\nTesting Yarn mappings download...")
    cache_dir = Path.home() / ".cache" / "mappingmcp"
    downloader = MappingDownloader(cache_dir)
    
    # Try 1.20.4 (stable version with Yarn)
    content = downloader.download_yarn_mappings("1.20.4")
    if content:
        print(f"✓ Downloaded Yarn 1.20.4 mappings ({len(content)} bytes)")
        
        # Parse and test search
        provider = TinyV2Provider()
        container = provider.parse(content)
        print(f"✓ Parsed {len(container.classes)} classes")
        
        # Search test
        results, fuzzy = container.search("Block", limit=5)
        print(f"✓ Found {len(results)} results for 'Block' (fuzzy={fuzzy})")
        for r in results[:3]:
            print(f"  - {r.entry.mapped_name or r.entry.intermediary_name}")
    else:
        print("✗ Failed to download Yarn mappings")

if __name__ == "__main__":
    test_mojang()
    test_yarn()
