# Cursor IDE Adapter (.cursorrules)

This adapter configures Goby for Cursor IDE AI agent sessions.

## Integration Setup
1. Copy the contents of this file into `.cursorrules` in your project root.

```markdown
# Goby Rules for Cursor
- Always check core/lde_detector.py when stuck in an error loop.
- Run tests via python -m unittest discover tests/ before confirming task completion.
- Execute tasks concurrently when possible using core/orchestrator.py.
- Use core/ccr_engine.py (CognitiveControlRoom) to validate code syntax, scope, and cross-references before finalizing file edits.
```

