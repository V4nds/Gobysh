# Claude Code & Anthropic API Adapter

This adapter configures Goby for Claude Code CLI and Claude Desktop agents.

## Integration Setup
1. Include `AGENTS.md` content into your `CLAUDE.md` file at the root of your project.
2. Register `SKILL.md` in your custom skill directory.

## Core Rules for Claude
- Enable subagent execution for parallel task processing.
- Perform empirical verification using terminal command calls (`python -m unittest`).
- Respect the Loop Detection Engine (LDE) threshold when debugging.
- Use `CognitiveControlRoom` (CCR) neurons (`core/ccr_engine.py`) to validate syntax, scope, cross-references, and information density before delivering outputs.

