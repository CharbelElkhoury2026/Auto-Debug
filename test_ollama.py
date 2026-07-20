"""
Standalone diagnostic — run this directly to check each layer separately:
    python test_ollama.py
No Gradio, no UI — just prints what's happening at each step.
"""

import os

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

print(f"1. Testing connection to Ollama at {OLLAMA_HOST} ...")
try:
    from ollama import Client

    client = Client(host=OLLAMA_HOST)
    tags = client.list()
    print("   OK — Ollama is reachable. Models available:")
    for m in tags.models:
        print(f"     - {m.model}")
except Exception as e:
    print(f"   FAILED: {e}")
    print("   -> Is Ollama running? Try `ollama serve` in another terminal, or `ollama list`.")
    raise SystemExit(1)

print(f"\n2. Testing a plain chat call to '{OLLAMA_MODEL}' (no tools) ...")
try:
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": "Say hello in exactly 3 words."}],
    )
    print(f"   OK — model responded: {response.message.content!r}")
except Exception as e:
    print(f"   FAILED: {e}")
    print(f"   -> Is '{OLLAMA_MODEL}' pulled? Try `ollama pull {OLLAMA_MODEL}` or `ollama list`.")
    raise SystemExit(1)

print(f"\n3. Testing tool calling with '{OLLAMA_MODEL}' ...")
try:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_python",
                "description": "Execute a Python code snippet and return stdout/stderr.",
                "parameters": {
                    "type": "object",
                    "properties": {"code": {"type": "string"}},
                    "required": ["code"],
                },
            },
        }
    ]
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": "Run this code: print(2+2)"}],
        tools=tools,
        think=False,
    )
    print(f"   Message content: {response.message.content!r}")
    print(f"   Tool calls: {response.message.tool_calls}")
    if response.message.tool_calls:
        print("   OK — model correctly attempted a tool call.")
    else:
        print("   WARNING — model did not call the tool. This model may not")
        print("   support tool calling reliably, or needs a different prompt style.")
except Exception as e:
    print(f"   FAILED: {e}")
    raise SystemExit(1)

print("\nAll layers OK. If the Gradio UI still shows nothing, the issue is")
print("likely in the UI/browser layer, not the model connection — check the")
print("browser console (F12) for JS errors, and confirm your Gradio version.")
