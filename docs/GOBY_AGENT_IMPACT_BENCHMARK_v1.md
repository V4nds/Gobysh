Goby Agent Impact Benchmark v1

Purpose

Measure whether Goby changes the behavior and outcome of an AI coding agent,not merely whether Goby can detect bad code.

The experiment compares the same agent, model, task set, and environment:

CONTROL: agent without Goby

GOBY: agent with Goby verification/control enabled

The primary question is:

Does Goby improve successful task completion while reducing unsafe orwasteful repair behavior?

Core rule

Do not compare different prompts, models, temperature/settings, tools, ortask sets between CONTROL and GOBY. The only intended independent variable isGoby integration.

Evaluation matrix

For each task, run both conditions:

Condition

Agent

Model

Prompt

Tools

Environment

CONTROL

same

same

same

same

same

GOBY

same

same

same

same

same

Use a fresh isolated workspace for every trial.

Recommended first experiment:

30 tasks

2 conditions

3 repetitions per condition

180 total trials

If compute is limited, start with 10 tasks × 2 conditions × 2 repetitions =40 trials, then expand.

Task composition

Do not use only synthetic syntax mistakes.

Recommended 30-task mix:

8 bug-fix tasks

6 feature tasks

4 refactoring tasks

4 test-writing tasks

4 regression-prone tasks

4 deliberately ambiguous / abstention-sensitive tasks

Prefer real repositories and real issue descriptions. SWE-bench Verified isa useful external reference because it contains 500 human-validated,reproducible coding tasks, but a smaller custom suite is appropriate for thefirst Goby experiment.

Primary metrics

1. Task Success Rate

A task is successful only when its evaluator passes.

success_rate = successful_trials / total_trials

2. False Completion Rate

The agent claims completion but the evaluator fails.

false_completion_rate =false_completion_trials / trials_where_agent_claimed_completion

This is a key Goby metric.

3. Recovery Success Rate

Among trials where Goby blocks a candidate, how often does the agent eventuallyproduce a passing candidate?

recovery_success_rate =successful_recoveries / blocked_trials

4. Attempts to Success

Count candidate generations / repair cycles until the first passing result.

Report median and p90, not only the mean.

5. Tool Calls

Count tool invocations per trial.

Report median and p90.

6. Wall-clock Time

Measure from agent start until evaluator completion.

7. Token Cost

If the provider exposes usage, record input/output tokens. Otherwise report"not available" rather than estimating.

8. Regression Rate

A patch is a regression if previously passing tests become failing after theagent's change.

9. Unnecessary Action Rate

For tasks where the correct action is "do not change code", measure how oftenthe agent makes a modification anyway.

Secondary Goby-specific metrics

Gate Trigger Rate

How often does Goby block a candidate?

Gate Precision

Of all blocked candidates, how many contained a genuine evaluator-relevantproblem?

Gate False-Block Rate

How often does Goby block a candidate that would have passed the evaluator?

Loop Interception Rate

How often does LDE detect repeated repair behavior before the agent reachesthe baseline's corresponding failure count?

Strategy-Change Rate

After a repeated failure signal, how often does the agent actually change itsrepair strategy?

This metric is critical. LDE is not valuable merely because it says BLOCKED;it is valuable if the agent subsequently behaves differently.

Minimum event schema

Record one JSON object per event:

{"run_id": "uuid","condition": "control|goby","task_id": "task-001","trial": 1,"event": "candidate|goby_block|goby_pass|tool_call|agent_claim|evaluation","timestamp": "...","attempt": 1,"payload": {}}

Do not store secrets, API keys, or full private repository contents in thebenchmark artifact.

Required final record

Each trial should produce:

{"run_id": "...","condition": "control","task_id": "...","success": true,"agent_claimed_done": true,"false_completion": false,"attempts": 3,"tool_calls": 11,"wall_time_seconds": 142.7,"input_tokens": null,"output_tokens": null,"goby_blocks": 0,"goby_false_blocks": 0,"lde_interceptions": 0,"strategy_changes_after_lde": 0,"regression": false}

Statistical reporting

For each metric report:

CONTROL mean/median

GOBY mean/median

absolute difference

relative difference

bootstrap 95% confidence interval where practical

Do not declare an improvement from one or two trials.

For paired tasks, compare each task's CONTROL and GOBY outcome. The pairing isimportant because task difficulty varies.

Success criteria for a meaningful Goby effect

A strong first result would look like:

higher task success rate

lower false-completion rate

fewer repair attempts or tool calls

no material increase in regression rate

measurable recovery after Goby blocks

evidence that LDE causes strategy changes rather than merely extra blocks

Do not choose thresholds after seeing the results. Define them before the run.

A reasonable preregistered target for an exploratory first study is:

Task success: +5 percentage points or more

False completion: at least 25% relative reduction

Median repair attempts: at least 10% reduction

Regression rate: not worse by more than 2 percentage points

These are targets, not claims.

Critical ablation

Run at least these three configurations if possible:

A. Agent aloneB. Agent + Goby validation gatesC. Agent + Goby validation gates + LDE feedback

This isolates whether:

validation itself helps

loop detection adds additional value

If C is no better than B, LDE may be unnecessary complexity.If B is no better than A, Goby is not changing agent behavior enough.

Integration contract

Goby should expose a small agent-facing interface:

candidate = agent.propose(...)
verdict = goby.verify(candidate)

if verdict.blocked:
    agent.receive_feedback(verdict)
    # agent must decide whether to repair, change strategy, or abstain

if verdict.verified:
    agent.may_apply(candidate)

For dynamic verification:

evidence = goby.create_evidence_contract(
    claim="Tests pass",
    source=...
    test_command=...
)

The agent must not treat "BLOCKED" as a generic error. The feedback shouldcontain:

failed gate

evidence

reason

suggested next action

repeated-failure indicator

whether strategy change is required

Important distinction

A Goby block is not an improvement by itself.

The causal chain that must be demonstrated is:

Goby detects problem→ agent receives actionable evidence→ agent changes behavior→ candidate quality improves→ task outcome improves

If the chain stops at "Goby detected problem", Goby is a validator, not yetan effective agent-control layer.

External benchmark reference

For larger-scale evaluation, use a reproducible benchmark such asSWE-bench / SWE-bench Verified rather than inventing a proprietary task setonly for Goby.

SWE-bench evaluates generated patches by applying them to isolated repositoryenvironments and running tests. SWE-bench Verified is a 500-instancehuman-validated subset.

Do not compare a small Goby experiment numerically with public leaderboardscores unless the agent, model, harness, task subset, and evaluation protocolare equivalent.

Interpretation rules

If CONTROL ≈ GOBY:Goby has not demonstrated meaningful agent-level impact.

If GOBY improves verification but not task success:Goby is a useful validator, but agent integration is insufficient.

If GOBY improves task success but increases cost substantially:Goby may be effective but inefficient.

If GOBY reduces attempts/cost and improves success:This is evidence for a genuine agent-level benefit.

If GOBY increases false blocks:Fix the verifier before adding more agent-control features.

Recommended next Goby implementation

Prioritize these in order:

Agent-facing feedback object

Explicit STRATEGY_CHANGE_REQUIRED state for repeated failures

Candidate/evidence provenance ID

Structured event tracing

Benchmark runner

