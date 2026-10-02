"""
Symbol and File-to-Symbol Mapping for Gobysh v5.1.
Enables bidirectional translation between semantic requirements and concrete code entities.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Symbol:
    """An individual code symbol (function, class, method, or constant)."""
    name: str
    kind: str  # function | class | method | variable
    file_path: str
    line_start: int = 1
    line_end: int = 1
    docstring: str = ""
    parameters: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Symbol":
        return cls(
            name=data.get("name", ""),
            kind=data.get("kind", "function"),
            file_path=data.get("file_path", ""),
            line_start=data.get("line_start", 1),
            line_end=data.get("line_end", 1),
            docstring=data.get("docstring", ""),
            parameters=list(data.get("parameters", [])),
        )


@dataclass
class FileSymbolMap:
    """All symbols and imports discovered within a single source file."""
    file_path: str
    symbols: List[Symbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": self.imports,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileSymbolMap":
        syms = [
            Symbol.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("symbols", [])
        ]
        return cls(
            file_path=data.get("file_path", ""),
            symbols=syms,
            imports=list(data.get("imports", [])),
        )


class SymbolMap:
    """Global symbol table aggregating symbols across all repository files."""

    def __init__(self, files: Optional[Dict[str, FileSymbolMap]] = None):
        self.files: Dict[str, FileSymbolMap] = files or {}

    def add_file(self, file_map: FileSymbolMap) -> None:
        self.files[file_map.file_path] = file_map

    def find_symbol(self, name: str) -> List[Symbol]:
        """Find symbols matching name (exact or substring)."""
        matches = []
        name_lower = name.lower()
        for fmap in self.files.values():
            for sym in fmap.symbols:
                if sym.name == name or sym.name.lower() == name_lower:
                    matches.append(sym)
                elif name_lower in sym.name.lower():
                    matches.append(sym)
        return matches

    def get_file_symbols(self, file_path: str) -> List[Symbol]:
        norm = file_path.replace("\\", "/").strip("./").strip("/")
        for fp, fmap in self.files.items():
            norm_fp = fp.replace("\\", "/").strip("./").strip("/")
            if norm_fp == norm:
                return fmap.symbols
        return []

    def all_symbols(self) -> List[Symbol]:
        all_syms = []
        for fmap in self.files.values():
            all_syms.extend(fmap.symbols)
        return all_syms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": {fp: fmap.to_dict() for fp, fmap in self.files.items()}
        }
