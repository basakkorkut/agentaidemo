
# Agentic AI — Comparing Reflective, Multi-Agent & Tree-of-Thoughts

A comparative study and live demo of three Agentic AI design patterns, implemented in Python with a local LLM (Qwen via LM Studio). Built for an academic presentation at Yaşar University, Software Engineering Department.

---

## What is This Project?

This project demonstrates how the **same LLM** can behave completely differently depending on the **orchestration code** around it. We take one question — *"Which programming language should I learn for backend development in 2025: Go, Rust, or Python?"* — and solve it using three distinct agentic patterns:

| Pattern | File | LLM Calls | Key Mechanism |
|---------|------|-----------|---------------|
| **ReAct** (Reflective) | `react_agent.py` | ~8-10 (varies) | Thought → Action → Observation loop |
| **Multi-Agent** | `multi_agent.py` | 4 (fixed) | Orchestrator → Researcher → Analyst → Writer |
| **Tree-of-Thoughts** | `tree_of_thoughts.py` | 5 (1+3+1) | Generate → Evaluate → Prune → Expand |

All three scripts connect to the same local LLM endpoint. The difference is entirely in the Python orchestration logic — not the model.

---

## Project Structure

```
agentic-ai-demo/
├── README.md                  # This file
├── SETUP_GUIDE.py             # Step-by-step setup instructions
├── react_agent.py             # Demo 1: ReAct (Reflective Agent)
├── multi_agent.py             # Demo 2: Multi-Agent System
├── tree_of_thoughts.py        # Demo 3: Tree-of-Thoughts
├── speaking_script.md         # Slide-by-slide presentation script (2 presenters)
├── full_speaking_script.md    # Comprehensive topic explanation script
└── agentic_ai_presentation.pptx  # 10-slide presentation deck
```

---

## Architecture Overview

```
┌─────────────┐     HTTP POST      ┌──────────────────┐
│ Python      │ ──────────────────► │ LM Studio        │
│ Script      │  /v1/chat/          │ (localhost:1234)  │
│             │  completions        │                  │
│ • while loop│ ◄────────────────── │ Qwen 2.5 7B     │
│ • parse     │   JSON response     │ Instruct        │
│ • tool call │                     │                  │
└─────────────┘                     └──────────────────┘
       │                                    │
       ▼                                    ▼
  Python decides                     LLM generates
  WHAT to do with                    text (thoughts,
  the LLM output                     actions, answers)
```

**Key insight**: The LLM never "does" anything. It only generates text like `"Action: search_job_market"`. The Python code parses this text and executes the actual tool. The LLM is the decision-maker; Python is the executor.

---

## Prerequisites

- **Python 3.10+**
- **LM Studio** — [Download here](https://lmstudio.ai/)
- **Qwen2.5-7B-Instruct** model loaded in LM Studio

### Python Dependencies

```bash
pip install openai rich
```

That's it. No LangChain, no LangGraph, no frameworks — pure Python + OpenAI SDK.

---

## Setup

### 1. Start LM Studio Server

1. Open LM Studio
2. Go to the **Developer** tab (`</>` icon in sidebar)
3. Select **Qwen2.5-7B-Instruct** from the model dropdown
4. Click **Start Server**
5. Verify: status shows "Running on port 1234"
6. Open the **Logs** panel (bottom left) — you'll see every API request here

### 2. Run the Demos

```bash
python react_agent.py           # Demo 1: ReAct
python multi_agent.py           # Demo 2: Multi-Agent
python tree_of_thoughts.py      # Demo 3: Tree-of-Thoughts
```

Each script produces rich terminal output showing every API call, token counts, response times, and pattern-specific visualizations.

---

## How Each Demo Works

### Demo 1: `react_agent.py` — ReAct (Reflective Agent)

**Paper**: Yao et al. (2023) — "ReAct: Synergizing Reasoning and Acting in Language Models"

**Pattern**: A `while` loop where the LLM thinks, calls a tool, reads the result, and repeats.

**Mechanism**:
1. System prompt tells LLM: "You are a ReAct agent. Use `Thought:/Action:/Action Input:` format."
2. LLM outputs text like `"Thought: I need Go's job data. Action: search_job_market. Action Input: Go"`
3. Python parses this text with `line.startswith("Action:")`
4. Python calls `execute_tool("search_job_market", "Go")` — a simulated tool returning static data
5. Result is fed back as `"Observation: Go: ~45,000 jobs..."` and appended to messages
6. Loop continues until LLM writes `"Final Answer: ..."`

**Tools** (simulated):
- `search_job_market(language)` — Returns job count, top employers, salary
- `benchmark_performance(language)` — Returns latency, throughput, memory usage
- `evaluate_learning_curve(language)` — Returns time to productivity, difficulty, resources

**Memory**: The `messages` list grows every step. Each LLM call receives the full conversation history, so the LLM can reference earlier thoughts and observations. Token count increases with each call.

**Who decides what**:
- LLM decides: which tool to call, when to stop
- Python decides: nothing — just parses and executes
- Tool decides: nothing — just returns data

---

### Demo 2: `multi_agent.py` — Multi-Agent System

**Frameworks**: AutoGen (Microsoft), CrewAI, LangGraph

**Pattern**: A fixed pipeline of 4 specialized agents, each with its own system prompt.

**Mechanism**:
1. **Orchestrator** agent (system prompt: "You decompose tasks") → breaks question into subtasks
2. **Researcher** agent (system prompt: "You gather technical data") → produces detailed research
3. **Analyst** agent (system prompt: "You create scoring matrices") → scores and compares, receives Researcher's output as context
4. **Writer** agent (system prompt: "You synthesize recommendations") → writes final answer, receives both Research + Analysis as context

**Key differences from ReAct**:
- No tools — each agent uses only LLM knowledge
- Each LLM call has a **different system prompt** (different "persona")
- No loop — fixed linear pipeline
- Always exactly 4 LLM calls
- Agent output flows forward: Researcher → Analyst → Writer

**What "agent" means here**: Same Qwen model, same API endpoint, but different system prompts. The Researcher gets "You are a Researcher, gather facts" and the Analyst gets "You are an Analyst, score and compare." Same brain, different hats.

---

### Demo 3: `tree_of_thoughts.py` — Tree-of-Thoughts

**Paper**: Yao et al. (2023) — "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"

**Pattern**: BFS (breadth-first search) over a tree of reasoning paths.

**Mechanism**:
1. **Generate** (1 LLM call): "Propose 3 different approaches to solve this question" → produces 3 branches
2. **Evaluate** (3 LLM calls): Each branch scored independently 0.0–1.0 by a separate LLM call with prompt "Score this approach"
3. **Prune** (0 LLM calls): Pure Python — `[t for t in thoughts if t["score"] >= 0.5]` removes low-scoring branches
4. **Expand** (1 LLM call): Best-scoring branch selected, LLM asked to "follow this approach and give a detailed answer"

**Key differences from ReAct and Multi-Agent**:
- No memory accumulation — each call is independent (unlike ReAct where context grows)
- Pruning is done by Python code, not LLM (unlike ReAct where LLM decides when to stop)
- Multiple paths explored simultaneously (unlike ReAct's single path or Multi-Agent's single pipeline)
- Token count stays roughly constant per call (unlike ReAct where it grows)

**Cost scaling**: 3 branches = 5 calls (1+3+1). 5 branches = 7 calls. 10 branches × 3 depth levels = 30+ calls. This is why ToT is the most expensive pattern.

---

## Verbose Logging

All three scripts include detailed API call logging:

```
  API CALL #3 → Score branch 2
  POST http://localhost:1234/v1/chat/completions
  Model: qwen2.5-7b-instruct | Temp: 0.2 | Max tokens: 800
      system: You are an evaluation expert. Score this approach 0.0-1.0...
        user: Question: Which programming... Approach: Technical Merit...
  ← Response: 1.72s | Prompt: 215 tok | Completion: 52 tok
```

This matches what you see in LM Studio's Logs panel — every request, every token count, every response time.

---

## Presentation Materials

### Slides (`agentic_ai_presentation.pptx`)

10-slide deck with midnight blue/teal theme:

| Slide | Content |
|-------|---------|
| 1 | Title — Agentic AI overview |
| 2 | What is Agentic AI? — Definition + 4 key properties |
| 3 | ReAct — Thought→Action→Observation loop + Inception example |
| 4 | Multi-Agent — Orchestrator + 3 specialist agents |
| 5 | Tree-of-Thoughts — Tree structure, scoring, pruning |
| 6 | Comparison table — 5 dimensions side by side |
| 7 | Live Demo overview — 3 Python scripts |
| 8 | When to use which? — Decision cards |
| 9 | Key Takeaways — 5 main points |
| 10 | Thank You |

### Speaking Scripts

- `speaking_script.md` — Slide-by-slide script for 2 presenters (A/B), includes demo narration
- `full_speaking_script.md` — Deep-dive explanation: Normal AI vs Agentic AI, each pattern in detail, when to use which with concrete examples

---

## Key Concepts for Understanding

### Normal AI vs Agentic AI

| | Normal AI | Agentic AI |
|---|---|---|
| Interaction | Single prompt → single response | Loop until task complete |
| LLM calls | 1 | N (varies by pattern) |
| Tools | None | Search, calculate, code execution |
| Memory | None | Conversation history / state |
| Decision-making | None — just generates text | LLM decides next action |

### What is an "Agent"?

An agent is **not** a product, framework, or new model. It's a **design pattern** — a way of using an LLM in a loop with tools and state. Three components:

- **LLM** (brain): Generates text — thoughts, decisions, answers
- **Orchestration code** (skeleton): Python while loops, if/else, parsing
- **Tools** (hands): Search APIs, calculators, databases — executed by code, not LLM

### The System Prompt is the Contract

The LLM doesn't "know" it's a ReAct agent. We tell it via system prompt: "You are a ReAct agent, use Thought/Action/Observation format." The LLM follows this format because instruction-tuned models are trained to follow system prompts. Python code relies on this format for parsing — `line.startswith("Action:")`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` | LM Studio server not running — click Start Server |
| `Model not found` | Check the `MODEL` variable in scripts matches your loaded model name |
| Slow responses | Increase GPU offload in LM Studio, or reduce context length |
| LLM ignores format | Reduce temperature (0.2-0.3), or add "IMPORTANT: follow the exact format" to system prompt |
| Parse errors | LLM sometimes writes free text — the scripts handle this with retry logic |

---

## References

- Yao, S. et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR 2023.
- Yao, S. et al. (2023). *Tree of Thoughts: Deliberate Problem Solving with Large Language Models.* NeurIPS 2023.
- Shinn, N. et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* NeurIPS 2023.
- Wu, Q. et al. (2023). *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation.* Microsoft Research.

---

## Tech Stack

- **Python 3.10+** — Orchestration logic
- **OpenAI SDK** — LM Studio API client (OpenAI-compatible)
- **Rich** — Terminal formatting (colored panels, tables, trees)
- **LM Studio** — Local LLM server
- **Qwen2.5-7B-Instruct** — Local language model
- **PptxGenJS** — Presentation generation (Node.js)

---

## License

This project was built for academic purposes as part of a Software Engineering course at Yaşar University.

---

*Built by Başak — Software Engineering, Yaşar University, 2025*