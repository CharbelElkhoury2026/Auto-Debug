# Setup, Hosting & Model Notes

Detailed instructions for running and deploying the Auto-Debug Agent. See the main [README.md](./README.md) for the project overview.

## Files

- `app.py` — the agent + a small Gradio UI
- `requirements.txt` — dependencies

## How to host it for free (Hugging Face Spaces — ~10 minutes)

1. Go to https://huggingface.co and create a free account if you don't have
   one.
2. Click **New Space** (top right, under your profile → "New Space").
3. Give it a name (e.g. `auto-debug-agent`), choose **Gradio** as the SDK,
   choose the free **CPU basic** hardware, set visibility to **Public**.
4. Once created, you'll land on a page for your new Space with a "Files"
   tab. Upload `app.py` and `requirements.txt` there (drag and drop works),
   or use git:
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/auto-debug-agent
   cd auto-debug-agent
   cp /path/to/app.py .
   cp /path/to/requirements.txt .
   git add .
   git commit -m "Add auto-debug agent"
   git push
   ```
5. Add your Anthropic API key as a secret: go to **Settings** (in your
   Space) → **Repository secrets** → add a secret named
   `ANTHROPIC_API_KEY` with your key as the value. (Never put the key
   directly in `app.py`.)
6. The Space will auto-build and give you a public URL like:
   `https://huggingface.co/spaces/<your-username>/auto-debug-agent`
   That's the link you paste into the application.

## Alternative: run it locally first to test

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```
Then open the local URL it prints (usually http://127.0.0.1:7860).

## Using your local Ollama model instead

The app has a pluggable backend so you can develop/test for free against a
local Ollama model, and only use the Claude API for the version you
actually deploy.

```bash
pip install -r requirements.txt
export MODEL_BACKEND=ollama
export OLLAMA_MODEL=qwen3-coder:30b      # recommended, see below
python app.py
```

**Recommended model: `qwen3-coder:30b`** (`ollama pull qwen3-coder:30b`).
It's a 30B MoE model (~3B active params, so it's fast despite the size) built
specifically for agentic coding and tool calling — currently the top local
pick for exactly this kind of task. Needs ~19GB at Q4 quantization.

If that's too heavy for your hardware, **`qwen3:8b`** is a solid, lighter
fallback with reliable native tool calling (~6-8GB).

If you'd rather use something you've already pulled, `qwen3.6` also works —
it has native tool calling, but its "thinking" mode can interfere with
reliable tool calls, so `app.py` already passes `think=False` when calling
it, which fixes this. `deepseek-coder-v2:16b` is a strong coding model but
its tool-calling support in Ollama is less consistent. `deepseek-r1:8b` is a
reasoning model, not built for tool calling, so skip it for this agent loop.

**Important caveats:**
- **Not every local model supports tool calling reliably.** If a model
  doesn't, the agent loop will error out or silently never call
  `run_python`.
- **This only works locally.** Hugging Face Spaces (or any cloud host)
  cannot reach `localhost:11434` on your laptop. If you want a hosted
  public link for the application, deploy the `anthropic` backend (the
  default) instead — Ollama is best used for free local iteration while
  you build/tweak the agent, then you switch back to Claude for the
  version you actually submit.
- If you really want a public link to a locally-running Ollama agent, you'd
  need to tunnel it (e.g. `ngrok http 7860`), but this exposes your machine
  to the internet and isn't recommended for a job application demo.

## Alternative hosts (if you'd rather not use Hugging Face)

- **Render.com** — free web service tier, connect your GitHub repo, set
  `ANTHROPIC_API_KEY` as an environment variable, start command
  `python app.py` (with `server_name="0.0.0.0"` added to `demo.launch()`).
- **Railway.app** — similar flow, connects to GitHub, auto-detects Python.

Hugging Face Spaces is the fastest path since it's built specifically for
demos like this and handles the server config for you.

## Ideas if you want to extend it before applying (optional, ~15 more min)

- Add a second tool, e.g. `lint_check` using `pyflakes`, so the agent checks
  style as well as correctness.
- Log each run's trace to a file so you can show "here are 5 examples of it
  fixing real bugs" as extra evidence.
- Swap `run_python` for a tool that runs a repo's actual test suite
  (`pytest`), turning this into a mini CI-debugging agent.
