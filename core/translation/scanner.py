"""
Repository Scanner for Gobysh v5.1.
Deterministically scans source files and directories using standard Python ast
and lightweight regex tokenizers for JavaScript/TypeScript and Kotlin.
"""

import ast
import json
import os
import re
import shutil
import subprocess
from typing import List, Optional

from .symbol_mapper import FileSymbolMap, Symbol, SymbolMap


class RepositoryScanner:
    """Scanner for turning source code into structured FileSymbolMap and SymbolMap."""

    @classmethod
    def _get_native_binary(cls) -> Optional[str]:
        """Locates the compiled goby_core native accelerator binary if present."""
        env_bin = os.getenv("GOBY_CORE_BIN")
        if env_bin and os.path.isfile(env_bin):
            return env_bin

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidates = [
            os.path.join(repo_root, "crates", "goby_core", "target", "release", "goby_core.exe"),
            os.path.join(repo_root, "crates", "goby_core", "target", "release", "goby_core"),
            os.path.join(repo_root, "crates", "goby_core", "target", "debug", "goby_core.exe"),
            os.path.join(repo_root, "crates", "goby_core", "target", "debug", "goby_core"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c

        return shutil.which("goby-core") or shutil.which("goby_core")

    @classmethod
    def scan_file(cls, file_path: str, content: Optional[str] = None, use_native: bool = True) -> FileSymbolMap:
        """Scan a single file from path or provided string content."""
        norm_path = file_path.replace("\\", "/")
        if content is None and use_native and os.path.isfile(file_path):
            native_bin = cls._get_native_binary()
            if native_bin:
                try:
                    proc = subprocess.run(
                        [native_bin, "scan-file", file_path],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=5,
                    )
                    data = json.loads(proc.stdout)
                    return FileSymbolMap.from_dict(data)
                except Exception:
                    pass

        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                return FileSymbolMap(file_path=norm_path)

        if norm_path.endswith((".py", ".pyw")):
            return cls._scan_python(norm_path, content)
        elif norm_path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            return cls._scan_javascript(norm_path, content)
        elif norm_path.endswith((".kt", ".kts")):
            return cls._scan_kotlin(norm_path, content)
        elif norm_path.endswith(".rs"):
            return cls._scan_rust(norm_path, content)
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

        import_matches = re.finditer(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))""", code)
        for m in import_matches:
            mod = m.group(1) or m.group(2)
            if mod:
                imports.append(mod)

        fn_matches = re.finditer(r"""(?:function\s+([a-zA-Z0-9_$]+)\s*\(|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)""", code)
        for m in fn_matches:
            fname = m.group(1) or m.group(2)
            if fname:
                lineno = code[:m.start()].count("\n") + 1
                symbols.append(
                    Symbol(name=fname, kind="function", file_path=file_path, line_start=lineno)
                )

        cls_matches = re.finditer(r"""class\s+([a-zA-Z0-9_$]+)""", code)
        for m in cls_matches:
            cname = m.group(1)
            lineno = code[:m.start()].count("\n") + 1
            symbols.append(
                Symbol(name=cname, kind="class", file_path=file_path, line_start=lineno)
            )

        return FileSymbolMap(file_path=file_path, symbols=symbols, imports=imports)

    @classmethod
    def _scan_kotlin(cls, file_path: str, code: str) -> FileSymbolMap:
        symbols: List[Symbol] = []
        imports: List[str] = []

        # Strip comments so words inside comments are not mistaken for declarations
        code_without_comments = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), code, flags=re.DOTALL)
        code_without_comments = re.sub(r"//.*", "", code_without_comments)

        # Imports: import package.name.Class
        import_matches = re.finditer(r"""^\s*import\s+([a-zA-Z0-9_.*]+)""", code_without_comments, re.MULTILINE)
        for m in import_matches:
            mod = m.group(1).strip()
            if mod:
                imports.append(mod)

        # Classes, Interfaces, Objects, Enums
        cls_matches = re.finditer(r"""\b(?:data\s+class|enum\s+class|sealed\s+class|sealed\s+interface|class|interface|object)\s+([a-zA-Z0-9_]+)""", code_without_comments)
        for m in cls_matches:
            cname = m.group(1)
            lineno = code[:m.start()].count("\n") + 1
            symbols.append(
                Symbol(name=cname, kind="class", file_path=file_path, line_start=lineno)
            )

        # Functions & Methods
        fn_matches = re.finditer(r"""\b(?:fun|suspend\s+fun|override\s+fun)\s+(?:<[^>]+>\s+)?([a-zA-Z0-9_]+)\s*\(""", code_without_comments)
        for m in fn_matches:
            fname = m.group(1)
            lineno = code[:m.start()].count("\n") + 1
            symbols.append(
                Symbol(name=fname, kind="function", file_path=file_path, line_start=lineno)
            )

        return FileSymbolMap(file_path=file_path, symbols=symbols, imports=imports)

    @classmethod
    def _scan_rust(cls, file_path: str, code: str) -> FileSymbolMap:
        symbols: List[Symbol] = []
        imports: List[str] = []

        import_matches = re.finditer(r"(?m)^\s*use\s+([^;]+);", code)
        for m in import_matches:
            imports.append(m.group(1).strip())

        type_matches = re.finditer(r"\b(?:pub\s+)?(?:struct|enum|trait|type)\s+([a-zA-Z0-9_]+)", code)
        for m in type_matches:
            cname = m.group(1)
            lineno = code[:m.start()].count("\n") + 1
            symbols.append(Symbol(name=cname, kind="class", file_path=file_path, line_start=lineno))

        fn_matches = re.finditer(r"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*(?:<[^>]*>)?\s*\(", code)
        for m in fn_matches:
            fname = m.group(1)
            lineno = code[:m.start()].count("\n") + 1
            symbols.append(Symbol(name=fname, kind="function", file_path=file_path, line_start=lineno))

        return FileSymbolMap(file_path=file_path, symbols=symbols, imports=imports)

    @classmethod
    def scan_directory(cls, dir_path: str, max_files: int = 500, use_native: bool = True) -> SymbolMap:
        """Scan a directory for supported source files with optional native Rust acceleration."""
        if use_native:
            native_bin = cls._get_native_binary()
            if native_bin:
                try:
                    proc = subprocess.run(
                        [native_bin, "scan", dir_path, "--max-files", str(max_files)],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10,
                    )
                    data = json.loads(proc.stdout)
                    sym_map = SymbolMap()
                    for fp, f_dict in data.get("files", {}).items():
                        sym_map.add_file(FileSymbolMap.from_dict(f_dict))
                    return sym_map
                except Exception:
                    # Fallback to Python scanning
                    pass

        sym_map = SymbolMap()
        count = 0
        exts = (".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".kt", ".kts", ".rs")
        ignored_dirs = {
            ".git", ".venv", "node_modules", "__pycache__", ".kilo",
            "build", ".gradle", "gradle", ".idea", "dist", "out", "bin", "target"
        }

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for f in sorted(files):
                if f.endswith(exts):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, dir_path).replace("\\", "/")
                    fmap = cls.scan_file(full_p, use_native=False)
                    fmap.file_path = rel_p
                    for s in fmap.symbols:
                        s.file_path = rel_p
                    sym_map.add_file(fmap)
                    count += 1
                    if count >= max_files:
                        return sym_map

        return sym_map
