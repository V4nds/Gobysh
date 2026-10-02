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


if __name__ == "__main__":
    unittest.main()


