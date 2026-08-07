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
        print("Goby Framework CLI v4.0.0 (Omni-Synthesis)")
        print("Usage:")
        print("  goby audit        Run full test suite verification")
        print("  goby benchmark    Run empirical benchmark simulation")
        print("  goby evolve       Run autonomous self-evolution cycle (BFM metric)")
        print("  goby check <code> Validate python snippet via CCR")
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "evolve":
        print("[EVOLUTION] Running Goby v4.0 Omni-Synthesis Evolution Benchmark...")
        from .evolution_loop import SelfEvolutionEngine
        engine = SelfEvolutionEngine()
        result = engine.run_evolution_cycle()
        print(f"  -> Total Benchmarks: {result['total_benchmarks']}")
        print(f"  -> Caught Apriori:   {result['caught_apriori']}")
        print(f"  -> Bypasses Needed:  {result['bypasses_needed']}")
        print(f"  -> BFM Metric:       {result['bypass_frequency_metric']}")
        print(f"  -> Status:           {result['status']}")
        sys.exit(0 if result['status'] == "ZERO_BYPASS_ACHIEVED" else 1)


    if cmd == "audit":
        print("[AUDIT] Running Goby Empirical Verification Audit...")
        suite = unittest.defaultTestLoader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    elif cmd == "benchmark":
        print("[BENCHMARK] Running Goby Benchmark Simulation...")
        from tests import benchmark_simulation
        benchmark_simulation.main()
        sys.exit(0)

    elif cmd == "check":
        if len(args) < 2:
            print("Error: Please provide code string to check. Example: goby check 'x = 1'")
            sys.exit(1)
        code = args[1]
        ccr = CognitiveControlRoom()
        
        signals = []
        syn = ccr.neuron_syntax_check(code)
        signals.append(syn)
        if syn.passed:
            signals.append(ccr.neuron_scope_check(code))
            signals.append(ccr.neuron_taste_design_check(code))
            
        res = ccr.evaluate_signals(signals)
        
        for sig in signals:
            print(f"[{sig.neuron_name}] {'PASS' if sig.passed else 'FAIL'} (Gate: {sig.gate_type.value}) - {sig.message}")
            
        if res["blocked"]:
            print(f"\n[BLOCKED] {res['summary']}")
            sys.exit(1)
        else:
            print("\n[SUCCESS] Code passed all hard gates.")
            sys.exit(0)

    else:
        print(f"Unknown command: '{cmd}'. Run 'goby --help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
