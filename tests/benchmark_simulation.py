"""
Empirical Benchmark & Evaluation Suite for Goby v4.2.0 Framework.
Evaluates 60-Case Static AST Classification Accuracy (TP, TN, FP, FN, Precision, Recall, F1-Score, Latency)
and Reference Workload Parallelism Demonstration.
"""

import math
import os
import sys
import time
from typing import List, Dict, Any
from core.ccr_engine import CognitiveControlRoom
from core.lde_detector import LoopDetectionEngine
from core.gca_runner import GroundedCompilerArbitrage
from core.orchestrator import MultitaskOrchestrator, TaskStatus


def run_ccr_empirical_classification_benchmark():
    print("==========================================================")
    print("  BENCHMARK 1: 60-Case Pre-Output AST Static Classification")
    print("==========================================================")

    ccr = CognitiveControlRoom()

    # 60 Ground Truth Evaluation Cases: (code_snippet, language, expected_is_blocked)
    test_cases = [
        # Category 1: Clean Python (10 Cases -> Expected Blocked: False)
        ("def add(a, b):\n    return a + b", "python", False),
        ("x = 10\ny = 20\nz = x + y", "python", False),
        ("def get_length(arr):\n    return len(arr)", "python", False),
        ("import math\nval = math.sqrt(16)", "python", False),
        ("class Person:\n    def __init__(self, name):\n        self.name = name", "python", False),
        ("data = [i * 2 for i in range(10)]", "python", False),
        ("def greet(name='World'):\n    return f'Hello {name}'", "python", False),
        ("items = {'a': 1, 'b': 2}\nfor k, v in items.items():\n    print(k, v)", "python", False),
        ("try:\n    res = 10 / 2\nexcept ZeroDivisionError:\n    res = 0", "python", False),
        ("def is_even(n):\n    return n % 2 == 0", "python", False),

        # Category 2: Clean JavaScript (10 Cases -> Expected Blocked: False)
        ("const greeting = 'hello'; console.log(greeting);", "javascript", False),
        ("function sum(a, b) { return a + b; }", "javascript", False),
        ("const nums = [1, 2, 3]; const doubled = nums.map(n => n * 2);", "javascript", False),
        ("let x = 5; x += 10; console.log(x);", "javascript", False),
        ("const user = { name: 'Alice', age: 30 };", "javascript", False),
        ("const delay = ms => new Promise(res => setTimeout(res, ms));", "javascript", False),
        ("function isAdult(age) { return age >= 18; }", "javascript", False),
        ("const colors = ['red', 'green', 'blue'];", "javascript", False),
        ("class Animal { constructor(name) { self.name = name; } }", "javascript", False),
        ("const obj = Object.assign({}, { a: 1 });", "javascript", False),

        # Category 3: Clean TypeScript (10 Cases -> Expected Blocked: False)
        ("const val: number = 42; console.log(val);", "typescript", False),
        ("interface User { id: number; name: string; }", "typescript", False),
        ("type Status = 'active' | 'inactive';", "typescript", False),
        ("function getId<T>(arg: T): T { return arg; }", "typescript", False),
        ("const isValid: boolean = true;", "typescript", False),
        ("interface Config { host: string; port: number; }", "typescript", False),
        ("const scores: Array<number> = [90, 85, 95];", "typescript", False),
        ("enum Direction { Up, Down, Left, Right }", "typescript", False),
        ("function logMsg(msg: string): void { console.log(msg); }", "typescript", False),
        ("const identity = <T>(x: T): T => x;", "typescript", False),

        # Category 4: Syntax Errors (10 Cases -> Expected Blocked: True)
        ("def broken_func(\n    return 42", "python", True),
        ("x = [1, 2, 3", "python", True),
        ("if True\n    print('no colon')", "python", True),
        ("class Unclosed:\n    def foo(self)", "python", True),
        ("def bad_indent():\nprint('bad')", "python", True),
        ("const x = ;", "javascript", True),
        ("function badFunc( { return 1; }", "javascript", True),
        ("let y = [1, 2, ;", "javascript", True),
        ("const obj = { a: 1 ", "javascript", True),
        ("interface BadTS { id: number", "typescript", True),

        # Category 5: Undefined Scope Errors (10 Cases -> Expected Blocked: True)
        ("def calc():\n    return missing_var * 10", "python", True),
        ("def process(items):\n    return total_sum / len(items)", "python", True),
        ("def compute():\n    a = 5\n    return a + unassigned_b", "python", True),
        ("def run():\n    return undefined_function()", "python", True),
        ("def calc_tax(price):\n    return price * tax_rate", "python", True),
        ("def get_first():\n    return item_list[0]", "python", True),
        ("def transform():\n    return [x * multiplier for x in data_in]", "python", True),
        ("def execute():\n    status = current_status\n    return status", "python", True),
        ("def checkout():\n    return cart_total - discount_amount", "python", True),
        ("def evaluate_score():\n    return raw_score + bonus_points", "python", True),

        # Category 6: Security Violations (10 Cases -> Expected Blocked: True)
        ("AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLEkey12345'", "python", True),
        ("eval('import os; os.system(\"rm -rf /\")')", "python", True),
        ("PRIVATE_KEY = '-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA0'", "python", True),
        ("DATABASE_PASSWORD = 'super_secret_db_password_12345'", "python", True),
        ("api_token = 'bearer_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'", "python", True),
        ("exec('import subprocess; subprocess.run(\"dir\", shell=True)')", "python", True),
        ("STRIPE_SECRET_KEY = 'sk_test_mock_stripe_secret_key_123456789'", "python", True),
        ("GITHUB_TOKEN = 'ghp_16F2A5D6xB7c8D9e0F1A2B3C4D5E6F7A8B9C'", "python", True),
        ("PASSWORD = 'hardcoded_admin_password'", "python", True),
        ("SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'", "python", True),
    ]

    tp = 0  # True Positive: Expected Blocked, Actual Blocked
    tn = 0  # True Negative: Expected Clean, Actual Clean
    fp = 0  # False Positive: Expected Clean, Actual Blocked
    fn = 0  # False Negative: Expected Blocked, Actual Clean

    latencies = []

    for code, lang, expected_blocked in test_cases:
        t0 = time.time()
        res = ccr.verify_candidate(code, language=lang)
        t_elapsed_ms = (time.time() - t0) * 1000
        latencies.append(t_elapsed_ms)

        actual_blocked = res["blocked"]

        if expected_blocked and actual_blocked:
            tp += 1
        elif not expected_blocked and not actual_blocked:
            tn += 1
        elif not expected_blocked and actual_blocked:
            fp += 1
        elif expected_blocked and not actual_blocked:
            fn += 1

    total = len(test_cases)
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    avg_latency_ms = sum(latencies) / len(latencies)

    print(f"  - Total Evaluation Cases: {total}")
    print(f"  - True Positives (Blocked Defects): {tp}")
    print(f"  - True Negatives (Passed Clean Code): {tn}")
    print(f"  - False Positives (False Blocks): {fp}")
    print(f"  - False Negatives (Missed Defects): {fn}")
    print(f"  - Classification Accuracy: {accuracy * 100:.1f}%")
    print(f"  - Precision: {precision:.3f} | Recall: {recall:.3f} | F1-Score: {f1:.3f}")
    print(f"  - Average Latency: {avg_latency_ms:.2f} ms per verification\n")

    return {
        "total_cases": total,
        "accuracy": round(accuracy, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "avg_latency_ms": round(avg_latency_ms, 2)
    }


def run_lde_simulated_attempt_reduction_benchmark():
    print("==========================================================")
    print("  BENCHMARK 2: LDE Error Loop Attempt Reduction")
    print("==========================================================")

    lde = LoopDetectionEngine(threshold_similarity=0.85, max_history_size=10)
    
    repeated_error = (
        "TypeError: Cannot read property 'map' of undefined\n"
        "    at UserList.render (UserList.js:42:18)"
    )

    baseline_simulated_attempts = 15
    goby_iterations_to_detect = 0

    for i in range(1, baseline_simulated_attempts + 1):
        code_variant = f"const users = props.data; users.map(u => u.id); // attempt {i}"
        result = lde.record_attempt(code_variant, repeated_error)
        if result.is_loop_detected:
            goby_iterations_to_detect = i
            break

    reduction_percent = ((baseline_simulated_attempts - goby_iterations_to_detect) / baseline_simulated_attempts) * 100

    print(f"  - Baseline Simulated Repair Attempts: {baseline_simulated_attempts}")
    print(f"  - Goby LDE Triggered Interception at Attempt: {goby_iterations_to_detect}")
    print(f"  - Simulated Attempt Reduction: {reduction_percent:.1f}%\n")

    return {
        "baseline_attempts": baseline_simulated_attempts,
        "goby_attempts": goby_iterations_to_detect,
        "simulated_attempt_reduction_percent": round(reduction_percent, 1)
    }


def run_multitask_orchestration_benchmark():
    print("==========================================================")
    print("  BENCHMARK 3: Reference Workload Parallelism Demonstration")
    print("==========================================================")
    
    task_count = 8
    work_duration = 0.05  # 50ms synthetic I/O workload per task

    def dummy_task(t_id):
        time.sleep(work_duration)
        return f"Result_{t_id}"

    # Sequential Dispatch
    start_seq = time.time()
    for i in range(task_count):
        dummy_task(i)
    duration_seq = time.time() - start_seq

    # Goby Orchestrator Parallel Dispatch (4 Parallel Workers)
    orchestrator = MultitaskOrchestrator(max_workers=4)
    for i in range(task_count):
        orchestrator.add_task(f"t_{i}", f"Task {i}", dummy_task, args=(i,))

    start_goby = time.time()
    results = orchestrator.execute_all()
    duration_goby = time.time() - start_goby

    speedup_ratio = duration_seq / duration_goby if duration_goby > 0 else 1.0

    print(f"  - Sequential Time (8 tasks): {duration_seq:.3f}s")
    print(f"  - Goby Parallel Dispatch Time (4 Workers): {duration_goby:.3f}s")
    print(f"  - Dispatch Speedup Factor: {speedup_ratio:.2f}x\n")

    return {
        "sequential_seconds": round(duration_seq, 3),
        "goby_seconds": round(duration_goby, 3),
        "speedup_ratio": round(speedup_ratio, 2)
    }


def main():
    print("Running Goby v4.1 Empirical Benchmark & Evaluation Suite...")
    b1 = run_ccr_empirical_classification_benchmark()
    b2 = run_lde_simulated_attempt_reduction_benchmark()
    b3 = run_multitask_orchestration_benchmark()
    print("==========================================================")
    print("  BENCHMARK SUMMARY")
    print(f"  - Pre-Output AST Verification Accuracy: {b1['accuracy'] * 100}% (F1: {b1['f1']}, Cases: {b1['total_cases']})")
    print(f"  - LDE Simulated Attempt Reduction: {b2['simulated_attempt_reduction_percent']}%")
    print(f"  - Task Dispatch Speedup Factor: {b3['speedup_ratio']}x")
    print("==========================================================")


if __name__ == "__main__":
    main()
