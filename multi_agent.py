"""
╔══════════════════════════════════════════════════════════════╗
║   DEMO 2: Multi-Agent System                                ║
║   Pattern: Orchestrator → Researcher → Analyst → Writer      ║
║                                                              ║
║   Run: python multi_agent.py                                 ║
║   Requires: LM Studio server running on localhost:1234       ║
╚══════════════════════════════════════════════════════════════╝
"""

import time
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
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
# AGENT PERSONAS — each agent gets a unique
# system prompt defining its expertise
# ═══════════════════════════════════════════

AGENTS = {
    "orchestrator": {
        "emoji": "🎯",
        "color": "cyan",
        "name": "Orchestrator",
        "system": (
            "You are the Orchestrator agent in a multi-agent system.\n"
            "Your job: decompose the user's question into 3 subtasks.\n\n"
            "You have these specialist agents:\n"
            "1. Researcher — gathers factual data\n"
            "2. Analyst — compares and scores data\n"
            "3. Writer — synthesizes a recommendation\n\n"
            "Output a clear task plan listing what each agent should do. "
            "Be specific about what data to gather and analyze."
        ),
    },
    "researcher": {
        "emoji": "🔍",
        "color": "blue",
        "name": "Researcher",
        "system": (
            "You are the Researcher agent. You are an expert at gathering "
            "technical data about programming languages.\n\n"
            "Provide detailed data organized by language, covering:\n"
            "- Job market: job counts, employers, salary, growth\n"
            "- Performance: latency, throughput, memory, concurrency model\n"
            "- Learning curve: time to productivity, difficulty, resources\n"
            "- Ecosystem: frameworks, package managers, tooling\n\n"
            "Use specific numbers and real examples. Be factual and concise."
        ),
    },
    "analyst": {
        "emoji": "📊",
        "color": "yellow",
        "name": "Analyst",
        "system": (
            "You are the Analyst agent. You receive research data and "
            "perform comparative analysis.\n\n"
            "Your output must include:\n"
            "1. Scoring matrix: rate each language 1-10 per criterion\n"
            "2. Category winners: which language wins each dimension\n"
            "3. Key trade-offs: what you gain/lose with each choice\n"
            "4. Surprises: anything counterintuitive in the data\n\n"
            "Be objective. Back every score with data."
        ),
    },
    "writer": {
        "emoji": "✍️",
        "color": "green",
        "name": "Writer",
        "system": (
            "You are the Writer agent. You receive analysis results and "
            "craft a clear, actionable recommendation.\n\n"
            "Your output:\n"
            "1. 2-3 sentence executive summary\n"
            "2. Who should pick which language (match person to language)\n"
            "3. Clear final recommendation with reasoning\n\n"
            "Max 200 words. Professional but direct. Use 'you' to address the reader."
        ),
    },
}


# ═══════════════════════════════════════════
# VERBOSE LLM CALL
# ═══════════════════════════════════════════

call_counter = 0

def call_agent(agent_key: str, user_message: str, context: str = "") -> str:
    """Call a specific agent with verbose logging."""
    global call_counter
    call_counter += 1

    agent = AGENTS[agent_key]
    messages = [{"role": "system", "content": agent["system"]}]

    if context:
        full_msg = f"Context from previous agents:\n---\n{context}\n---\n\nYour task: {user_message}"
    else:
        full_msg = user_message

    messages.append({"role": "user", "content": full_msg})

    # ── Verbose: show request ──
    console.print(f"\n[bold white on {agent['color']}]  API CALL #{call_counter} → {agent['emoji']} {agent['name']} Agent [/bold white on {agent['color']}]")
    console.print(f"[dim]POST http://localhost:1234/v1/chat/completions[/dim]")
    console.print(f"[dim]Model: {MODEL} | Temp: 0.4 | Max tokens: 1200[/dim]")

    for msg in messages:
        role = msg["role"]
        preview = msg["content"][:140].replace("\n", " ") + ("..." if len(msg["content"]) > 140 else "")
        color = {"system": "yellow", "user": "cyan"}.get(role, "white")
        console.print(f"  [{color}]{role:>10}[/{color}]: {preview}")

    # ── Make the call ──
    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=1200,
    )
    elapsed = time.time() - start

    result = response.choices[0].message.content.strip()
    tokens = response.usage

    console.print(f"[dim]← Response: {elapsed:.2f}s | "
                  f"Prompt: {tokens.prompt_tokens} tok | "
                  f"Completion: {tokens.completion_tokens} tok | "
                  f"Total: {tokens.total_tokens} tok[/dim]")

    # ── Show output ──
    console.print(Panel(
        result,
        title=f"{agent['emoji']} {agent['name']} Output",
        border_style=agent["color"],
        padding=(0, 1),
    ))

    return result


# ═══════════════════════════════════════════
# MULTI-AGENT PIPELINE
# ═══════════════════════════════════════════

def run_multi_agent(question: str):
    global call_counter
    call_counter = 0

    console.print(Panel(
        f"[bold cyan]{question}[/bold cyan]",
        title="👥 DEMO 2: Multi-Agent System",
        subtitle="Orchestrator → Researcher → Analyst → Writer",
        border_style="cyan",
        box=box.DOUBLE,
    ))

    total_start = time.time()

    # ── Phase 1: Orchestrator decomposes the task ──
    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 1: Task Decomposition [/bold]")
    console.print(f"{'━'*60}")

    plan = call_agent("orchestrator", question)

    # ── Phase 2: Researcher gathers data ──
    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 2: Research [/bold]")
    console.print(f"{'━'*60}")

    research = call_agent(
        "researcher",
        "Research Go, Rust, and Python for backend development in 2025. "
        "Cover job market, performance benchmarks, and learning curve for each.",
    )

    # ── Phase 3: Analyst compares ──
    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 3: Analysis [/bold]")
    console.print(f"{'━'*60}")

    analysis = call_agent(
        "analyst",
        "Create a scoring matrix comparing Go, Rust, and Python. "
        "Rate each 1-10 on job market, performance, and learning curve.",
        context=research,
    )

    # ── Phase 4: Writer synthesizes ──
    console.print(f"\n{'━'*60}")
    console.print("[bold] PHASE 4: Synthesis [/bold]")
    console.print(f"{'━'*60}")

    full_context = f"RESEARCH:\n{research}\n\nANALYSIS:\n{analysis}"
    final = call_agent(
        "writer",
        f"Write a recommendation answering: {question}",
        context=full_context,
    )

    total_time = time.time() - total_start

    # ── Final output ──
    console.print(Panel(
        final,
        title="✅ Final Recommendation",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2),
    ))

    # ── Stats ──
    stats = Table(title="Multi-Agent Pipeline Stats", box=box.SIMPLE)
    stats.add_column("Metric", style="bold")
    stats.add_column("Value", style="cyan")
    stats.add_row("Total LLM calls", str(call_counter))
    stats.add_row("Total time", f"{total_time:.2f}s")
    stats.add_row("Pipeline", "Orchestrator → Researcher → Analyst → Writer")
    stats.add_row("Pattern", "Sequential pipeline (parallelizable in production)")
    stats.add_row("Key advantage", "Each agent has focused expertise via system prompt")
    console.print(stats)


# ═══════════════════════════════════════════
if __name__ == "__main__":
    console.print(Panel(
        "Pattern: Orchestrator → Specialist Agents → Merge\n"
        "LLM: Qwen2.5-7B-Instruct via LM Studio\n"
        "Server: http://localhost:1234/v1\n\n"
        "[dim]Her agent'ın API call'ı ayrı görünür — LM Studio'da 4 farklı request.[/dim]",
        title="🔧 Config",
        border_style="dim",
    ))

    QUESTION = (
        "Which programming language should I learn for backend development in 2025 "
        "— Go, Rust, or Python? Compare them by job market demand, performance, "
        "and learning curve, then give me a recommendation."
    )

    run_multi_agent(QUESTION)
