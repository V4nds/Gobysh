"""
Repository Scanner for Gobysh v5.1.
Deterministically scans source files and directories using standard Python ast
and lightweight regex tokenizers for JavaScript/TypeScript.
"""

import ast
import os
import re
from typing import List, Optional

from .symbol_mapper import FileSymbolMap, Symbol, SymbolMap


class RepositoryScanner:
    """Scanner for turning source code into structured FileSymbolMap and SymbolMap."""

    @classmethod
    def scan_file(cls, file_path: str, content: Optional[str] = None) -> FileSymbolMap:
        """Scan a single file from path or provided string content."""
        norm_path = file_path.replace("\\", "/")
        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                return FileSymbolMap(file_path=norm_path)

        if norm_path.endswith(".py"):
            return cls._scan_python(norm_path, content)
        elif norm_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            return cls._scan_javascript(norm_path, content)
        else:
            return FileSymbolMap(file_path=norm_path)

    @classmethod
    def _scan_python(cls, file_path: str, code: str) -> FileSymbolMap:
        symbols: List[Symbol] = []
        imports: List[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return FileSymbolMap(file_path=file_path)

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}" if mod else alias.name)
            elif isinstance(node, ast.ClassDef):
                cls_doc = ast.get_docstring(node) or ""
                symbols.append(
                    Symbol(
                        name=node.name,
                        kind="class",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        docstring=cls_doc,
                    )
                )
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_doc = ast.get_docstring(item) or ""
                        params = [a.arg for a in item.args.args]
                        symbols.append(
                            Symbol(
                                name=f"{node.name}.{item.name}",
                                kind="method",
                                file_path=file_path,
                                line_start=item.lineno,
                                line_end=getattr(item, "end_lineno", item.lineno),
                                docstring=m_doc,
                                parameters=params,
                            )
                        )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                f_doc = ast.get_docstring(node) or ""
                params = [a.arg for a in node.args.args]
                symbols.append(
                    Symbol(
                        name=node.name,
                        kind="function",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        docstring=f_doc,
                        parameters=params,
                    )
                )

        return FileSymbolMap(file_path=file_path, symbols=symbols, imports=imports)

    @classmethod
    def _scan_javascript(cls, file_path: str, code: str) -> FileSymbolMap:
        symbols: List[Symbol] = []
        imports: List[str] = []

        # Imports: import ... from 'mod'; or require('mod')
        import_matches = re.finditer(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))""", code)
        for m in import_matches:
            mod = m.group(1) or m.group(2)
            if mod:
                imports.append(mod)

        # Functions: function foo(...) or const foo = (...) =>
        fn_matches = re.finditer(r"""(?:function\s+([a-zA-Z0-9_$]+)\s*\(|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)""", code)
        for m in fn_matches:
            fname = m.group(1) or m.group(2)
            if fname:
                lineno = code[:m.start()].count("\n") + 1
                symbols.append(
                    Symbol(name=fname, kind="function", file_path=file_path, line_start=lineno)
                )

        # Classes: class Foo
        cls_matches = re.finditer(r"""class\s+([a-zA-Z0-9_$]+)""", code)
        for m in cls_matches:
            cname = m.group(1)
            lineno = code[:m.start()].count("\n") + 1
            symbols.append(
                Symbol(name=cname, kind="class", file_path=file_path, line_start=lineno)
            )

        return FileSymbolMap(file_path=file_path, symbols=symbols, imports=imports)

    @classmethod
    def scan_directory(cls, dir_path: str, max_files: int = 100) -> SymbolMap:
        """Scan a directory for supported source files."""
        sym_map = SymbolMap()
        count = 0
        exts = (".py", ".js", ".jsx", ".ts", ".tsx")

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "node_modules", "__pycache__", ".kilo")]
            for f in sorted(files):
                if f.endswith(exts):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, dir_path).replace("\\", "/")
                    fmap = cls.scan_file(full_p)
                    fmap.file_path = rel_p
                    for s in fmap.symbols:
                        s.file_path = rel_p
                    sym_map.add_file(fmap)
                    count += 1
                    if count >= max_files:
                        return sym_map

        return sym_map
