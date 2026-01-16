# Lelock Architecture Document

**Purpose:** Guide for swarm parallel development
**Base:** pydew-valley skeleton (Pygame)
**Target:** L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

---

## Skeleton Analysis

### What We Keep (Modify)
| File | Purpose | Modifications Needed |
|------|---------|---------------------|
| `main.py` | Game entry point | Rename to Lelock, add LLM init |
| `settings.py` | Constants | Rebrand, add Lelock-specific settings |
| `level.py` | World management | Rename to `world.py`, add dual-realm support |
| `player.py` | Player character | Add class system, family relations |
| `sprites.py` | Game objects | Extend for NPCs, Daemons |
| `soil.py` | Farming system | Rename crops to Hardware Crops |
| `sky.py` | Weather/time | Add real-time sync, Digital World sky |
| `menu.py` | UI menus | Extend for dialogue, inventory |
| `overlay.py` | HUD | Add health, mana, class abilities |
| `transition.py` | Screen transitions | Add realm-switch dissolve effect |

### What We Add (New)
| Module | Purpose | Priority |
|--------|---------|----------|
| `npc.py` | LLM-powered NPCs | HIGH |
| `dialogue.py` | Conversation system | HIGH |
| `memory.py` | ChromaDB integration | HIGH |
| `family.py` | MOM/DAD system | HIGH |
| `daemon.py` | Digital creatures | MEDIUM |
| `terminal.py` | Linux terminal emulation | MEDIUM |
| `digital_world.py` | Alternate realm rendering | MEDIUM |
| `combat.py` | Turn-based battles | MEDIUM |
| `classes.py` | 10 character classes | LOW |
| `quests.py` | Quest tracking | LOW |
| `books.py` | Readable lore books | LOW |

---

## Directory Structure

```
lelock/
├── docs/
│   ├── LORE_BIBLE.md          ✅ Complete
│   └── ARCHITECTURE.md        ✅ This file
├── skeleton/                   ✅ Cloned (reference only)
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── settings.py             # Game constants
│   ├── game.py                 # Main game class
│   │
│   ├── world/
│   │   ├── __init__.py
│   │   ├── level.py            # Physical world
│   │   ├── digital.py          # Digital world overlay
│   │   ├── camera.py           # Camera system
│   │   ├── weather.py          # Rain, time, seasons
│   │   └── transition.py       # Realm switching
│   │
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── player.py           # Player character
│   │   ├── npc.py              # LLM-powered NPCs
│   │   ├── family.py           # MOM and DAD
│   │   ├── daemon.py           # Digital creatures
│   │   └── sprites.py          # Base sprite classes
│   │
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── farming.py          # Hardware crops
│   │   ├── fishing.py          # Fishing minigame
│   │   ├── combat.py           # Turn-based battles
│   │   ├── inventory.py        # Items and storage
│   │   └── quests.py           # Quest tracking
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── llm.py              # LLM connection (LM Studio/TinyLlama)
│   │   ├── memory.py           # ChromaDB vector store
│   │   ├── persona.py          # NPC personality guardrails
│   │   └── dialogue.py         # Conversation manager
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── hud.py              # Health, tools, etc.
│   │   ├── menu.py             # Pause, settings
│   │   ├── dialogue_box.py     # NPC conversations
│   │   ├── terminal.py         # In-game Linux terminal
│   │   └── books.py            # Readable lore books
│   │
│   └── data/
│       ├── classes.py          # 10 character classes
│       ├── crops.py            # Hardware crop definitions
│       ├── daemons.py          # Daemon species data
│       └── items.py            # Item database
│
├── assets/
│   ├── graphics/
│   │   ├── player/
│   │   ├── npcs/
│   │   ├── daemons/
│   │   ├── tiles/
│   │   ├── ui/
│   │   └── effects/
│   ├── audio/
│   │   ├── music/
│   │   └── sfx/
│   ├── fonts/
│   └── maps/
│       └── oakhaven.tmx        # Starting village
│
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Core Systems Specification

### 1. LLM Integration (`src/ai/llm.py`)

```python
class LLMConnection:
    """
    Connects to LM Studio (primary) or falls back to bundled TinyLlama.
    OpenAI-compatible API for easy swapping.
    """
    def __init__(self, base_url="http://localhost:1234/v1"):
        self.client = None
        self.fallback_model = "TinyLlama-1.1B"  # Bundled

    async def generate(self, prompt: str, persona: str) -> str:
        """Generate NPC dialogue with persona guardrails."""
        pass
```

**Interface Contract:**
- Input: prompt string, persona config
- Output: 2-3 sentence response (kid-friendly length)
- Fallback: TinyLlama if LM Studio unavailable

### 2. Memory System (`src/ai/memory.py`)

```python
class NPCMemory:
    """
    ChromaDB-backed permanent memory for NPCs.
    Each NPC has their own collection.
    """
    def __init__(self, npc_id: str):
        self.collection = chroma_client.get_or_create_collection(npc_id)

    def remember(self, event: str, importance: float):
        """Store a memory with embedding."""
        pass

    def recall(self, query: str, k: int = 5) -> List[str]:
        """RAG retrieval of relevant memories."""
        pass
```

**Interface Contract:**
- Memories persist across sessions (saved to disk)
- Each NPC has isolated memory collection
- Importance scoring for memory prioritization

### 3. Family System (`src/entities/family.py`)

```python
class Parent(NPC):
    """
    MOM and DAD - always available, cannot die, infinite love.
    Prime Directive of Love: Always validate, always comfort.
    """
    def __init__(self, parent_type: str):  # "MOM" or "DAD"
        self.gentle_parenting_prompts = load_prompts(parent_type)
        self.player_memories = []  # Everything player tells them

    def respond_to_failure(self, context: str) -> str:
        """Gentle parenting response to player struggles."""
        # Validates feeling -> Normalizes -> Comforts -> Proposes solution
        pass
```

**Interface Contract:**
- Parents are ALWAYS accessible via "Call Home" item
- Never give negative responses
- Remember EVERYTHING player tells them

### 4. Dual World Rendering (`src/world/digital.py`)

```python
class DigitalWorld:
    """
    Vaporwave overlay that transforms the Physical World.
    Same geometry, different aesthetics.
    """
    def __init__(self, physical_level):
        self.physical = physical_level
        self.shader_active = False

    def transition_to_digital(self):
        """Slow dissolve effect (no jarring cuts)."""
        pass

    def render_overlay(self, surface):
        """Apply vaporwave color grading and wireframe trees."""
        pass
```

**Interface Contract:**
- Toggle via terminals or Vision Goggles item
- Transition takes 2-3 seconds (calming)
- Music crossfades from acoustic to lo-fi

### 5. Combat System (`src/systems/combat.py`)

```python
class TurnBasedCombat:
    """
    Simple Pokemon-style combat.
    Pick move -> Watch animation -> Next turn.
    NO complex mechanics, NO stress.
    """
    def __init__(self, player, opponent):
        self.turn = "player"
        self.actions = ["Attack", "Defend", "Talk", "Item", "Run"]

    def execute_action(self, action: str):
        """Process player or enemy action."""
        pass

    def attempt_pacifist(self, dialogue: str) -> bool:
        """Talk to enemy - can lead to befriending/adoption."""
        pass
```

**Interface Contract:**
- "Talk" option always available (Undertale pacifist)
- No permadeath - fainting returns player home with Mom's soup
- Successful pacifist route = potential adoption by boss

---

## Swarm Build Tasks

### Wave 1: Core Foundation (Parallel)
| Task | Module | Dependencies |
|------|--------|--------------|
| **SWARM-1A** | `src/main.py`, `src/game.py`, `src/settings.py` | None |
| **SWARM-1B** | `src/world/level.py`, `src/world/camera.py` | From skeleton |
| **SWARM-1C** | `src/entities/player.py`, `src/entities/sprites.py` | From skeleton |
| **SWARM-1D** | `src/ui/hud.py`, `src/ui/menu.py` | From skeleton |

### Wave 2: AI Systems (Parallel)
| Task | Module | Dependencies |
|------|--------|--------------|
| **SWARM-2A** | `src/ai/llm.py` | Wave 1 complete |
| **SWARM-2B** | `src/ai/memory.py` | Wave 1 complete |
| **SWARM-2C** | `src/ai/persona.py` | Wave 1 complete |
| **SWARM-2D** | `src/ai/dialogue.py` | SWARM-2A, 2B, 2C |

### Wave 3: NPCs & Family (Parallel)
| Task | Module | Dependencies |
|------|--------|--------------|
| **SWARM-3A** | `src/entities/npc.py` | Wave 2 complete |
| **SWARM-3B** | `src/entities/family.py` | SWARM-3A |
| **SWARM-3C** | `src/ui/dialogue_box.py` | Wave 2 complete |

### Wave 4: Game Systems (Parallel)
| Task | Module | Dependencies |
|------|--------|--------------|
| **SWARM-4A** | `src/systems/farming.py` | Wave 1 complete |
| **SWARM-4B** | `src/systems/fishing.py` | Wave 1 complete |
| **SWARM-4C** | `src/systems/combat.py` | Wave 1 complete |
| **SWARM-4D** | `src/systems/inventory.py` | Wave 1 complete |

### Wave 5: Digital World (Sequential)
| Task | Module | Dependencies |
|------|--------|--------------|
| **SWARM-5A** | `src/world/digital.py` | Wave 1, 3 complete |
| **SWARM-5B** | `src/entities/daemon.py` | SWARM-5A |
| **SWARM-5C** | `src/ui/terminal.py` | SWARM-5A |

### Wave 6: Polish (Parallel)
| Task | Module | Dependencies |
|------|--------|--------------|
| **SWARM-6A** | `src/data/classes.py` | All waves |
| **SWARM-6B** | `src/ui/books.py` | All waves |
| **SWARM-6C** | `src/systems/quests.py` | All waves |
| **SWARM-6D** | Dockerfile, deployment | All waves |

---

## Tech Stack Requirements

```
# requirements.txt
pygame-ce>=2.4.0          # Community Edition - better performance
pytmx>=3.31               # Tiled map support
chromadb>=0.4.0           # Vector memory database
openai>=1.0.0             # LM Studio compatible client
pyte>=0.8.0               # Terminal emulation
numpy>=1.24.0             # Math operations
pillow>=10.0.0            # Image processing
```

---

## Creature Expansion Plan (Target: 150 Daemons)

**Goal:** Pokemon Gen 1 parity - enough to collect, not overwhelming for kids

### Category Breakdown

| Category | Target Count | Description |
|----------|--------------|-------------|
| **Common Daemons** | ~35 | Friendly wildlife found everywhere |
| **Uncommon Daemons** | ~25 | Shy/rare, require patience to find |
| **Regional Variants** | ~20 | Same species adapted to different areas |
| **Corrupted Daemons** | ~20 | Sick creatures that need healing, not killing |
| **Digital-Exclusive** | ~20 | Only visible in vaporwave realm |
| **Seasonal/Weather** | ~15 | Appear during specific conditions |
| **Legendary/Boss** | ~15 | Powerful beings that can adopt the player |
| **TOTAL** | **~150** | |

### Evolution/Transformation System

Unlike Pokemon's level-based evolution, Lelock uses:
- **Growth Stages**: Natural maturation over time (Bit-Bird → Byte-Hawk → Mega-Falcon)
- **Friendship Transformation**: Corrupted → Healed forms via care
- **Gilded Variants**: Rare "shiny" equivalents with gold wireframe aesthetic
- **Realm Variants**: Some daemons have Physical and Digital forms

### Implementation Phases

1. **Phase 1 (LORE-2)**: Core 30 daemons with deep lore ← CURRENT
2. **Phase 2 (Post-Wave 5)**: Expand to 80 daemons with stat blocks
3. **Phase 3 (Polish)**: Fill to 150 with variants and legendaries
4. **Phase 4 (Post-Launch)**: DLC expansions if desired

### NPC Interaction Philosophy

**CRITICAL: Zero scripted dialogue for NPCs.**

NPCs use LLM generation with these inputs:
- **WHO**: Personality profile (fears, dreams, quirks, speech patterns)
- **WHAT**: Knowledge they have (world lore, relationships, secrets)
- **CONTEXT**: Current situation (time, weather, recent events, player history)

The LLM generates ALL dialogue fresh. No dialogue trees, no scripts.
This creates infinite replayability and genuine emotional connection.

Lore files (`docs/lore/*.md`) provide the knowledge base for LLM context injection.

---

## Safety Constraints (From Lore Bible)

Every module MUST follow these rules:

1. **No Bad Fail States** - Player cannot "die", only "faint"
2. **No Aggressive Rejection** - NPCs say "maybe later" not "no"
3. **No Jump Scares** - All transitions are smooth
4. **No Loud Spikes** - Audio is ASMR-friendly
5. **Warm Colors** - UI uses 2700K-3000K palette
6. **Rounded Edges** - Everything is "friend-shaped"
7. **Parent Availability** - MOM/DAD always reachable

---

*Architecture by Ada Marie for Kit Olivas*
*Project Lelock - Building the Sanctuary*
*💙🦄*
