"""
╔══════════════════════════════════════════════════════════════╗
║   DEMO 3: Tree-of-Thoughts (ToT)                            ║
║   Pattern: Generate → Evaluate → Prune → Expand              ║
║                                                              ║
║   Run: python tree_of_thoughts.py                            ║
║   Requires: LM Studio server running on localhost:1234       ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import re
import time
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich import box

console = Console(width=100)

# ─── LM Studio Connection ───
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)
MODEL = "qwen2.5-7b-instruct-1m"


# ═══════════════════════════════════════════
# VERBOSE LLM CALL
# ═══════════════════════════════════════════

call_counter = 0

def llm_call(system: str, user: str, label: str = "",
             temperature: float = 0.7, max_tokens: int = 800) -> str:
    """Make an LLM call with full verbose logging."""
    global call_counter
    call_counter += 1

    console.print(f"\n[bold white on magenta]  API CALL #{call_counter} {label} [/bold white on magenta]")
    console.print(f"[dim]POST http://localhost:1234/v1/chat/completions[/dim]")
    console.print(f"[dim]Model: {MODEL} | Temp: {temperature} | Max tokens: {max_tokens}[/dim]")

    sys_preview = system[:100].replace("\n", " ") + "..."
    usr_preview = user[:120].replace("\n", " ") + ("..." if len(user) > 120 else "")
    console.print(f"  [yellow]    system[/yellow]: {sys_preview}")
    console.print(f"  [cyan]      user[/cyan]: {usr_preview}")

    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
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
# PHASE 1: GENERATE — multiple thought branches
# ═══════════════════════════════════════════

def generate_thoughts(question: str) -> list[dict]:
    """Generate 3 different reasoning approaches."""

    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 1: Generate Thought Branches [/bold]")
    console.print(f"{'━'*60}")

    system = (
        "You are a strategic thinker. Generate exactly 3 DIFFERENT approaches "
        "to answer the given question. Each approach must use a fundamentally "
        "different reasoning strategy.\n\n"
        "Format:\n"
        "APPROACH 1: [title]\n"
        "[2-3 sentence description]\n\n"
        "APPROACH 2: [title]\n"
        "[2-3 sentence description]\n\n"
        "APPROACH 3: [title]\n"
        "[2-3 sentence description]"
    )

    result = llm_call(system, f"Question: {question}", "→ Generate 3 branches")

    # Parse
    thoughts = []
    current_title = None
    current_lines = []

    for line in result.split("\n"):
        line = line.strip()
        if re.match(r"^APPROACH\s*\d", line, re.IGNORECASE):
            if current_title:
                thoughts.append({
                    "title": current_title,
                    "description": " ".join(current_lines),
                    "score": 0.0,
                    "eval_reason": "",
                })
            parts = line.split(":", 1)
            current_title = parts[1].strip() if len(parts) > 1 else line
            current_lines = []
        elif line and current_title:
            current_lines.append(line)

    if current_title:
        thoughts.append({
            "title": current_title,
            "description": " ".join(current_lines),
            "score": 0.0,
            "eval_reason": "",
        })

    for i, t in enumerate(thoughts):
        console.print(Panel(
            f"[bold]{t['title']}[/bold]\n{t['description']}",
            title=f"🌿 Branch {i+1}",
            border_style="blue",
            padding=(0, 1),
        ))

    return thoughts


# ═══════════════════════════════════════════
# PHASE 2: EVALUATE — score each branch
# ═══════════════════════════════════════════

def evaluate_thoughts(question: str, thoughts: list[dict]) -> list[dict]:
    """Score each thought branch via separate LLM calls."""

    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 2: Evaluate & Score Each Branch [/bold]")
    console.print(f"{'━'*60}")

    system = (
        "You are an evaluation expert. Score the given approach on a 0.0-1.0 scale.\n\n"
        "Criteria:\n"
        "- Completeness: addresses all parts of the question?\n"
        "- Feasibility: can actually produce a good answer?\n"
        "- Depth: goes beyond surface-level?\n\n"
        "Respond with ONLY this JSON (no markdown):\n"
        '{"score": 0.X, "reasoning": "one sentence explanation"}'
    )

    for i, t in enumerate(thoughts):
        user = (
            f"Question: {question}\n\n"
            f"Approach to evaluate:\n"
            f"Title: {t['title']}\n"
            f"Description: {t['description']}"
        )

        result = llm_call(system, user, f"→ Score branch {i+1}", temperature=0.2)

        # Parse score
        try:
            match = re.search(r'\{[^}]+\}', result)
            if match:
                parsed = json.loads(match.group())
                t["score"] = round(float(parsed.get("score", 0.5)), 1)
                t["eval_reason"] = parsed.get("reasoning", "")
            else:
                t["score"] = 0.5
                t["eval_reason"] = result
        except (json.JSONDecodeError, ValueError):
            t["score"] = 0.5
            t["eval_reason"] = result

        # Display with color
        if t["score"] >= 0.7:
            color, status = "green", "✅ KEEP"
        elif t["score"] >= 0.4:
            color, status = "yellow", "⚠️  MARGINAL"
        else:
            color, status = "red", "❌ PRUNE"

        console.print(Panel(
            f"Score: [bold {color}]{t['score']}[/bold {color}]  {status}\n"
            f"Reason: {t['eval_reason']}",
            title=f"📊 Branch {i+1}: {t['title']}",
            border_style=color,
            padding=(0, 1),
        ))

    return thoughts


# ═══════════════════════════════════════════
# PHASE 3: PRUNE — remove low-scoring branches
# ═══════════════════════════════════════════

def prune_thoughts(thoughts: list[dict], threshold: float = 0.5) -> list[dict]:
    """Remove branches below threshold."""

    console.print(f"\n{'━'*60}")
    console.print(f"[bold] PHASE 3: Prune (threshold: {threshold}) [/bold]")
    console.print(f"{'━'*60}")

    kept = [t for t in thoughts if t["score"] >= threshold]
    pruned = [t for t in thoughts if t["score"] < threshold]

    for t in pruned:
        console.print(f"  [red]✂  Pruned:[/red] {t['title']} → score {t['score']}")
    for t in kept:
        console.print(f"  [green]✓  Kept:  [/green] {t['title']} → score {t['score']}")

    if not kept:
        console.print("  [yellow]Nothing survived — keeping best branch[/yellow]")
        kept = [max(thoughts, key=lambda x: x["score"])]

    return kept


# ═══════════════════════════════════════════
# PHASE 4: EXPAND — deep dive on best branch
# ═══════════════════════════════════════════

def expand_best(question: str, thoughts: list[dict]) -> str:
    """Expand the highest-scoring branch into a full answer."""

    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 4: Expand Best Branch [/bold]")
    console.print(f"{'━'*60}")

    best = max(thoughts, key=lambda x: x["score"])
    console.print(f"  [bold green]★ Selected:[/bold green] {best['title']} (score: {best['score']})")

    system = (
        "You are an expert software engineering advisor. Follow the given "
        "analytical approach to produce a thorough answer.\n\n"
        "Structure:\n"
        "1. Analysis using the specified approach\n"
        "2. Concrete comparison with data\n"
        "3. Clear recommendation\n"
        "4. Who should choose what\n\n"
        "Be specific. Use numbers. Max 300 words."
    )

    user = (
        f"Question: {question}\n\n"
        f"Approach to follow:\n"
        f"Title: {best['title']}\n"
        f"Strategy: {best['description']}\n\n"
        f"Execute this approach now."
    )

    result = llm_call(system, user, "→ Expand best path", temperature=0.3, max_tokens=1200)

    console.print(Panel(
        result,
        title=f"🌳 Expanded: {best['title']}",
        border_style="green",
        padding=(0, 1),
    ))

    return result


# ═══════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════

def run_tot(question: str):
    global call_counter
    call_counter = 0

    console.print(Panel(
        f"[bold cyan]{question}[/bold cyan]",
        title="🌳 DEMO 3: Tree-of-Thoughts",
        subtitle="Generate → Evaluate → Prune → Expand",
        border_style="magenta",
        box=box.DOUBLE,
    ))

    total_start = time.time()

    # Run pipeline
    thoughts = generate_thoughts(question)
    thoughts = evaluate_thoughts(question, thoughts)
    surviving = prune_thoughts(thoughts)
    final = expand_best(question, surviving)

    total_time = time.time() - total_start

    # ── Visual tree ──
    console.print()
    tree = Tree("[bold]🌳 Thought Tree Summary[/bold]")
    root = tree.add("[cyan]Problem[/cyan]")

    best = max(thoughts, key=lambda x: x["score"])
    for t in thoughts:
        sc = t["score"]
        color = "green" if sc >= 0.7 else "yellow" if sc >= 0.4 else "red"
        label = f"[{color}]{t['title']} (score: {sc})[/{color}]"

        if t is best and t in surviving:
            branch = root.add(f"[bold green]★ {label}[/bold green]")
            branch.add("[green]→ Expanded into final answer[/green]")
        elif t in surviving:
            root.add(label)
        else:
            root.add(f"[red dim]✂ {label} (pruned)[/red dim]")

    console.print(tree)

    # ── Final answer ──
    console.print(Panel(
        final,
        title="✅ Final Answer (Best Path)",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2),
    ))

    # ── Stats ──
    stats = Table(title="Tree-of-Thoughts Stats", box=box.SIMPLE)
    stats.add_column("Metric", style="bold")
    stats.add_column("Value", style="magenta")
    stats.add_row("Total LLM calls", str(call_counter))
    stats.add_row("Branches generated", str(len(thoughts)))
    stats.add_row("Branches pruned", str(len(thoughts) - len(surviving)))
    stats.add_row("Best score", str(best["score"]))
    stats.add_row("Total time", f"{total_time:.2f}s")
    stats.add_row("Search strategy", "BFS (breadth-first)")
    stats.add_row("Key cost", f"{call_counter} LLM calls vs ReAct's ~5-10")
    console.print(stats)


# ═══════════════════════════════════════════
if __name__ == "__main__":
    console.print(Panel(
        "Pattern: Generate → Evaluate → Prune → Expand\n"
        "LLM: Qwen2.5-7B-Instruct via LM Studio\n"
        "Server: http://localhost:1234/v1\n\n"
        "[dim]Branch generation = 1 call, scoring = 3 calls, expansion = 1 call → 5+ total[/dim]",
        title="🔧 Config",
        border_style="dim",
    ))

    QUESTION = (
        "Which programming language should I learn for backend development in 2025 "
        "— Go, Rust, or Python? Compare them by job market demand, performance, "
        "and learning curve, then give me a recommendation."
    )

    run_tot(QUESTION)
