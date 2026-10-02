"""
Scope Normalizer for Gobysh v5.1.
Enforces strict file and directory boundaries, cross-platform path normalization,
and glob matching.
"""

import fnmatch
from typing import List


class ScopeNormalizer:
    """Utilities for path and scope validation."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path across OS boundaries (POSIX style, stripped)."""
        if not path:
            return ""
        norm = path.strip().replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        norm = norm.strip("/")
        return norm

    @classmethod
    def is_in_scope(cls, file_path: str, scope_patterns: List[str]) -> bool:
        """Check if file_path matches any allowed scope pattern."""
        if not scope_patterns:
            return True  # Unrestricted scope

        norm_file = cls.normalize_path(file_path)

        for pat in scope_patterns:
            norm_pat = cls.normalize_path(pat)
            if not norm_pat:
                continue

            # Exact match
            if norm_file == norm_pat:
                return True

            # Directory prefix match (e.g. "core" matches "core/cli.py")
            if norm_file.startswith(norm_pat + "/"):
                return True

            # Glob pattern match
            if any(char in norm_pat for char in "*?[]"):
                if fnmatch.fnmatch(norm_file, norm_pat):
                    return True
                # Support ** globbing
                if "**" in norm_pat:
                    import re
                    regex_pat = re.escape(norm_pat).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
                    if re.match(f"^{regex_pat}$", norm_file):
                        return True

        return False

    @classmethod
    def validate_file_targets(cls, targets: List[str], allowed_scopes: List[str]) -> List[str]:
        """Return list of error messages for any targets outside allowed scopes."""
        if not allowed_scopes:
            return []
        violations = []
        for target in targets:
            if not cls.is_in_scope(target, allowed_scopes):
                violations.append(
                    f"SCOPE_VIOLATION: Target '{target}' is outside allowed scope: {allowed_scopes}"
                )
        return violations
