# Stage 3: Semantic Code Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Stage 3 Semantic Code Mapping from `GOBYSH_ARCHITECTURE_CALIBRATION_SPEC.md`: build `SymbolMap`, `RepositoryScanner`, `DependencyGraph`, and `CodeSemanticMapper` in `core/translation/` and `core/semantics/`, linking user semantic entities to concrete AST symbols, files, and dependencies without external heavy packages.

**Architecture:**
1. `core/translation/symbol_mapper.py`: `Symbol`, `FileSymbolMap`, and `SymbolMap` data structures.
2. `core/translation/scanner.py`: `RepositoryScanner` extracting symbols, imports, and definitions from Python (`ast`) and JS/TS (lightweight structural regex tokenizer).
3. `core/semantics/dependency_graph.py`: `DependencyGraph` supporting impact analysis (`get_impact_radius`, `find_affected_protected_symbols`).
4. `core/translation/engine.py`: `CodeSemanticMapper` connecting `SemanticIR` requirements to concrete file/symbol targets.
5. Integration & verification gate across test suites and `goby gate`.

**Tech Stack:** Python 3.8+ (`ast`, `pathlib`, `re`, `dataclasses`, `typing`, standard library only).

## Global Constraints

- **Preservation First:** Do NOT break or modify existing public APIs in `core/intent_resolver.py`, `core/semantics/`, or `core/ccr_engine.py`.
- **Pure Python Standard Library:** Use `ast` for Python AST parsing and fast deterministic token regexes for JS/TS; no node/npm or tree-sitter requirements.
- **Fail-Safe Gate:** All 223 existing unit tests must continue to pass (`python -m unittest discover tests/`) and `goby gate` must remain at 0 unresolved errors.

---

### Task 1: Symbol & File-to-Symbol Mapping (`core/translation/symbol_mapper.py`)

**Files:**
- Create: `core/translation/__init__.py`
- Create: `core/translation/symbol_mapper.py`
- Test: `tests/test_semantic_mapping.py`

**Interfaces:**
- Produces: `Symbol`, `FileSymbolMap`, `SymbolMap` in `core/translation/symbol_mapper.py`:
  - `Symbol(name: str, kind: str, file_path: str, line_start: int, line_end: int, docstring: str, parameters: List[str])`
  - `FileSymbolMap(file_path: str, symbols: List[Symbol], imports: List[str])`
  - `SymbolMap(files: Dict[str, FileSymbolMap])`:
    - `find_symbol(name: str) -> List[Symbol]`
    - `get_file_symbols(file_path: str) -> List[Symbol]`
    - `all_symbols() -> List[Symbol]`
    - `to_dict() -> Dict[str, Any]`

- [ ] **Step 1: Write failing test for Symbol and SymbolMap**

Create `tests/test_semantic_mapping.py`:

```python
"""Tests for Stage 3 Semantic Code Mapping (Goby Calibration)."""

import unittest
from core.translation.symbol_mapper import Symbol, FileSymbolMap, SymbolMap


class TestSymbolMapper(unittest.TestCase):
    """Test suite for Symbol, FileSymbolMap, and SymbolMap."""

    def test_symbol_creation_and_dict(self):
        sym = Symbol(
            name="IntentResolver.resolve",
            kind="method",
            file_path="core/intent_resolver.py",
            line_start=150,
            line_end=220,
            docstring="Resolves user intent.",
            parameters=["self", "user_input"],
        )
        self.assertEqual(sym.name, "IntentResolver.resolve")
        self.assertEqual(sym.kind, "method")
        d = sym.to_dict()
        self.assertEqual(d["name"], "IntentResolver.resolve")
        self.assertEqual(d["line_start"], 150)

    def test_symbol_map_querying(self):
        s1 = Symbol("login", "function", "auth.py", 10, 30)
        s2 = Symbol("logout", "function", "auth.py", 35, 50)
        s3 = Symbol("login", "function", "api.py", 5, 20)

        f_auth = FileSymbolMap(file_path="auth.py", symbols=[s1, s2], imports=["jwt", "db"])
        f_api = FileSymbolMap(file_path="api.py", symbols=[s3], imports=["auth"])

        sym_map = SymbolMap(files={"auth.py": f_auth, "api.py": f_api})

        matches = sym_map.find_symbol("login")
        self.assertEqual(len(matches), 2)
        self.assertIn(s1, matches)
        self.assertIn(s3, matches)

        auth_syms = sym_map.get_file_symbols("auth.py")
        self.assertEqual(len(auth_syms), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.translation'`

- [ ] **Step 3: Implement Symbol, FileSymbolMap, and SymbolMap**

Create `core/translation/__init__.py`:

```python
"""
Goby Translation & Code Mapping Layer v5.1.0
Maps high-level semantic intent and constraints into concrete files, symbols, and dependencies.
"""

from .symbol_mapper import Symbol, FileSymbolMap, SymbolMap

__all__ = ["Symbol", "FileSymbolMap", "SymbolMap"]
```

Create `core/translation/symbol_mapper.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/translation/__init__.py core/translation/symbol_mapper.py tests/test_semantic_mapping.py
git commit -m "feat(translation): add Symbol, FileSymbolMap, and SymbolMap models"
```

---

### Task 2: Repository Scanner (`core/translation/scanner.py`)

**Files:**
- Create: `core/translation/scanner.py`
- Modify: `core/translation/__init__.py`
- Modify: `tests/test_semantic_mapping.py`

**Interfaces:**
- Produces: `RepositoryScanner` in `core/translation/scanner.py`:
  - `RepositoryScanner.scan_file(file_path: str, content: Optional[str]) -> FileSymbolMap`
  - `RepositoryScanner.scan_directory(dir_path: str, max_files: int) -> SymbolMap`

- [ ] **Step 1: Write failing test for RepositoryScanner**

Append to `tests/test_semantic_mapping.py`:

```python
from core.translation.scanner import RepositoryScanner


class TestRepositoryScanner(unittest.TestCase):
    """Test suite for RepositoryScanner parsing Python and JS/TS code."""

    def test_scan_python_content(self):
        py_code = """
import os
from math import sqrt

class Calculator:
    \"\"\"Performs basic calculations.\"\"\"
    def add(self, a, b):
        return a + b

def multiply(x, y):
    \"\"\"Multiplies two numbers.\"\"\"
    return x * y
"""
        fmap = RepositoryScanner.scan_file("calc.py", content=py_code)
        self.assertEqual(fmap.file_path, "calc.py")
        self.assertIn("os", fmap.imports)
        self.assertIn("math.sqrt", fmap.imports)

        names = [s.name for s in fmap.symbols]
        self.assertIn("Calculator", names)
        self.assertIn("Calculator.add", names)
        self.assertIn("multiply", names)

    def test_scan_javascript_content(self):
        js_code = """
import { useState } from 'react';
const API_URL = "http://localhost:3000";

function authenticateUser(username, password) {
    return true;
}

class SessionManager {
    logout() {
        console.log("Logged out");
    }
}
"""
        fmap = RepositoryScanner.scan_file("auth.js", content=js_code)
        self.assertEqual(fmap.file_path, "auth.js")
        self.assertIn("react", fmap.imports)
        names = [s.name for s in fmap.symbols]
        self.assertIn("authenticateUser", names)
        self.assertIn("SessionManager", names)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.translation.scanner'`

- [ ] **Step 3: Implement RepositoryScanner**

Create `core/translation/scanner.py`:

```python
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
```

Update `core/translation/__init__.py` to export `RepositoryScanner`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/translation/scanner.py core/translation/__init__.py tests/test_semantic_mapping.py
git commit -m "feat(translation): add RepositoryScanner for Python and JS/TS parsing"
```

---

### Task 3: Causal Dependency Graph (`core/semantics/dependency_graph.py`)

**Files:**
- Create: `core/semantics/dependency_graph.py`
- Modify: `core/semantics/__init__.py`
- Modify: `tests/test_semantic_mapping.py`

**Interfaces:**
- Produces: `DependencyGraph` in `core/semantics/dependency_graph.py`:
  - `DependencyGraph.build_from_symbol_map(sym_map: SymbolMap) -> DependencyGraph`
  - `DependencyGraph.get_downstream_dependents(file_path: str) -> List[str]`
  - `DependencyGraph.find_affected_protected_symbols(target_files: List[str], protected_symbols: List[str]) -> List[str]`

- [ ] **Step 1: Write failing test for DependencyGraph**

Append to `tests/test_semantic_mapping.py`:

```python
from core.semantics.dependency_graph import DependencyGraph


class TestDependencyGraph(unittest.TestCase):
    """Test suite for DependencyGraph and impact analysis."""

    def test_build_and_query_dependents(self):
        f1 = FileSymbolMap("core/auth.py", symbols=[Symbol("login", "function", "core/auth.py")], imports=[])
        f2 = FileSymbolMap("core/api.py", symbols=[Symbol("api_endpoint", "function", "core/api.py")], imports=["core/auth.py"])
        f3 = FileSymbolMap("core/cli.py", symbols=[Symbol("main", "function", "core/cli.py")], imports=["core/api.py"])

        sym_map = SymbolMap({"core/auth.py": f1, "core/api.py": f2, "core/cli.py": f3})

        dg = DependencyGraph.build_from_symbol_map(sym_map)
        downstream = dg.get_downstream_dependents("core/auth.py")
        self.assertIn("core/api.py", downstream)
        self.assertIn("core/cli.py", downstream)

    def test_find_affected_protected_symbols(self):
        f1 = FileSymbolMap("core/db.py", symbols=[Symbol("UserModel", "class", "core/db.py")], imports=[])
        f2 = FileSymbolMap("core/service.py", symbols=[Symbol("get_user", "function", "core/service.py")], imports=["core/db.py"])
        sym_map = SymbolMap({"core/db.py": f1, "core/service.py": f2})

        dg = DependencyGraph.build_from_symbol_map(sym_map)
        affected = dg.find_affected_protected_symbols(
            target_files=["core/db.py"],
            protected_symbols=["UserModel"],
        )
        self.assertIn("UserModel", affected)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.semantics.dependency_graph'`

- [ ] **Step 3: Implement DependencyGraph**

Create `core/semantics/dependency_graph.py`:

```python
"""
Causal Dependency Graph (CDG) for Gobysh v5.1.
Enables repository impact analysis, upstream/downstream tracking, and protected symbol checking.
"""

from collections import defaultdict, deque
from typing import Dict, List, Set

from core.translation.symbol_mapper import SymbolMap


class DependencyGraph:
    """Directed dependency graph representing file and symbol relationships."""

    def __init__(self):
        self.upstream: Dict[str, Set[str]] = defaultdict(set)    # file -> files it imports
        self.downstream: Dict[str, Set[str]] = defaultdict(set)  # file -> files that import it
        self.file_symbols: Dict[str, Set[str]] = defaultdict(set) # file -> symbol names

    @classmethod
    def build_from_symbol_map(cls, sym_map: SymbolMap) -> "DependencyGraph":
        graph = cls()

        for file_path, fmap in sym_map.files.items():
            norm_file = file_path.replace("\\", "/").strip("./").strip("/")
            for s in fmap.symbols:
                graph.file_symbols[norm_file].add(s.name)

            for imp in fmap.imports:
                norm_imp = imp.replace("\\", "/").replace(".", "/").strip("./").strip("/")
                # Match imported module to registered file path
                for target_path in sym_map.files:
                    norm_target = target_path.replace("\\", "/").strip("./").strip("/")
                    if norm_imp in norm_target or norm_target.startswith(norm_imp):
                        if norm_file != norm_target:
                            graph.upstream[norm_file].add(norm_target)
                            graph.downstream[norm_target].add(norm_file)

        return graph

    def get_downstream_dependents(self, file_path: str) -> List[str]:
        """Compute all files that transitively depend on file_path."""
        norm_file = file_path.replace("\\", "/").strip("./").strip("/")
        visited: Set[str] = set()
        queue = deque([norm_file])

        while queue:
            curr = queue.popleft()
            for dep in self.downstream.get(curr, []):
                if dep not in visited and dep != norm_file:
                    visited.add(dep)
                    queue.append(dep)

        return sorted(list(visited))

    def find_affected_protected_symbols(
        self,
        target_files: List[str],
        protected_symbols: List[str],
    ) -> List[str]:
        """Check if modifying target_files touches or impacts any protected symbols."""
        affected: List[str] = []
        if not protected_symbols:
            return affected

        # All files directly modified or transitively affected
        all_touched_files: Set[str] = set()
        for tf in target_files:
            norm_tf = tf.replace("\\", "/").strip("./").strip("/")
            all_touched_files.add(norm_tf)
            all_touched_files.update(self.get_downstream_dependents(norm_tf))

        # Check symbol definitions in touched files
        for f in all_touched_files:
            defined_syms = self.file_symbols.get(f, set())
            for ps in protected_symbols:
                if ps in defined_syms or any(ps.lower() in s.lower() for s in defined_syms):
                    if ps not in affected:
                        affected.append(ps)

        return affected
```

Update `core/semantics/__init__.py` to export `DependencyGraph`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/semantics/dependency_graph.py core/semantics/__init__.py tests/test_semantic_mapping.py
git commit -m "feat(semantics): add DependencyGraph for repository impact analysis"
```

---

### Task 4: Code-Semantic Mapper (`core/translation/engine.py`)

**Files:**
- Create: `core/translation/engine.py`
- Modify: `core/translation/__init__.py`
- Modify: `tests/test_semantic_mapping.py`

**Interfaces:**
- Produces: `MappingReport`, `CodeSemanticMapper` in `core/translation/engine.py`:
  - `CodeSemanticMapper.map_contract(semantic_ir: SemanticIR, sym_map: SymbolMap, dep_graph: Optional[DependencyGraph]) -> MappingReport`
  - `MappingReport(resolved_targets, mapped_requirements, unmapped_requirements, affected_protected_symbols)`

- [ ] **Step 1: Write failing test for CodeSemanticMapper**

Append to `tests/test_semantic_mapping.py`:

```python
from core.translation.engine import CodeSemanticMapper
from core.semantics.intermediate_representation import SemanticIR
from core.semantics.specification import SemanticSpecification, Requirement
from core.semantics.constraints import ConstraintModel


class TestCodeSemanticMapper(unittest.TestCase):
    """Test suite for CodeSemanticMapper."""

    def test_map_contract_to_existing_symbols(self):
        fmap = FileSymbolMap("core/auth.py", symbols=[Symbol("login_flow", "function", "core/auth.py")])
        sym_map = SymbolMap({"core/auth.py": fmap})
        dg = DependencyGraph.build_from_symbol_map(sym_map)

        req1 = Requirement("R1", "add registration flow", target_entities=["auth.py"])
        req2 = Requirement("R2", "new unknown feature", target_entities=["unknown_module"])

        spec = SemanticSpecification(id="S1", requirements=[req1, req2])
        ir = SemanticIR(specification=spec, constraints=ConstraintModel(protected_symbols=["login_flow"]))

        mapper = CodeSemanticMapper()
        report = mapper.map_contract(ir, sym_map, dg)

        self.assertIn("core/auth.py", report.resolved_targets)
        self.assertEqual(len(report.mapped_requirements), 1)
        self.assertEqual(len(report.unmapped_requirements), 1)
        self.assertEqual(report.unmapped_requirements[0].id, "R2")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.translation.engine'`

- [ ] **Step 3: Implement CodeSemanticMapper**

Create `core/translation/engine.py`:

```python
"""
Code-Semantic Mapping Engine for Gobysh v5.1.
Bridges formal SemanticIR requirements and repository code structures (files, symbols, and dependencies).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.semantics.dependency_graph import DependencyGraph
from core.semantics.intermediate_representation import SemanticIR
from core.semantics.specification import Requirement
from .symbol_mapper import Symbol, SymbolMap


@dataclass
class MappingReport:
    """Result of mapping a SemanticIR against repository codebase."""
    resolved_targets: List[str] = field(default_factory=list)
    mapped_requirements: List[Requirement] = field(default_factory=list)
    unmapped_requirements: List[Requirement] = field(default_factory=list)
    target_to_symbols: Dict[str, List[Symbol]] = field(default_factory=dict)
    affected_protected_symbols: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "resolved_targets": self.resolved_targets,
            "mapped_requirements": [r.id for r in self.mapped_requirements],
            "unmapped_requirements": [r.id for r in self.unmapped_requirements],
            "affected_protected_symbols": self.affected_protected_symbols,
        }


class CodeSemanticMapper:
    """Translates high-level semantic requirements into concrete code targets."""

    def map_contract(
        self,
        semantic_ir: SemanticIR,
        sym_map: SymbolMap,
        dep_graph: Optional[DependencyGraph] = None,
    ) -> MappingReport:
        resolved_targets: List[str] = []
        mapped_reqs: List[Requirement] = []
        unmapped_reqs: List[Requirement] = []
        target_to_symbols: Dict[str, List[Symbol]] = {}

        # 1. Resolve requirement targets against symbol map
        for req in semantic_ir.specification.requirements:
            req_mapped = False
            for target in req.target_entities:
                norm_t = target.replace("\\", "/").strip("./").strip("/")
                matched_file = None

                # Check if target matches a file
                for fp in sym_map.files:
                    norm_fp = fp.replace("\\", "/").strip("./").strip("/")
                    if norm_t == norm_fp or norm_fp.endswith(norm_t) or norm_t in norm_fp:
                        matched_file = fp
                        break

                if matched_file:
                    if matched_file not in resolved_targets:
                        resolved_targets.append(matched_file)
                    req_mapped = True
                    target_to_symbols[matched_file] = sym_map.get_file_symbols(matched_file)
                else:
                    # Check if target matches a symbol directly
                    syms = sym_map.find_symbol(target)
                    if syms:
                        req_mapped = True
                        for s in syms:
                            if s.file_path not in resolved_targets:
                                resolved_targets.append(s.file_path)
                            target_to_symbols.setdefault(s.file_path, []).append(s)

            if req_mapped:
                req.status = "MAPPED"
                mapped_reqs.append(req)
            else:
                req.status = "UNMAPPED"
                unmapped_reqs.append(req)

        # 2. Check affected protected symbols via DependencyGraph
        affected_protected = []
        if dep_graph and semantic_ir.constraints.protected_symbols:
            affected_protected = dep_graph.find_affected_protected_symbols(
                target_files=resolved_targets,
                protected_symbols=semantic_ir.constraints.protected_symbols,
            )

        return MappingReport(
            resolved_targets=resolved_targets,
            mapped_requirements=mapped_reqs,
            unmapped_requirements=unmapped_reqs,
            target_to_symbols=target_to_symbols,
            affected_protected_symbols=affected_protected,
        )
```

Update `core/translation/__init__.py` to export `CodeSemanticMapper` and `MappingReport`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest tests/test_semantic_mapping.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/translation/engine.py core/translation/__init__.py tests/test_semantic_mapping.py
git commit -m "feat(translation): add CodeSemanticMapper for linking requirements to code symbols"
```

---

### Task 5: Integration, CLI Verification, and Completion Gate

**Files:**
- Modify: `core/intent_resolver.py` (enrich entities and mapped files when repository context exists)
- Run: Full test suite (`python -m unittest discover tests/`)
- Run: `goby gate`

- [ ] **Step 1: Run full unit test suite**

Run: `.venv\Scripts\python.exe -m unittest discover tests/`
Expected: PASS (All tests pass including Stage 1, Stage 2, and Stage 3 suites)

- [ ] **Step 2: Run Goby Gate check**

Run: `goby gate`
Expected: Exit code 0 (`[GOBY GATE] Ledger clean: 0 unresolved file errors. Workspace ready.`)

- [ ] **Step 3: Commit and finalize**

```bash
git add core/intent_resolver.py
git commit -m "feat(intent): enrich semantic intent resolution with Stage 3 code mapping"
```
