# Antigravity & Gemini IDE Adapter

This adapter configures Goby for the Antigravity IDE and Gemini CLI environment.

## Integration Setup
1. Copy `SKILL.md` to `.agents/skills/goby/SKILL.md` or global config `~/.gemini/config/skills/goby/SKILL.md`.
2. Append `AGENTS.md` instructions to your workspace `.agents/AGENTS.md`.

## Runtime Integration
Use standard Antigravity tools:
- `run_command`: Run Python test suites via `python -m unittest discover tests/`.
- `view_file`: Read source code definitions before writing implementations.
- `write_to_file`: Edit code files with precision.
- `CognitiveControlRoom`: Validate pre-output thoughts via `python -c "from core import CognitiveControlRoom; ccr = CognitiveControlRoom(); print(ccr.neuron_syntax_check('...'))"`.

