"""
Causal Dependency Graph (CDG) for Gobysh v5.1.
Enables repository impact analysis, upstream/downstream tracking, and protected symbol checking.
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from core.translation.symbol_mapper import SymbolMap


class DependencyGraph:
    """Directed dependency graph representing file and symbol relationships."""

    def __init__(self):
        self.upstream: Dict[str, Set[str]] = defaultdict(set)    # file -> files it imports
        self.downstream: Dict[str, Set[str]] = defaultdict(set)  # file -> files that import it
        self.file_symbols: Dict[str, Set[str]] = defaultdict(set) # file -> symbol names

    @classmethod
    def build_from_symbol_map(cls, sym_map: "SymbolMap") -> "DependencyGraph":
        graph = cls()

        for file_path, fmap in sym_map.files.items():
            norm_file = file_path.replace("\\", "/").strip("./").strip("/")
            for s in fmap.symbols:
                graph.file_symbols[norm_file].add(s.name)

            for imp in fmap.imports:
                norm_imp = imp.replace("\\", "/").strip().lstrip("./")
                # Remove common extensions for base comparison
                imp_base = norm_imp
                for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
                    if imp_base.endswith(ext):
                        imp_base = imp_base[:-len(ext)]
                        break
                imp_slashes = imp_base.replace(".", "/")

                # Match imported module/path to registered file path
                for target_path in sym_map.files:
                    norm_target = target_path.replace("\\", "/").strip().lstrip("./")
                    target_base = norm_target
                    for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
                        if target_base.endswith(ext):
                            target_base = target_base[:-len(ext)]
                            break

                    matches = (
                        norm_imp == norm_target
                        or imp_base == target_base
                        or imp_slashes == target_base
                        or target_base.endswith("/" + imp_base)
                        or target_base.endswith("/" + imp_slashes)
                    )
                    if matches and norm_file != norm_target:
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
