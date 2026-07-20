# 🔧 Auto-Debug Agent

A small, transparent, autonomous coding agent — built to *actually* debug code, not just talk about it.

Give it broken Python and a goal. It runs the code, reads the real error, fixes it, and re-runs — looping until the code genuinely works. Every reasoning step and every execution result is shown, so you can watch it work instead of trusting a black box.

> Built to understand — and demonstrate — how agentic tool-calling loops actually work under the hood, rather than just wrapping a single prompt.

---

## Why this is an *agent*, not just a chatbot wrapper

Most "AI demo" projects are one prompt → one response. This one has a real feedback loop:

1. **Perceive** — the model reads the code and the goal.
2. **Act** — it calls a tool (`run_python`) to actually execute the code.
3. **Observe** — the agent runs it in a sandboxed subprocess and returns the *real* stdout, stderr, and exit code.
4. **Decide** — the model reads that real feedback and either fixes the code and loops again, or declares success.
5. Repeats for up to 5 iterations.

It can't just claim a bug is fixed — it has to prove it by re-running the code and getting a clean result. This is the same perceive → act → observe pattern behind tools like Claude Code and Cursor's agent mode, built from scratch at a small scale so the mechanics stay visible.

---

## How it works

```
┌──────────────┐      tool call       ┌──────────────────┐
│              │ ───────────────────► │                  │
│  LLM (Claude │                      │  run_python tool │
│  or local    │ ◄─────────────────── │  (sandboxed       │
│  Ollama)     │   stdout / stderr    │  subprocess)      │
│              │      exit code       │                  │
└──────────────┘                      └──────────────────┘
       │
       │ loops until code runs cleanly
       ▼
  Final working code + explanation of the fix
```

The model backend is pluggable:
- **Anthropic (Claude)** — used for the hosted version.
- **Local Ollama model** — free, fully offline, used for development/testing (tested with `qwen3-coder:30b`).

Both paths share the exact same agent loop and tool — only the model call is swapped, via a single environment variable.

---

## Try it

**Live demo:** *[add your Hugging Face Spaces link here once deployed]*

**Run it yourself:**

```bash
# 1. Clone
git clone https://github.com/<your-username>/auto-debug-agent.git
cd auto-debug-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3a. Option A — run with Claude
export ANTHROPIC_API_KEY=sk-ant-...
python app.py

# 3b. Option B — run fully local and free with Ollama
ollama pull qwen3-coder:30b
export MODEL_BACKEND=ollama
export OLLAMA_MODEL=qwen3-coder:30b
python app.py
```

Then open the local URL it prints (usually `http://127.0.0.1:7860`).

---

## Project structure

```
auto-debug-agent/
├── app.py             # Agent loop + Gradio UI
├── requirements.txt   # Dependencies
├── SETUP.md           # Detailed setup, hosting, and model notes
└── README.md          # This file
```

See [`SETUP.md`](./SETUP.md) for full hosting instructions (Hugging Face Spaces, Render, Railway) and notes on which local models work best for tool calling.

---

## What I'd extend next

- A second tool (e.g. a linter) so the agent checks style as well as correctness.
- Point `run_python` at a repo's actual `pytest` suite, turning this into a mini CI-debugging agent.
- Persist each run's trace so multiple debugging sessions can be compared.

---

## License

MIT — use it, fork it, break it, fix it.
