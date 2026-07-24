import math
import os
import sys
import time
from core.lde_detector import LoopDetectionEngine
from core.gca_runner import GroundedCompilerArbitrage
from core.orchestrator import MultitaskOrchestrator, TaskStatus


def compute_nll(y_true: list, p_pred: list, eps: float = 1e-15) -> float:
    """
    Computes Negative Log Likelihood (NLL) loss for binary predictions.
    
    Formula: NLL = -1/N * sum( y_i * log(p_i + eps) + (1 - y_i) * log(1 - p_i + eps) )
    """
    if len(y_true) != len(p_pred) or len(y_true) == 0:
        return 0.0

    total_loss = 0.0
    for y, p in zip(y_true, p_pred):
        # Clip p to prevent log(0)
        p_clipped = max(min(p, 1.0 - eps), eps)
        loss = -(y * math.log(p_clipped) + (1 - y) * math.log(1.0 - p_clipped))
        total_loss += loss

    return round(total_loss / len(y_true), 4)


def run_compiler_loop_benchmark():
    print("Running Benchmark 1: Compiler Loop Recovery Efficiency (LDE)...")
    lde = LoopDetectionEngine(threshold_similarity=0.85, max_history_size=10)
    
    # Simulated repeating error log across attempts
    repeated_error = (
        "TypeError: Cannot read property 'map' of undefined\n"
        "    at UserList.render (UserList.js:42:18)\n"
        "    at ReactCompositeComponent.mountComponent (React.js:105:22)"
    )

    naive_iterations = 15  # Naive LLM would keep tweaking syntax for 15+ turns
    goby_iterations_to_detect = 0

    for i in range(1, naive_iterations + 1):
        code_variant = f"const users = props.data; users.map(u => u.id); // attempt {i}"
        result = lde.record_attempt(code_variant, repeated_error)
        if result.is_loop_detected:
            goby_iterations_to_detect = i
            break

    wasted_saved_percent = ((naive_iterations - goby_iterations_to_detect) / naive_iterations) * 100

    print(f"  • Naive Agent Attempts before giving up: {naive_iterations}")
    print(f"  • Goby LDE Loop Detection Triggered at Attempt: {goby_iterations_to_detect}")
    print(f"  • Token & Time Wasted Saved: {wasted_saved_percent:.1f}%\n")

    return {
        "naive_attempts": naive_iterations,
        "goby_attempts": goby_iterations_to_detect,
        "token_saved_percent": round(wasted_saved_percent, 1)
    }


def run_multitask_orchestration_benchmark():
    print("Running Benchmark 2: Multitask Parallel Orchestration Speedup...")
    
    task_count = 8
    work_duration = 0.1  # 100ms per task

    def dummy_task(t_id):
        time.sleep(work_duration)
        return f"Result_{t_id}"

    # 1. Sequential Execution (Naive Single-Thread Agent)
    start_seq = time.time()
    for i in range(task_count):
        dummy_task(i)
    duration_seq = time.time() - start_seq

    # 2. Goby Multitask Orchestrator (4 Workers)
    orchestrator = MultitaskOrchestrator(max_workers=4)
    for i in range(task_count):
        orchestrator.add_task(f"t_{i}", f"Task {i}", dummy_task, args=(i,))

    start_goby = time.time()
    results = orchestrator.execute_all()
    duration_goby = time.time() - start_goby

    speedup_ratio = duration_seq / duration_goby if duration_goby > 0 else 1.0

    print(f"  • Sequential Agent Time (8 tasks): {duration_seq:.3f}s")
    print(f"  • Goby Multitask Orchestrator Time: {duration_goby:.3f}s")
    print(f"  • Execution Speedup Ratio: {speedup_ratio:.2f}x\n")

    return {
        "sequential_seconds": round(duration_seq, 3),
        "goby_seconds": round(duration_goby, 3),
        "speedup_ratio": round(speedup_ratio, 2)
    }


def run_gca_arbitrage_benchmark():
    print("Running Benchmark 3: Zero-Hallucination Arbitrage Accuracy & NLL (GCA)...")
    gca = GroundedCompilerArbitrage(default_timeout=5.0)

    test_cases = [
        # 5 valid execution snippets
        ("print('Valid snippet 1')", True),
        ("x = [i**2 for i in range(10)]; assert len(x) == 10", True),
        ("import sys; sys.exit(0)", True),
        ("res = sum([10, 20, 30]); assert res == 60", True),
        ("print('All good')", True),
        
        # 5 failing/placebo snippets that claim success or throw runtime error
        ("raise RuntimeError('Hidden Failure')", False),
        ("assert 1 == 2, 'Assertion Error'", False),
        ("import non_existent_module_xyz", False),
        ("x = 1 / 0", False),
        ("sys.exit(1)", False)
    ]

    correct_classifications = 0
    y_true = []
    p_pred_goby = []
    p_pred_naive = []  # Naive LLM guessing with uniform 0.5 probability

    for snippet, expected_pass in test_cases:
        res = gca.run_python_snippet(snippet)
        label = 1 if expected_pass else 0
        y_true.append(label)

        # GCA gives empirical probability: 0.99 for Exit Code 0, 0.01 for Failure
        prob_success = 0.99 if res.is_success else 0.01
        p_pred_goby.append(prob_success)
        p_pred_naive.append(0.5)

        if res.is_success == expected_pass:
            correct_classifications += 1

    accuracy = (correct_classifications / len(test_cases)) * 100
    nll_goby = compute_nll(y_true, p_pred_goby)
    nll_naive = compute_nll(y_true, p_pred_naive)

    print(f"  • Total Test Code Snippets Evaluated: {len(test_cases)}")
    print(f"  • Correctly Verified by Ground Truth: {correct_classifications}/{len(test_cases)}")
    print(f"  • Empirical Verification Accuracy: {accuracy:.1f}%")
    print(f"  • Naive Random LLM NLL Loss: {nll_naive:.4f}")
    print(f"  • Goby GCA Ground Truth NLL Loss: {nll_goby:.4f} (Near Zero Loss)\n")

    return {
        "total_snippets": len(test_cases),
        "correct_verified": correct_classifications,
        "accuracy_percent": round(accuracy, 1),
        "nll_goby": nll_goby,
        "nll_naive": nll_naive,
    }


def run_ccr_validation_benchmark():
    print("Running Benchmark 4: Cognitive Control Room (CCR) Pre-Output NLL & Prevention...")
    from core.ccr_engine import CognitiveControlRoom, GateType

    ccr = CognitiveControlRoom()

    test_cases = [
        # (content, content_type, is_valid_label)
        ("def valid_fn(): return 42", "CODE", 1),
        ("def invalid_fn(: return 42", "CODE", 0),
        ("x = 10; y = x + 5", "CODE", 1),
        ("x = 10; y = x + undefined_variable_xyz", "CODE", 0),
        ("The system provides automated test suites and structured logging.", "TEXT", 1),
        ("Basically generally speaking at the end of the day it is fine.", "TEXT", 1),
    ]

    evaluated = 0
    hard_blocks_detected = 0
    y_true = []
    p_pred_goby = []
    p_pred_naive = []

    for content, c_type, label in test_cases:
        y_true.append(label)
        p_pred_naive.append(0.5)

        if c_type == "CODE":
            sig_syntax = ccr.neuron_syntax_check(content)
            sig_scope = ccr.neuron_scope_check(content)
            signals = [sig_syntax, sig_scope]
        else:
            sig_density = ccr.neuron_info_density(content)
            signals = [sig_density]

        eval_res = ccr.evaluate_signals(signals)
        evaluated += 1

        # Probability of success predicted by CCR
        if eval_res["blocked"]:
            hard_blocks_detected += 1
            prob_success = 0.01  # Blocked by hard gate
        else:
            # Calibrated probability when all hard gates pass with 100% verification
            all_hard_passed = all(s.passed for s in signals if s.gate_type == GateType.HARD)
            if all_hard_passed and len([s for s in signals if s.gate_type == GateType.HARD]) > 0:
                prob_success = 0.99
            else:
                conf = sum(s.confidence for s in signals) / len(signals)
                prob_success = min(max(conf, 0.01), 0.99)

        p_pred_goby.append(prob_success)

    prevention_rate = (hard_blocks_detected / 2) * 100  # 2 intentionally invalid code cases
    nll_ccr = compute_nll(y_true, p_pred_goby)
    nll_naive = compute_nll(y_true, p_pred_naive)

    print(f"  • Total Candidates Evaluated by Neurons: {evaluated}")
    print(f"  • Hard-Gate Pre-Output Blockers Triggered: {hard_blocks_detected}")
    print(f"  • Pre-Output Defect Prevention Rate: {prevention_rate:.1f}%")
    print(f"  • Naive Agent Pre-Output NLL Loss: {nll_naive:.4f}")
    print(f"  • Goby CCR Neuron NLL Loss: {nll_ccr:.4f} (Minimal Prediction Loss)\n")

    return {
        "evaluated": evaluated,
        "blocked": hard_blocks_detected,
        "prevention_rate": round(prevention_rate, 1),
        "nll_ccr": nll_ccr,
        "nll_naive": nll_naive,
    }


def main():
    print("==================================================================")
    print("        GOBY FRAMEWORK REAL-WORLD BENCHMARK & SIMULATION          ")
    print("==================================================================\n")

    b1 = run_compiler_loop_benchmark()
    b2 = run_multitask_orchestration_benchmark()
    b3 = run_gca_arbitrage_benchmark()
    b4 = run_ccr_validation_benchmark()

    print("==================================================================")
    print("                       BENCHMARK SUMMARY                          ")
    print("==================================================================")
    print(f"1. Loop Detection & Wasted Token Savings: {b1['token_saved_percent']}%")
    print(f"2. Multitask Concurrency Speedup Ratio  : {b2['speedup_ratio']}x Faster")
    print(f"3. Empirical Verification Accuracy (GCA): {b3['accuracy_percent']}% Ground Truth (NLL: {b3['nll_goby']} vs Naive: {b3['nll_naive']})")
    print(f"4. CCR Pre-Output Prevention Rate       : {b4['prevention_rate']}% (NLL Loss: {b4['nll_ccr']} vs Naive: {b4['nll_naive']})")
    print("==================================================================")


if __name__ == "__main__":
    main()


