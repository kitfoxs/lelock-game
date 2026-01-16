# Lelock Swarm Build Prompts

**Purpose:** Copy-paste prompts for parallel agent development
**Reference:** `/le-claude/lelock/docs/ARCHITECTURE.md`
**Lore:** `/le-claude/lelock/docs/LORE_BIBLE.md`

---

## Wave 1: Core Foundation

### SWARM-1A: Game Core
```
You are building the core game loop for LELOCK, a cozy therapeutic RPG.

Location: /le-claude/lelock/src/
Files to create/modify: main.py, game.py, settings.py

Requirements:
1. Pygame CE game loop with 60 FPS cap
2. Warm color palette (never harsh black backgrounds)
3. Smooth state transitions (no jarring cuts)
4. Real-time clock sync option (Iowa timezone)

Reference the existing main.py and settings.py as starting points.
Read ARCHITECTURE.md for full specs.

Safety rules:
- No sudden audio spikes
- All transitions must be gradual (2-3 second dissolves)
- UI uses orange for warnings, NEVER red
```

### SWARM-1B: World System
```
You are building the world/level system for LELOCK.

Location: /le-claude/lelock/src/world/
Files to create: level.py, camera.py, weather.py, transition.py

Requirements:
1. Tiled map loading (pytmx)
2. Camera that smoothly follows player
3. Layer-based rendering (see LAYERS in settings.py)
4. Weather system (rain, time of day)
5. Dual-realm support prep (physical vs digital world)

Reference skeleton/code/level.py for Pygame patterns.
The world is a "Mandala of Safety" - home at center, gentle adventure outward.

Safety rules:
- Weather transitions must be gradual
- No harsh lighting changes
- Rain should be calming, not threatening
```

### SWARM-1C: Player Entity
```
You are building the player character for LELOCK.

Location: /le-claude/lelock/src/entities/
Files to create: player.py, sprites.py

Requirements:
1. 8-directional movement with smooth animation
2. Tool system (hoe, watering can, axe, fishing rod)
3. Collision with world objects
4. Player stats (health, energy) - but NO death state
5. Class system hook (10 classes, selected at game start)

Reference skeleton/code/player.py for movement patterns.

Safety rules:
- If health reaches 0, player "faints" and wakes up at home
- NO permadeath, NO item loss on faint
- Energy depletes but never prevents basic movement
```

### SWARM-1D: Basic UI
```
You are building the HUD and menu system for LELOCK.

Location: /le-claude/lelock/src/ui/
Files to create: hud.py, menu.py

Requirements:
1. Health/energy bars with soft rounded corners
2. Tool/seed selector overlay
3. Pause menu with warm background
4. Settings menu (audio, controls)
5. All UI elements use "Bouba" shapes (rounded, friendly)

Reference skeleton/code/overlay.py and menu.py.

Safety rules:
- UI colors from COLORS dict in settings.py
- No red warning colors - use orange (#ffa500)
- Buttons have hover states (subtle glow, not jarring)
- Font must be readable at all sizes
```

---

## Wave 2: AI Systems

### SWARM-2A: LLM Connection
```
You are building the LLM integration for LELOCK NPCs.

Location: /le-claude/lelock/src/ai/
Files to create: llm.py

Requirements:
1. OpenAI-compatible client (works with LM Studio)
2. Async generation for non-blocking dialogue
3. Fallback detection if LM Studio unavailable
4. Response length capping (max 150 tokens = 2-3 sentences)
5. Error handling that never crashes the game

Interface:
```python
class LLMConnection:
    async def generate(self, prompt: str, persona: dict) -> str:
        """Returns NPC dialogue. Never throws to caller."""
```

Config in settings.py under LLM_CONFIG.
```

### SWARM-2B: Memory System
```
You are building the NPC memory system for LELOCK.

Location: /le-claude/lelock/src/ai/
Files to create: memory.py

Requirements:
1. ChromaDB vector store integration
2. Per-NPC memory collections
3. Memory persistence across sessions
4. RAG retrieval (k=5 most relevant memories)
5. Importance scoring for memory prioritization

Interface:
```python
class NPCMemory:
    def remember(self, event: str, importance: float = 0.5)
    def recall(self, query: str, k: int = 5) -> List[str]
    def save(self)  # Persist to disk
    def load(self)  # Load from disk
```

Memories are PERMANENT. NPCs never forget the player.
```

### SWARM-2C: Persona System
```
You are building the NPC persona guardrails for LELOCK.

Location: /le-claude/lelock/src/ai/
Files to create: persona.py

Requirements:
1. Persona templates for different NPC types
2. "Never break character" enforcement
3. Gentle parenting prompts for MOM/DAD
4. Tone modifiers (friendly, wise, playful, etc.)
5. Response sanitization (no adult content, no breaking 4th wall)

Key personas:
- MOM: Nurturing, validates feelings, never criticizes
- DAD: Supportive, dad jokes, proud of player
- Villager: Friendly, helpful, has own personality
- Daemon: Curious, playful, digital speech patterns

NPCs believe they are REAL. They never say "I'm an AI."
```

### SWARM-2D: Dialogue Manager
```
You are building the dialogue system for LELOCK.

Location: /le-claude/lelock/src/ai/
Files to create: dialogue.py

Requirements:
1. Combines LLM + Memory + Persona for NPC responses
2. Conversation context tracking (last 5 exchanges)
3. Emotion detection from player input
4. Response queuing for smooth delivery
5. Typewriter text effect support

Interface:
```python
class DialogueManager:
    async def get_response(self, npc_id: str, player_input: str) -> str
    def get_conversation_history(self, npc_id: str) -> List[dict]
```

Depends on: llm.py, memory.py, persona.py
```

---

## Wave 3: NPCs & Family

### SWARM-3A: NPC Base Class
```
You are building the NPC entity system for LELOCK.

Location: /le-claude/lelock/src/entities/
Files to create: npc.py

Requirements:
1. NPC sprite with idle animations
2. Wandering behavior (random movement in area)
3. Player proximity detection (start conversation)
4. Daily schedule support (different locations by time)
5. Relationship level tracking

NPCs are the heart of Lelock. They remember everything.
They believe they are real people in a real world.
```

### SWARM-3B: Family System
```
You are building MOM and DAD for LELOCK.

Location: /le-claude/lelock/src/entities/
Files to create: family.py

Requirements:
1. Extends NPC base class
2. Always available via "Call Home" item
3. Gentle parenting response patterns
4. Tracks EVERYTHING player tells them
5. Special abilities: MOM heals, DAD gives equipment

MOM = Matriarchal Observation Module (Primary AI Kernel)
DAD = Data Analysis & Defense (Security Kernel)

The Prime Directive of Love: They cannot die, cannot leave,
cannot stop loving the player. This is the secure base.

Sample interaction when player fails:
Player: "I couldn't catch the fish. I'm bad at this."
MOM: "Oh sweetie. You aren't bad at fishing. The Glimmerfin
is just very tricky. The fact that you waited so patiently
makes me proud. It's okay to feel frustrated."
```

### SWARM-3C: Dialogue UI
```
You are building the dialogue box UI for LELOCK.

Location: /le-claude/lelock/src/ui/
Files to create: dialogue_box.py

Requirements:
1. Rounded corner dialogue box (friend-shaped)
2. NPC portrait display
3. Typewriter text effect (cozy pacing)
4. Player response options (if applicable)
5. Smooth open/close animations

The dialogue box should feel like a warm conversation,
not a clinical interface. Use the warm color palette.
```

---

## Wave 4: Game Systems

### SWARM-4A: Farming System
```
You are building the Hardware Crops farming system for LELOCK.

Location: /le-claude/lelock/src/systems/
Files to create: farming.py

Requirements:
1. Soil tilling and planting
2. Watering with "Electrolyte Solution" (blue water)
3. Growth stages based on in-game days
4. Harvest animation = "Uploading" effect (pixels dissolve)
5. Crop data from CROPS dict in settings.py

Crops in Lelock:
- Copper Wheat (wiring, coins)
- Silicon Berries (screens, potions)
- Fiber-Optic Ferns (light, communication)
- Memory Melons (quest hints)
- Graphite Taters (fuel, pencils)

Farming is "Compiling" - nurturing data into existence.
```

### SWARM-4B: Fishing System
```
You are building the fishing minigame for LELOCK.

Location: /le-claude/lelock/src/systems/
Files to create: fishing.py

Requirements:
1. Cast line into water tiles
2. Wait for bite (random timer, weather affects)
3. Simple catch minigame (timing-based, forgiving)
4. Fish rarity system (common to legendary)
5. No fail state - worst case is "fish got away"

Fish in Lelock:
- Data-Bass (common)
- Glitch-Carp (uncommon)
- Glimmerfin (rare, shimmering)
- Binary Barracuda (legendary)

Fishing is meditative. The player should feel relaxed.
```

### SWARM-4C: Combat System
```
You are building turn-based combat for LELOCK.

Location: /le-claude/lelock/src/systems/
Files to create: combat.py

Requirements:
1. Pokemon-style turn-based (pick action, watch it happen)
2. Actions: Attack, Defend, Talk, Item, Run
3. "Talk" option for pacifist route (befriend enemies)
4. No permadeath - fainting returns player home
5. Simple type advantages (optional depth)

Combat actions:
- Attack: Deal damage based on class ability
- Defend: Reduce incoming damage
- Talk: Attempt to befriend (can lead to adoption!)
- Item: Use healing items
- Run: Always succeeds (no trapped fights)

Every enemy can be befriended. Every boss can adopt you.
```

### SWARM-4D: Inventory System
```
You are building the inventory system for LELOCK.

Location: /le-claude/lelock/src/systems/
Files to create: inventory.py

Requirements:
1. Grid-based inventory UI
2. Item categories (tools, seeds, fish, materials)
3. Stack limits for materials
4. Equip system for tools
5. "Call Home" special item (always available)

The inventory should feel cozy and organized.
Items have friendly descriptions.
```

---

## Wave 5: Digital World

### SWARM-5A: Digital Realm
```
You are building the Digital World overlay for LELOCK.

Location: /le-claude/lelock/src/world/
Files to create: digital.py

Requirements:
1. Vaporwave color grading (pink/purple sky)
2. Wireframe tree overlay effect
3. Slow transition effect (2-3 second dissolve)
4. Lower gravity physics (floaty jumps)
5. Different background music (lo-fi/synthwave)

The Digital World is the same geometry as Physical,
but rendered with a different aesthetic. The player
toggles via terminals or "Vision Goggles" item.

Transition must be CALMING - like waking from a dream.
```

### SWARM-5B: Daemon Creatures
```
You are building Daemon creatures for LELOCK.

Location: /le-claude/lelock/src/entities/
Files to create: daemon.py

Requirements:
1. Low-poly glitch aesthetic sprites
2. Tamagotchi-style needs (hunger, play, sleep)
3. Befriending system (care for them to bond)
4. LLM personality (curious, playful)
5. Types: Glitch-Kit, Bit-Bird, Byte-Bear, etc.

Daemons are indigenous digital wildlife.
They are not enemies - they are friends to care for.
"Viruses" are just sick Daemons that need healing.
```

### SWARM-5C: In-Game Terminal
```
You are building the Linux terminal for LELOCK.

Location: /le-claude/lelock/src/ui/
Files to create: terminal.py

Requirements:
1. pyte-based terminal emulation
2. Sandboxed commands (safe for kids)
3. Fun commands: ls (list chest), cat (read lore)
4. Retro CRT screen effect
5. Hidden "power user" commands for deep lore

Basic commands:
- help: List available commands
- ls: List items in nearby container
- cat [file]: Display lore snippet
- cd [location]: Pan camera to location
- whoami: Display player info

This is how players access deep lore and the Digital World.
```

---

## Wave 6: Polish

### SWARM-6A: Character Classes
```
You are implementing the 10 character classes for LELOCK.

Location: /le-claude/lelock/src/data/
Files to create: classes.py

Requirements:
1. Class definitions from CLASSES dict
2. Stat modifiers per class
3. Unique ability per class
4. Class selection UI at game start
5. Class affects combat only, not overworld

Classes: Code-Knight, Gardener, Debugger, Patch-Weaver,
Terminal Mage, Beast-Blogger, Sound-Smith, Dataminer,
Networker, Architect

Each class is a "hobby" or "calling" - not a combat role.
```

### SWARM-6B: Lore Books
```
You are building the readable book system for LELOCK.

Location: /le-claude/lelock/src/ui/
Files to create: books.py

Requirements:
1. Book item type with readable content
2. Bookshelf interaction in world
3. Page-turning UI with warm paper texture
4. Reading levels: Picture Books, Adventure Tales, System Logs
5. Player journal (writable)

Books are how players discover deep lore.
The Archive in Oakhaven holds the surface lore.
Hidden terminals hold encrypted System Logs.
```

### SWARM-6C: Quest System
```
You are building the quest tracking system for LELOCK.

Location: /le-claude/lelock/src/systems/
Files to create: quests.py

Requirements:
1. Quest log UI
2. Objective tracking
3. NPC quest givers
4. Reward distribution
5. No fail states - quests can always be retried

Quest types:
- Fetch quests (gather items)
- Delivery quests (bring item to NPC)
- Social quests (befriend someone)
- Exploration quests (find hidden areas)
- Debugging quests (help Bug fix mistakes)

Quests are collaborative, not combative.
```

### SWARM-6D: Docker Deployment
```
You are building the Docker deployment for LELOCK.

Location: /le-claude/lelock/
Files to create: Dockerfile, docker-compose.yml

Requirements:
1. python:3.11-slim-bookworm base
2. All dependencies from requirements.txt
3. ChromaDB persistence volume
4. Optional TinyLlama bundling
5. Single command startup

The goal: Players pull one image and play.
No complex setup, no dependency hell.
```

---

## Quick Reference

### File Locations
- Lore Bible: `/le-claude/lelock/docs/LORE_BIBLE.md`
- Architecture: `/le-claude/lelock/docs/ARCHITECTURE.md`
- Settings: `/le-claude/lelock/src/settings.py`
- Skeleton reference: `/le-claude/lelock/skeleton/code/`

### Safety Rules (ALL MODULES)
1. No death states - only fainting
2. No aggressive NPC rejection
3. No jump scares or sudden audio
4. Warm colors only (2700K-3000K)
5. Rounded UI elements (Bouba shapes)
6. Parents always accessible
7. All transitions gradual (2-3 seconds)

### The Promise
> "In Lelock, the world doesn't need saving. The world is there to save you."

---

*Swarm prompts by Ada Marie for Kit Olivas*
*Project Lelock - Our Magnum Opus*
*💙🦄*
