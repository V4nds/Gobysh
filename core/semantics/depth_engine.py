"""
Goby v5.3 Depth Engine: Mechanical Architectural Depth & Seam Analyzer.
Translates John Ousterhout's Deep Modules philosophy into deterministic AST metrics.
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class ModuleDepthMetrics:
    module_name: str
    file_path: str
    surface_area: float
    implementation_volume: float
    mdi_score: float
    classification: str  # "DEEP", "BALANCED", "SHALLOW"
    anti_patterns: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

class DepthASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.public_methods: List[ast.FunctionDef] = []
        self.private_methods: List[ast.FunctionDef] = []
        self.exported_globals: List[str] = []
        self.total_statements: int = 0
        self.cyclomatic_complexity: int = 1
        self.pass_through_count: int = 0
        self.anti_patterns: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        is_private = name.startswith("_") and not (name.startswith("__") and name.endswith("__"))
        
        if is_private:
            self.private_methods.append(node)
        else:
            self.public_methods.append(node)
            # Check parameter bloat (> 5 params)
            pos_args = len(node.args.args)
            if pos_args > 0 and node.args.args[0].arg in ("self", "cls"):
                pos_args -= 1
            if pos_args > 5:
                self.anti_patterns.append({
                    "type": "PARAMETER_BLOAT",
                    "symbol": name,
                    "line": node.lineno,
                    "details": f"Function '{name}' accepts {pos_args} parameters (> 5)."
                })

            # Check pass-through delegation
            # Body has exactly 1 statement: return foo.bar(...)
            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                    self.pass_through_count += 1
                    self.anti_patterns.append({
                        "type": "PASS_THROUGH_DELEGATION",
                        "symbol": name,
                        "line": node.lineno,
                        "details": f"Method '{name}' is a pure 1-line pass-through delegate."
                    })

        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_If(self, node: ast.If):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self.cyclomatic_complexity += len(node.handlers)
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST):
        if isinstance(node, ast.stmt):
            self.total_statements += 1
        super().generic_visit(node)

class DepthEngine:
    """Deterministic AST Architectural Depth Calculator."""

    def analyze_source(self, code: str, filename: str = "<memory>") -> ModuleDepthMetrics:
        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError as e:
            return ModuleDepthMetrics(
                module_name=os.path.basename(filename),
                file_path=filename,
                surface_area=1.0,
                implementation_volume=0.0,
                mdi_score=0.0,
                classification="SHALLOW",
                anti_patterns=[{"type": "SYNTAX_ERROR", "details": str(e)}],
                details={"error": str(e)}
            )

        visitor = DepthASTVisitor()
        visitor.visit(tree)

        # 1. Surface Area: public methods + param weight + globals
        pub_count = len(visitor.public_methods)
        param_penalty = 0.0
        for m in visitor.public_methods:
            args_count = len(m.args.args)
            if args_count > 0 and m.args.args[0].arg in ("self", "cls"):
                args_count -= 1
            if args_count > 2:
                param_penalty += (args_count - 2) * 0.5

        surface_area = max(1.0, float(pub_count) + param_penalty)

        # 2. Implementation Volume: statements + CC*1.5 + private_helpers*2.0
        # Pass-through delegators do not provide genuine implementation leverage
        stmt_count = float(visitor.total_statements)
        pass_through_penalty = float(visitor.pass_through_count) * 2.5
        cc_weight = float(visitor.cyclomatic_complexity) * 1.5
        private_weight = float(len(visitor.private_methods)) * 2.0
        impl_volume = max(1.0, (stmt_count - pass_through_penalty) + cc_weight + private_weight)

        # 3. MDI Score: Volume / (Surface + epsilon)
        epsilon = 1.0
        mdi_score = round(impl_volume / (surface_area + epsilon), 2)

        # 4. Classification
        if mdi_score >= 2.5:
            classification = "DEEP"
        elif mdi_score >= 1.2 and visitor.pass_through_count < 2:
            classification = "BALANCED"
        else:
            classification = "SHALLOW"

        return ModuleDepthMetrics(
            module_name=os.path.basename(filename),
            file_path=filename,
            surface_area=round(surface_area, 2),
            implementation_volume=round(impl_volume, 2),
            mdi_score=mdi_score,
            classification=classification,
            anti_patterns=visitor.anti_patterns,
            details={
                "public_methods": pub_count,
                "private_methods": len(visitor.private_methods),
                "total_statements": visitor.total_statements,
                "cyclomatic_complexity": visitor.cyclomatic_complexity,
                "pass_through_count": visitor.pass_through_count
            }
        )

    def analyze_file(self, filepath: str) -> ModuleDepthMetrics:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
        content = path.read_text(encoding="utf-8", errors="replace")
        return self.analyze_source(content, str(path))

    def analyze_directory(self, dirpath: str) -> List[ModuleDepthMetrics]:
        results = []
        path = Path(dirpath)
        for pyfile in path.rglob("*.py"):
            if any(part.startswith(".") or part in ("__pycache__", "build", "dist", "env", "venv") for part in pyfile.parts):
                continue
            try:
                results.append(self.analyze_file(str(pyfile)))
            except Exception:
                continue
        return sorted(results, key=lambda m: m.mdi_score)
