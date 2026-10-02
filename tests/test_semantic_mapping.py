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
