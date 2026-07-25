"""
CLI Entrypoint for Goby Framework.
Run using: goby audit | goby benchmark | goby check <code>
"""

import sys
import unittest
from .ccr_engine import CognitiveControlRoom


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Goby Framework CLI v1.3.0")
        print("Usage:")
        print("  goby audit        Run full test suite verification")
        print("  goby benchmark    Run empirical benchmark simulation")
        print("  goby check <code> Validate python snippet via CCR")
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "audit":
        print("🔍 Running Goby Empirical Verification Audit...")
        suite = unittest.defaultTestLoader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    elif cmd == "benchmark":
        print("📈 Running Goby Benchmark Simulation...")
        from tests import benchmark_simulation
        benchmark_simulation.run_all_benchmarks()
        sys.exit(0)

    elif cmd == "check":
        if len(args) < 2:
            print("Error: Please provide code string to check. Example: goby check 'x = 1'")
            sys.exit(1)
        code = args[1]
        ccr = CognitiveControlRoom()
        sig = ccr.neuron_syntax_check(code)
        print(f"Neuron SYNTAX: passed={sig.passed}, msg='{sig.message}'")
        sys.exit(0 if sig.passed else 1)

    else:
        print(f"Unknown command: '{cmd}'. Run 'goby --help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
