"""
╔══════════════════════════════════════════════════════════════╗
║   DEMO 1: ReAct Agent (Reflective Reasoning)                ║
║   Pattern: Thought → Action → Observation → Loop             ║
║                                                              ║
║   Run: python react_agent.py                                 ║
║   Requires: LM Studio server running on localhost:1234       ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import time
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console(width=100)

# ─── LM Studio Connection ───
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)
MODEL = "qwen2.5-7b-instruct-1m"


# ═══════════════════════════════════════════
# SIMULATED TOOLS
# In production these would call real APIs.
# We simulate them to keep the demo offline.
# ═══════════════════════════════════════════

TOOLS = {
    "search_job_market": {
        "Go":     "Go: ~45,000 backend jobs globally (2025). Strong in cloud-native & DevOps. Top employers: Google, Uber, Cloudflare. Avg salary: $135K.",
        "Rust":   "Rust: ~18,000 backend jobs globally (2025). Fast growth in systems & blockchain. Top employers: AWS, Microsoft, Discord. Avg salary: $145K.",
        "Python": "Python: ~320,000 backend jobs globally (2025). Dominant in AI/ML, web APIs. Top employers: Google, Meta, Netflix. Avg salary: $125K.",
    },
    "benchmark_performance": {
        "Go":     "Go: REST API avg 120ms latency, 15K req/s single-core. Compiled binary, goroutine concurrency. Memory: ~20MB baseline.",
        "Rust":   "Rust: REST API avg 45ms latency, 28K req/s single-core. Zero-cost abstractions, no GC. Memory: ~8MB baseline.",
        "Python": "Python: REST API avg 350ms latency, 2K req/s single-core. Interpreted, GIL limits threading. Memory: ~35MB baseline.",
    },
    "evaluate_learning_curve": {
        "Go":     "Go: 2-4 weeks to productivity. 25 keywords, simple type system. Excellent official tour. Challenge: verbose error handling.",
        "Rust":   "Rust: 2-4 months to productivity. Borrow checker is steep. #1 loved language on SO for 7 years. Challenge: ownership model.",
        "Python": "Python: 1-2 weeks to productivity. Most readable syntax. 500K+ PyPI packages. Challenge: async patterns, no static types by default.",
    },
}


def execute_tool(tool_name: str, argument: str) -> str:
    """Execute a simulated tool and return the result."""
    tool_name = tool_name.strip().lower()
    argument = argument.strip().strip('"').strip("'")

    for lang in ["Go", "Rust", "Python"]:
        if lang.lower() in argument.lower():
            argument = lang
            break

    if tool_name in TOOLS and argument in TOOLS[tool_name]:
        return TOOLS[tool_name][argument]
    return f"Tool '{tool_name}' returned no results for '{argument}'."


# ═══════════════════════════════════════════
# VERBOSE LLM CALL — shows what LM Studio sees
# ═══════════════════════════════════════════

call_counter = 0

def llm_call(messages: list, label: str = "") -> str:
    """Make an LLM call with full verbose logging."""
    global call_counter
    call_counter += 1

    console.print(f"\n[bold white on blue]  API CALL #{call_counter} {label} [/bold white on blue]")
    console.print(f"[dim]POST http://localhost:1234/v1/chat/completions[/dim]")
    console.print(f"[dim]Model: {MODEL} | Temp: 0.3 | Max tokens: 800[/dim]")

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        preview = content[:120].replace("\n", " ") + ("..." if len(content) > 120 else "")
        color = {"system": "yellow", "user": "cyan", "assistant": "green"}.get(role, "white")
        console.print(f"  [{color}]{role:>10}[/{color}]: {preview}")

    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=800,
    )
    elapsed = time.time() - start

    result = response.choices[0].message.content.strip()
    tokens = response.usage

    console.print(f"[dim]← Response: {elapsed:.2f}s | "
                  f"Prompt: {tokens.prompt_tokens} tok | "
                  f"Completion: {tokens.completion_tokens} tok | "
                  f"Total: {tokens.total_tokens} tok[/dim]")

    return result


# ═══════════════════════════════════════════
# REACT SYSTEM PROMPT
# ═══════════════════════════════════════════

SYSTEM = """You are a ReAct agent. You solve problems step-by-step using Thought, Action, and Observation.

Available tools:
- search_job_market(language): Get job market data. Input: Go, Rust, or Python
- benchmark_performance(language): Get performance benchmarks. Input: Go, Rust, or Python
- evaluate_learning_curve(language): Get learning curve info. Input: Go, Rust, or Python

RULES:
- Call ONE tool per step
- Use this EXACT format:

Thought: <reasoning>
Action: <tool_name>
Action Input: <language>

When you have enough data, use:

Thought: <final reasoning>
Final Answer: <comprehensive recommendation>"""


# ═══════════════════════════════════════════
# REACT LOOP
# ═══════════════════════════════════════════

def run_react(question: str):
    global call_counter
    call_counter = 0

    console.print(Panel(
        f"[bold cyan]{question}[/bold cyan]",
        title="🧠 DEMO 1: ReAct Agent",
        subtitle="Thought → Action → Observation → Loop",
        border_style="cyan",
        box=box.DOUBLE,
    ))

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]

    for step in range(1, 15):
        console.print(f"\n{'━'*60}")
        console.print(f"[bold] STEP {step} [/bold]")
        console.print(f"{'━'*60}")

        output = llm_call(messages, f"→ Step {step}")

        thought = action = action_input = final_answer = None
        for line in output.split("\n"):
            l = line.strip()
            if l.lower().startswith("thought:"):
                thought = l.split(":", 1)[1].strip()
            elif l.lower().startswith("action:"):
                action = l.split(":", 1)[1].strip()
            elif l.lower().startswith("action input:") or l.lower().startswith("action_input:"):
                action_input = l.split(":", 1)[1].strip()
            elif l.lower().startswith("final answer:") or l.lower().startswith("final_answer:"):
                final_answer = l.split(":", 1)[1].strip()

        if thought:
            console.print(Panel(thought, title="💭 Thought", border_style="blue", padding=(0, 1)))

        if final_answer:
            console.print(Panel(
                final_answer,
                title="✅ Final Answer",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2),
            ))
            console.print(f"\n[bold]Total LLM calls: {call_counter}[/bold]")
            console.print(f"[bold]Total steps: {step}[/bold]")
            console.print(f"[bold]Pattern: Sequential (single reasoning path)[/bold]")
            return

        if action and action_input:
            console.print(Panel(
                f"[yellow]{action}[/yellow]( {action_input} )",
                title="⚡ Action → Tool Call",
                border_style="yellow",
                padding=(0, 1),
            ))

            observation = execute_tool(action, action_input)

            console.print(Panel(
                observation,
                title="👁 Observation ← Tool Result",
                border_style="magenta",
                padding=(0, 1),
            ))

            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
        else:
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": "Follow the format: Thought/Action/Action Input or Thought/Final Answer."})

    console.print("[red]Max steps reached.[/red]")


# ═══════════════════════════════════════════
if __name__ == "__main__":
    console.print(Panel(
        "Pattern: Thought → Action → Observation → Loop\n"
        "LLM: Qwen2.5-7B-Instruct via LM Studio\n"
        "Server: http://localhost:1234/v1\n\n"
        "[dim]Her API call hem bu terminalde hem LM Studio Logs panelinde görünür.[/dim]",
        title="🔧 Config",
        border_style="dim",
    ))

    QUESTION = (
        "Which programming language should I learn for backend development in 2025 "
        "— Go, Rust, or Python? Compare them by job market demand, performance, "
        "and learning curve, then give me a recommendation."
    )

    run_react(QUESTION)
