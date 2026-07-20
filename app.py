"""
Auto-Debug Agent
-----------------
A small but *real* agent: it doesn't just answer once, it loops.

Loop = perceive -> act -> observe -> repeat:
  1. Claude reads the broken code + goal.
  2. Claude calls a tool (`run_python`) to actually execute the code.
  3. The agent runs it in a sandboxed subprocess and returns real stdout/stderr.
  4. Claude reads that real feedback and decides whether to fix the code and
     try again, or declare success.
  5. Repeats up to MAX_ITERATIONS times.

This is the core pattern behind coding agents (Claude Code, Cursor's agent
mode, etc.) just shrunk down to ~100 lines so it's easy to explain.
"""

import gradio as gr
import subprocess
import os
import json

# ---------------------------------------------------------------------------
# Backend switch: "ollama" (default — local, free, needs Ollama running on
# your machine) or "anthropic" (hosted, needs ANTHROPIC_API_KEY).
# Change via environment variable, e.g.:
#   export MODEL_BACKEND=anthropic
#   export ANTHROPIC_API_KEY=sk-ant-...
# Or point at a different local model:
#   export OLLAMA_MODEL=qwen3.6   # must be a model that supports tool calling
# ---------------------------------------------------------------------------
BACKEND = os.environ.get("MODEL_BACKEND", "ollama")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

MAX_ITERATIONS = 5

# Tool schema in a provider-neutral shape; each backend adapts it below.
TOOL_SCHEMA = {
    "name": "run_python",
    "description": (
        "Execute a Python code snippet in a sandboxed subprocess and "
        "return stdout, stderr, and exit code. Always use this to test "
        "whether code actually works before declaring it fixed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The full Python code to execute",
            }
        },
        "required": ["code"],
    },
}


def run_python(code: str, timeout: int = 5) -> dict:
    """Actually execute the code. This is the agent's only window onto reality."""
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1}


def _call_anthropic(history):
    """Adapt our provider-neutral history into an Anthropic API call."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    messages = []
    for turn in history:
        if turn["role"] == "user":
            messages.append({"role": "user", "content": turn["content"]})
        elif turn["role"] == "assistant":
            content = []
            if turn.get("content"):
                content.append({"type": "text", "text": turn["content"]})
            for tc in turn.get("tool_calls", []):
                content.append(
                    {
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc["arguments"],
                    }
                )
            messages.append({"role": "assistant", "content": content})
        elif turn["role"] == "tool":
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": turn["tool_call_id"],
                            "content": turn["content"],
                        }
                    ],
                }
            )

    tools = [
        {
            "name": TOOL_SCHEMA["name"],
            "description": TOOL_SCHEMA["description"],
            "input_schema": TOOL_SCHEMA["parameters"],
        }
    ]
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=2000, tools=tools, messages=messages
    )

    text = "".join(b.text for b in response.content if b.type == "text")
    tool_calls = [
        {"id": b.id, "name": b.name, "arguments": b.input}
        for b in response.content
        if b.type == "tool_use"
    ]
    return {"content": text, "tool_calls": tool_calls}


def _call_ollama(history):
    """Adapt our provider-neutral history into a call to a local Ollama
    model, using Ollama's native Python client (not the OpenAI-compat
    endpoint) so we can pass think=False. This matters for models like
    qwen3.6: their "thinking" mode can otherwise interfere with reliable
    tool calling."""
    from ollama import Client

    client = Client(host=OLLAMA_HOST)

    messages = []
    for turn in history:
        if turn["role"] == "user":
            messages.append({"role": "user", "content": turn["content"]})
        elif turn["role"] == "assistant":
            msg = {"role": "assistant", "content": turn.get("content") or ""}
            if turn.get("tool_calls"):
                msg["tool_calls"] = [
                    {
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        }
                    }
                    for tc in turn["tool_calls"]
                ]
            messages.append(msg)
        elif turn["role"] == "tool":
            messages.append(
                {
                    "role": "tool",
                    "content": turn["content"],
                }
            )

    tools = [{"type": "function", "function": TOOL_SCHEMA}]
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        tools=tools,
        think=False,  # avoid qwen3.6-style thinking mode breaking tool calls
    )
    msg = response.message

    tool_calls = []
    for idx, tc in enumerate(msg.tool_calls or []):
        tool_calls.append(
            {
                "id": f"call_{idx}",  # Ollama doesn't assign call ids, so we make our own
                "name": tc.function.name,
                "arguments": dict(tc.function.arguments),
            }
        )

    return {"content": msg.content or "", "tool_calls": tool_calls}


def call_model(history):
    if BACKEND == "ollama":
        return _call_ollama(history)
    return _call_anthropic(history)


def debug_agent(code: str, task_description: str, progress=gr.Progress()):
    print(f"[debug_agent] received click. backend={BACKEND} model={OLLAMA_MODEL if BACKEND=='ollama' else 'claude-sonnet-4-6'}")
    progress(0, desc="Starting agent...")
    trace = [f"*Backend: `{BACKEND}`" + (f" ({OLLAMA_MODEL})*" if BACKEND == "ollama" else "*")]
    history = [
        {
            "role": "user",
            "content": (
                f"You are an autonomous debugging agent. Goal: {task_description}\n\n"
                f"Here is the code:\n```python\n{code}\n```\n\n"
                "Use the run_python tool to test the code, observe the real "
                "output/errors, and iterate until it works correctly and "
                "fulfills the goal. When it works, respond with a final "
                "message (no more tool calls) starting with 'FINAL:' "
                "followed by the working code in a python code block and a "
                "short explanation of what you changed."
            ),
        }
    ]

    final_text = ""
    for i in range(MAX_ITERATIONS):
        print(f"[debug_agent] iteration {i + 1}/{MAX_ITERATIONS}: calling model...")
        progress((i) / MAX_ITERATIONS, desc=f"Agent step {i + 1}: thinking...")
        result = call_model(history)
        print(f"[debug_agent] iteration {i + 1}: got response, tool_calls={len(result['tool_calls'])}")
        history.append(
            {
                "role": "assistant",
                "content": result["content"],
                "tool_calls": result["tool_calls"],
            }
        )

        if result["content"]:
            trace.append(f"**Step {i + 1} — reasoning:**\n{result['content']}")

        if not result["tool_calls"]:
            final_text = result["content"]
            break

        for tc in result["tool_calls"]:
            if tc["name"] == "run_python":
                obs = run_python(tc["arguments"].get("code", ""))
                trace.append(
                    f"**Step {i + 1} — ran the code, real result:**\n"
                    f"stdout: `{obs['stdout']}`\n"
                    f"stderr: `{obs['stderr']}`\n"
                    f"exit_code: `{obs['exit_code']}`"
                )
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc["name"],
                        "content": json.dumps(obs),
                    }
                )

    return (
        final_text or "Agent did not converge within the iteration limit.",
        "\n\n---\n\n".join(trace),
    )


with gr.Blocks(title="Auto-Debug Agent") as demo:
    gr.Markdown(
        "# 🔧 Auto-Debug Agent\n"
        "Give it broken Python code and a goal. It will autonomously run it, "
        "read the real error, fix the code, and re-run — looping until it "
        "actually works. Scroll down to watch every step of its reasoning "
        "and every real execution result."
    )
    with gr.Row():
        code_input = gr.Textbox(
            label="Python code (can be broken)",
            lines=12,
            value="def add(a, b)\n    return a + b\n\nprint(add(2, 3))",
        )
        task_input = gr.Textbox(
            label="Goal",
            value="Fix the syntax error and make it print 5",
            lines=2,
        )
    run_btn = gr.Button("Run Agent", variant="primary")
    final_output = gr.Markdown(label="Final Result")
    trace_output = gr.Markdown(label="Agent Trace (step by step)")

    run_btn.click(
        debug_agent,
        inputs=[code_input, task_input],
        outputs=[final_output, trace_output],
    )

if __name__ == "__main__":
    demo.launch()
