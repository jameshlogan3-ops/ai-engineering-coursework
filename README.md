# AI Engineering Coursework

Coursework for CSC 595: AI Agent Architecture & Development, Saint Martin's University.

## Contents

| Folder | What's in it |
|---|---|
| `development-environment-setup/` | Hosted API call to Anthropic's Claude, plus a local model session with Ollama |
| `week2-hugging-face-hub-scavenger-hunt.md` | Week 2: comparison of Llama 3.2 3B, Qwen2.5 7B, and Mistral Small 24B, including tokenizer counts, context windows, and a Qwen2.5 technical report analysis |
| `week4/` | Week 4: Claude Opus 5.5 vs. Llama 3.2 3B on six support tickets, with scoring, recommendation, the Llama session log, and screenshots |
| `Project/` | Term project: a change review and CMDB hygiene assistant. Starts with the initial project draft. |

## Assignment 1: Development Environment Setup

### Part A: Hosted API call

`development-environment-setup/api_call.py` reads an Anthropic API key from an environment variable, sends one prompt to Claude, and prints the response. The key is never stored in the code or the repo.

**Run it (Windows PowerShell):**

1. Set the API key once, then close and reopen PowerShell:
   ```
   setx ANTHROPIC_API_KEY "your-key-here"
   ```
2. Install the SDK:
   ```
   pip install anthropic
   ```
3. Run the script:
   ```
   python development-environment-setup/api_call.py
   ```

Successful output is saved in `development-environment-setup/api_output.png`.

### Part B: Local model

Ran `llama3.2:3b` locally with Ollama:

```
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

The session is saved in `development-environment-setup/ollama_session.png`. See `development-environment-setup/ollama_notes.md` for notes.

## Security

API keys are read from environment variables only. `.gitignore` excludes `.env` files so keys are never committed.
