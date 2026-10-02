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


from core.semantics.intermediate_representation import SemanticEntity
from core.semantics.specification import Requirement
from core.translation.engine import CodeSemanticMapper, MappingReport


class TestCodeSemanticMapper(unittest.TestCase):
    """Test suite for CodeSemanticMapper and MappingReport."""

    def test_map_intent_matching_symbols_and_files(self):
        s1 = Symbol("login", "function", "core/auth.py")
        s2 = Symbol("renderLogin", "function", "ui/login.js")
        s3 = Symbol("api_call", "function", "core/api.py")

        f1 = FileSymbolMap("core/auth.py", symbols=[s1], imports=[])
        f2 = FileSymbolMap("ui/login.js", symbols=[s2], imports=[])
        f3 = FileSymbolMap("core/api.py", symbols=[s3], imports=["core/auth.py"])

        sym_map = SymbolMap({"core/auth.py": f1, "ui/login.js": f2, "core/api.py": f3})
        dg = DependencyGraph.build_from_symbol_map(sym_map)
        mapper = CodeSemanticMapper(sym_map, dg)

        report = mapper.map_query("fix login authentication")

        matched_names = [s.name for s in report.matched_symbols]
        self.assertIn("login", matched_names)
        self.assertIn("renderLogin", matched_names)

        self.assertIn("core/auth.py", report.target_files)
        self.assertIn("ui/login.js", report.target_files)
        self.assertIn("core/api.py", report.impacted_dependents)

    def test_protected_symbol_violation_detection(self):
        s1 = Symbol("UserModel", "class", "core/db.py")
        f1 = FileSymbolMap("core/db.py", symbols=[s1], imports=[])
        sym_map = SymbolMap({"core/db.py": f1})
        dg = DependencyGraph.build_from_symbol_map(sym_map)
        mapper = CodeSemanticMapper(sym_map, dg)

        report = mapper.map_query("modify UserModel schema", protected_symbols=["UserModel"])
        self.assertIn("UserModel", report.protected_symbols_violated)

    def test_map_with_semantic_entities_and_requirements(self):
        s1 = Symbol("process_payment", "function", "core/billing.py")
        f1 = FileSymbolMap("core/billing.py", symbols=[s1], imports=[])
        sym_map = SymbolMap({"core/billing.py": f1})
        dg = DependencyGraph.build_from_symbol_map(sym_map)
        mapper = CodeSemanticMapper(sym_map, dg)

        entities = [SemanticEntity(name="billing", entity_type="module")]
        reqs = [Requirement(id="REQ-01", description="Improve payment processing speed")]
        report = mapper.map_intent(entities=entities, requirements=reqs)

        self.assertIn("core/billing.py", report.target_files)
        self.assertTrue(len(report.matched_symbols) >= 1)

    def test_mapping_report_to_dict(self):
        report = MappingReport(
            matched_symbols=[Symbol("foo", "function", "foo.py")],
            target_files=["foo.py"],
            impacted_dependents=["bar.py"],
            protected_symbols_violated=["foo"],
        )
        d = report.to_dict()
        self.assertIn("matched_symbols", d)
        self.assertIn("target_files", d)
        self.assertEqual(d["target_files"], ["foo.py"])
        self.assertEqual(d["impacted_dependents"], ["bar.py"])


from core.intent_resolver import IntentResolver


class TestIntegrationSemanticMapping(unittest.TestCase):
    """Integration test suite for end-to-end repository mapping."""

    def test_intent_resolver_with_repo_mapping(self):
        resolver = IntentResolver()
        tree = resolver.resolve("modify neuron syntax check in control room", repo_root="core")
        self.assertIsNotNone(tree.code_mapping)
        self.assertIn("code_mapping", tree.to_dict())
        self.assertTrue(len(tree.primary_intent.target_files) >= 1)


if __name__ == "__main__":
    unittest.main()




