"""Mapping parsers and containers for Minecraft mappings."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from difflib import SequenceMatcher


@dataclass
class MappingEntry:
    """Base class for mapping entries."""
    obf_name: Optional[str]
    intermediary_name: str
    mapped_name: Optional[str]


@dataclass
class FieldMapping(MappingEntry):
    """Field mapping entry."""
    descriptor: Optional[str] = None


@dataclass
class MethodMapping(MappingEntry):
    """Method mapping entry."""
    descriptor: str = ""
    parameters: List[str] = field(default_factory=list)


@dataclass
class ClassMapping(MappingEntry):
    """Class mapping entry with members."""
    methods: Dict[str, MethodMapping] = field(default_factory=dict)
    fields: Dict[str, FieldMapping] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result with score."""
    entry: MappingEntry
    owner: Optional[ClassMapping]
    score: float
    fuzzy: bool


class MappingContainer:
    """Container for storing and searching mappings."""
    
    def __init__(self):
        self.classes: Dict[str, ClassMapping] = {}
        # Index for fast searching
        self._class_index: Dict[str, ClassMapping] = {}
        self._method_index: Dict[str, List[tuple[ClassMapping, MethodMapping]]] = {}  
        self._field_index: Dict[str, List[tuple[ClassMapping, FieldMapping]]] = {}
        
    def add_class(self, cls: ClassMapping):
        """Add a class to the container and build indexes."""
        self.classes[cls.intermediary_name] = cls
        
        # Index by all names (full path and simple name)
        for name in [cls.obf_name, cls.intermediary_name, cls.mapped_name]:
            if name:
                # Full path
                self._class_index[name.lower()] = cls
                # Simple name (after last /)
                simple = name.split("/")[-1].lower()
                if simple and simple != name.lower():
                    self._class_index[simple] = cls
            
        # Index methods
        for method in cls.methods.values():
            for name in [method.obf_name, method.intermediary_name, method.mapped_name]:
                if name:
                    key = name.lower()
                    if key not in self._method_index:
                        self._method_index[key] = []
                    self._method_index[key].append((cls, method))
                    
        # Index fields
        for fld in cls.fields.values():
            for name in [fld.obf_name, fld.intermediary_name, fld.mapped_name]:
                if name:
                    key = name.lower()
                    if key not in self._field_index:
                        self._field_index[key] = []
                    self._field_index[key].append((cls, fld))

    
    def search(self, query: str, limit: int = 100) -> tuple[List[SearchResult], bool]:
        """Search mappings with exact then fuzzy matching."""
        query_lower = query.lower().replace(".", "/")
        results: List[SearchResult] = []
        
        # Exact match
        # Classes
        if query_lower in self._class_index:
            results.append(SearchResult(
                entry=self._class_index[query_lower],
                owner=None,
                score=1.0,
                fuzzy=False
            ))
            
        # Methods
        if query_lower in self._method_index:
            for cls, method in self._method_index[query_lower]:
                results.append(SearchResult(
                   entry=method,
                    owner=cls,
                    score=1.0,
                    fuzzy=False
                ))
                
        # Fields
        if query_lower in self._field_index:
            for cls, fld in self._field_index[query_lower]:
                results.append(SearchResult(
                    entry=fld,
                    owner=cls,
                    score=1.0,
                    fuzzy=False
                ))
        
        if results:
            return results[:limit], False
            
        # Fuzzy match
        fuzzy_results: List[SearchResult] = []
        
        # Fuzzy class search
        for name, cls in self._class_index.items():
            ratio = SequenceMatcher(None, query_lower, name).ratio()
            if ratio > 0.6:
                fuzzy_results.append(SearchResult(
                    entry=cls,
                    owner=None,
                    score=ratio,
                    fuzzy=True
                ))
                
        # Fuzzy method search  
        for name, entries in self._method_index.items():
            ratio = SequenceMatcher(None, query_lower, name).ratio()
            if ratio > 0.6:
                for cls, method in entries:
                    fuzzy_results.append(SearchResult(
                        entry=method,
                        owner=cls,
                        score=ratio,
                        fuzzy=True
                    ))
                    
        # Fuzzy field search
        for name, entries in self._field_index.items():
            ratio = SequenceMatcher(None, query_lower, name).ratio()
            if ratio > 0.6:
                for cls, fld in entries:
                    fuzzy_results.append(SearchResult(
                        entry=fld,
                        owner=cls,
                        score=ratio,
                        fuzzy=True
                    ))
        
        # Sort by score
        fuzzy_results.sort(key=lambda x: x.score, reverse=True)
        return fuzzy_results[:limit], True


class MappingProvider(ABC):
    """Abstract mapping provider."""
    
    @abstractmethod
    def parse(self, content: str) -> MappingContainer:
        """Parse mapping content into a container."""
        pass


class TinyV2Provider(MappingProvider):
    """Parser for TinyV2 format (Yarn mappings)."""
    
    def parse(self, content: str) -> MappingContainer:
        """Parse TinyV2 content."""
        container = MappingContainer()
        lines = content.strip().split("\n")
        
        if not lines or not lines[0].startswith("tiny"):
            raise ValueError("Invalid TinyV2 format")
            
        # Parse header: tiny\t2\t0\t<namespace1>\t<namespace2>\t...
        header = lines[0].split("\t")
        namespaces = header[3:]  # Skip "tiny", version, minor
        num_namespaces = len(namespaces)
        
        # Find namespace indices
        intermediary_idx = namespaces.index("intermediary") if "intermediary" in namespaces else 0
        named_idx = namespaces.index("named") if "named" in namespaces else -1
        official_idx = namespaces.index("official") if "official" in namespaces else -1
        
        current_class: Optional[ClassMapping] = None
        
        for line in lines[1:]:
            if not line.strip():
                continue
                
            # Count leading tabs for indentation level
            indent = 0
            for ch in line:
                if ch == '\t':
                    indent += 1
                else:
                    break
                    
            parts = line.strip().split("\t")
            
            if indent == 0 and len(parts) > 0 and parts[0] == "c":
                # Class: c\t<name1>\t<name2>...
                names = parts[1:]  # All names after 'c'
                
                obf_name = names[official_idx] if official_idx >= 0 and len(names) > official_idx else None
                intermediary_name = names[intermediary_idx] if intermediary_idx >= 0 and len(names) > intermediary_idx else names[0]
                mapped_name = names[named_idx] if named_idx >= 0 and len(names) > named_idx else None
                
                current_class = ClassMapping(
                    obf_name=obf_name,
                    intermediary_name=intermediary_name,
                    mapped_name=mapped_name
                )
                container.add_class(current_class)
                
            elif indent == 1 and current_class and len(parts) > 0:
                if parts[0] == "m":
                    # Method: m\tdescriptor\t<name1>\t<name2>...
                    descriptor = parts[1] if len(parts) > 1 else ""
                    names = parts[2:]  # Names after 'm' and descriptor
                    
                    obf_name = names[official_idx] if official_idx >= 0 and len(names) > official_idx else None
                    intermediary_name = names[intermediary_idx] if intermediary_idx >= 0 and len(names) > intermediary_idx else (names[0] if names else "")
                    mapped_name = names[named_idx] if named_idx >= 0 and len(names) > named_idx else None
                    
                    method = MethodMapping(
                        descriptor=descriptor,
                        obf_name=obf_name,
                        intermediary_name=intermediary_name,
                        mapped_name=mapped_name
                    )
                    current_class.methods[method.intermediary_name] = method
                    
                elif parts[0] == "f":
                    # Field: f\tdescriptor\t<name1>\t<name2>...
                    descriptor = parts[1] if len(parts) > 1 else None
                    names = parts[2:]  # Names after 'f' and descriptor
                    
                    obf_name = names[official_idx] if official_idx >= 0 and len(names) > official_idx else None
                    intermediary_name = names[intermediary_idx] if intermediary_idx >= 0 and len(names) > intermediary_idx else (names[0] if names else "")
                    mapped_name = names[named_idx] if named_idx >= 0 and len(names) > named_idx else None
                    
                    fld = FieldMapping(
                        descriptor=descriptor,
                        obf_name=obf_name,
                        intermediary_name=intermediary_name,
                        mapped_name=mapped_name
                    )
                    current_class.fields[fld.intermediary_name] = fld
                    
        return container



class ProGuardProvider(MappingProvider):
    """Parser for ProGuard format (Mojang mappings)."""
    
    def parse(self, content: str) -> MappingContainer:
        """Parse ProGuard mappings.txt content."""
        container = MappingContainer()
        lines = content.strip().split("\n")
        
        current_class: Optional[ClassMapping] = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            # Class line: obf.Class -> mapped.Class:
            if " -> " in line and line.endswith(":"):
                parts = line[:-1].split(" -> ")
                obf_name = parts[0].strip().replace(".", "/")
                mapped_name = parts[1].strip().replace(".", "/")
                
                current_class = ClassMapping(
                    obf_name=obf_name,
                    intermediary_name=obf_name,  # Mojang doesn't have intermediary
                    mapped_name=mapped_name
                )
                container.add_class(current_class)
                
            # Member line (indented)
            elif current_class and line.startswith("    "):
                member_line = line.strip()
                if " -> " in member_line:
                    # Format: returnType obfName(params) -> mappedName
                    # or: fieldType obfName -> mappedName
                    parts = member_line.split(" -> ")
                    mapped_name = parts[1].strip()
                    left = parts[0].strip()
                    
                    if "(" in left:
                        # Method
                        method_parts = left.split("(")
                        obf_name = method_parts[0].split()[-1]
                        params_str = method_parts[1].rstrip(")")
                        
                        method = MethodMapping(
                            obf_name=obf_name,
                            intermediary_name=obf_name,
                            mapped_name=mapped_name,
                            descriptor="",  # ProGuard doesn't include JVM descriptors
                            parameters=params_str.split(",") if params_str else []
                        )
                        current_class.methods[obf_name] = method
                    else:
                        # Field
                        obf_name = left.split()[-1]
                        fld = FieldMapping(
                            obf_name=obf_name,
                            intermediary_name=obf_name,
                            mapped_name=mapped_name
                        )
                        current_class.fields[obf_name] = fld
                        
        return container
