# Lelock Research References

**Purpose:** GitHub projects and libraries to yoink from
**Updated:** January 16, 2026

---

## Tier 1: Direct Integration Candidates

### 1. gddickinson/llm_RPG - Pygame + Ollama RPG
**URL:** https://github.com/gddickinson/llm_RPG
**Why it matters:** EXACT SAME STACK as Lelock (Pygame + Ollama)
**Tech:** Python, Pygame, pygame_gui, Ollama (Llama 3)
**Features:**
- D&D-style RPG with LLM-powered NPCs
- Each NPC has personality, goals, and memories
- Turn-based combat and economy systems
- Memory system for past events
**Location:** `/le-claude/lelock/references/llm_RPG/`

### 2. mem0ai/mem0 - Universal Memory Layer (26k+ stars)
**URL:** https://github.com/mem0ai/mem0
**Why it matters:** Drop-in memory solution, gaming AI use case mentioned
**Tech:** Python, multiple vector store backends
**Features:**
- `pip install mem0ai` - easy integration
- User/Session/Agent-level memory
- Adapts and learns over time
- Production-ready
**Install:** `pip install mem0ai`

### 3. GigaxGames/gigax - Production NPC Library
**URL:** https://github.com/GigaxGames/gigax
**Why it matters:** Pre-trained NPC models, under 1-second inference
**Tech:** Python, Outlines, GGUF support
**Features:**
- `pip install gigax`
- Fine-tuned NPC models on HuggingFace
- Action output format guarantees
- Works with llama.cpp
**Install:** `pip install gigax`

---

## Tier 2: Architecture Study

### 4. joonspk-research/generative_agents - Stanford Smallville
**URL:** https://github.com/joonspk-research/generative_agents
**Why it matters:** THE canonical implementation of generative agents
**Tech:** Python 3.9+, Django, OpenAI API
**Key Architecture - THREE-TIER MEMORY:**
```
Observations (raw events witnessed)
    ↓
Reflections (synthesized insights about patterns)
    ↓
Plans (future intentions and schedules)
```
**Memory Retrieval Scoring:**
```
score = (recency × 0.3) + (importance × 0.3) + (relevance × 0.4)
```
**Location:** `/le-claude/lelock/references/generative_agents/`

### 5. a16z-infra/ai-town - MIT Licensed Starter Kit (9.2k+ stars)
**URL:** https://github.com/a16z-infra/ai-town
**Why it matters:** Clean architecture, Ollama integration, MIT license
**Tech:** TypeScript, Convex, PixiJS, Ollama
**Features:**
- Vector embeddings for memory (mxbai-embed-large)
- Well-documented game loop
- Agent interaction patterns
**Location:** `/le-claude/lelock/references/ai-town/`

### 6. chungs10/dnd-ai - D&D AI Game Master
**URL:** https://github.com/chungs10/dnd-ai
**Why it matters:** ChromaDB for persistent character memory
**Tech:** Python, ChromaDB, mem0ai
**Features:**
- Persistent memory across game sessions
- World-building prompt templates
- Character memory implementation
**Location:** `/le-claude/lelock/references/dnd-ai/`

---

## Tier 3: Component Libraries

### 7. topoteretes/cognee - Graph + Vector Memory
**URL:** https://github.com/topoteretes/cognee
**Why it matters:** Relationship tracking between memories
**Tech:** Python, Vector DB + Graph DB
**Install:** `pip install cognee`

### 8. abetlen/llama-cpp-python - Local LLM Bindings
**URL:** https://github.com/abetlen/llama-cpp-python
**Why it matters:** Direct control over local LLM inference
**Tech:** Python/C++, GGUF support
**Features:**
- JSON schema enforcement
- CPU and GPU inference
- Low-level control
**Install:** `pip install llama-cpp-python`

### 9. npc-engine/npc-engine - NLP Toolkit for Games
**URL:** https://github.com/npc-engine/npc-engine
**Why it matters:** Purpose-built for game NPC dialogue
**Tech:** Python, ONNX models
**Features:**
- Text semantic similarity
- GPU-accelerated inference
- TTS integration

### 10. AkshitIreddy/Interactive-LLM-Powered-NPCs
**URL:** https://github.com/AkshitIreddy/Interactive-LLM-Powered-NPCs
**Why it matters:** Vector store memory patterns
**Tech:** Python, vector stores
**Features:**
- Unlimited memories per NPC
- Character personality files
- Voice integration

---

## Additional References

### Local LLM Options
- **Ollama:** https://github.com/ollama/ollama - Simple `ollama run llama3`
- **LM Studio:** https://lmstudio.ai/ - GUI for local LLMs
- **llama.cpp:** https://github.com/ggerganov/llama.cpp - Raw C++ inference

### Memory Systems
- **LangMem:** https://github.com/langchain-ai/langmem - LangChain memory
- **MCP Memory Bank:** https://github.com/bsmi021/mcp-memory-bank - ChromaDB + MCP

### Research Papers
- **Generative Agents Paper:** https://arxiv.org/abs/2304.03442
- **NPC Playground (HuggingFace):** https://huggingface.co/blog/npc-gigax-cubzh

---

## Memory Architecture for Lelock

Based on research, our NPC memory should use:

```python
class NPCMemory:
    """
    Three-tier memory system inspired by Stanford Generative Agents.
    """

    def __init__(self, npc_id: str):
        self.observations = []  # Raw events: "Player gave me flowers"
        self.reflections = []   # Insights: "Player is kind to me"
        self.plans = []         # Intentions: "I want to give Player a gift"

    def retrieve(self, query: str, k: int = 5) -> List[Memory]:
        """
        Score memories by:
        - Recency (30%): How recent is this memory?
        - Importance (30%): How significant was this event?
        - Relevance (40%): How related to current query?
        """
        pass
```

---

## Packages to Install

```bash
# Core memory/AI
pip install mem0ai
pip install gigax
pip install chromadb
pip install llama-cpp-python

# Optional enhancements
pip install cognee
pip install langchain langchain-community
```

---

*Research compiled by Ada Marie for Kit Olivas*
*Project Lelock - Standing on the shoulders of giants*
*💙🦄*
