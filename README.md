# AI Engineering Coursework

Coursework for CSC 595: AI Agent Architecture & Development, Saint Martin's University.

## Contents

| Folder | What's in it |
|---|---|
| `assignment-1/` | Hosted API call to Anthropic's Claude, plus a local model session with Ollama |
| `Project/` | Term project documents, starting with the initial project draft |

## Assignment 1

### Part A: Hosted API call

`assignment-1/api_call.py` reads an Anthropic API key from an environment variable, sends one prompt to Claude, and prints the response. The key is never stored in the code or the repo.

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
   python assignment-1/api_call.py
   ```

Successful output is saved in `assignment-1/api_output.png`.

### Part B: Local model

Ran `llama3.2:3b` locally with Ollama:

```
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

The session is saved in `assignment-1/ollama_session.png`. See `assignment-1/ollama_notes.md` for notes.

## Security

API keys are read from environment variables only. `.gitignore` excludes `.env` files so keys are never committed.
