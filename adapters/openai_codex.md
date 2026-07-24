# OpenAI / Custom GPT / Codex Adapter

This adapter configures Goby for OpenAI API agents, ChatGPT Code Interpreter, and Custom GPTs.

## System Prompt Injection
Inject `SKILL.md` into the Custom Instructions / System Prompt field of your GPT or Assistant API configuration.

## Tool Capabilities Needed
- Code Execution Environment (Python 3.8+)
- Read & Write Access to Project Workspace
- Pre-Output Signal Validation via `from core import CognitiveControlRoom` (CCR Neurons)

