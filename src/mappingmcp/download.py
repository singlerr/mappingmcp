"""Download manager for Minecraft mappings."""

import httpx
import zipfile
import io
from pathlib import Path
from typing import Optional


class MappingDownloader:
    """Downloads mappings from Mojang and Yarn repositories."""
    
    # Correct URLs based on wagyourtail.xyz and Fabric infrastructure
    MOJANG_MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    FABRIC_META = "https://meta.fabricmc.net/v2/versions/yarn"
    YARN_MAVEN = "https://maven.fabricmc.net/net/fabricmc/yarn"
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def download_mojang_mappings(self, version: str) -> Optional[str]:
        """Download Mojang mappings for a specific version.
        
        Returns the file content as a string, or None if download fails.
        """
        cache_file = self.cache_dir / f"mojang_{version}.txt"
        
        # Return cached if exists
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
            
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                # Get version manifest
                manifest_resp = client.get(self.MOJANG_MANIFEST)
                manifest_resp.raise_for_status()
                manifest = manifest_resp.json()
                
                # Find version
                version_info = None
                for v in manifest.get("versions", []):
                    if v["id"] == version:
                        version_info = v
                        break
                        
                if not version_info:
                    print(f"Version {version} not found in Mojang manifest")
                    return None
                    
                # Get version JSON
                version_resp = client.get(version_info["url"])
                version_resp.raise_for_status()
                version_data = version_resp.json()
                
                # Get mappings URL (try client mappings first, then server)
                downloads = version_data.get("downloads", {})
                mappings_url = None
                if "client_mappings" in downloads:
                    mappings_url = downloads["client_mappings"]["url"]
                elif "server_mappings" in downloads:
                    mappings_url = downloads["server_mappings"]["url"]
                    
                if not mappings_url:
                    print(f"No mappings available for version {version}")
                    return None
                    
                # Download mappings
                mappings_resp = client.get(mappings_url)
                mappings_resp.raise_for_status()
                content = mappings_resp.text
                
                # Cache it
                cache_file.write_text(content, encoding="utf-8")
                return content
                
        except Exception as e:
            print(f"Error downloading Mojang mappings: {e}")
            return None
            
    def download_yarn_mappings(self, version: str) -> Optional[str]:
        """Download Yarn mappings for a specific version.
        
        Returns the file content as a string, or None if download fails.
        """
        cache_file = self.cache_dir / f"yarn_{version}.tiny"
        
        # Return cached if exists
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
            
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                # Get Yarn versions from Fabric meta API
                meta_resp = client.get(f"{self.FABRIC_META}/{version}")
                if meta_resp.status_code != 200:
                    print(f"No Yarn mappings found for MC version {version}")
                    return None
                    
                yarn_versions = meta_resp.json()
                if not yarn_versions:
                    print(f"No Yarn builds available for version {version}")
                    return None
                    
                # Get the latest build (first in list)
                latest_build = yarn_versions[0]
                yarn_version = latest_build["version"]  # e.g. "1.20.4+build.3"
                
                # Download the v2 JAR (contains mappings/mappings.tiny)
                jar_url = f"{self.YARN_MAVEN}/{yarn_version}/yarn-{yarn_version}-v2.jar"
                jar_resp = client.get(jar_url)
                jar_resp.raise_for_status()
                
                # Extract mappings.tiny from the JAR
                with zipfile.ZipFile(io.BytesIO(jar_resp.content)) as zf:
                    with zf.open("mappings/mappings.tiny") as f:
                        content = f.read().decode("utf-8")
                
                # Cache it
                cache_file.write_text(content, encoding="utf-8")
                return content
                
        except Exception as e:
            print(f"Error downloading Yarn mappings: {e}")
            return None
