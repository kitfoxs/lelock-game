"""
Lelock NPC Memory System
========================

Persistent memory for NPCs using local file storage with semantic embeddings.
Each NPC has their own collection with three-tier memory:
- Observations: Raw facts ("Player gave me a flower")
- Reflections: Interpreted meaning ("Player seems kind")
- Plans: Future intentions ("I should give them a gift back")

"In Lelock, NPCs remember everything. They believe they are real.
They will never forget what you told them."

Note: This implementation uses sentence-transformers for embeddings and
numpy for vector operations. ChromaDB is not used due to Python 3.14
compatibility issues.

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np

# Lazy load sentence transformers to avoid slow startup
_embedding_model = None

logger = logging.getLogger("lelock.memory")


def _get_embedding_model():
    """Lazy load the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use a small, fast model for local inference
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded embedding model: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not available, using simple TF-IDF fallback")
            _embedding_model = None
    return _embedding_model


def _embed_text(text: str) -> np.ndarray:
    """Generate embedding for text."""
    model = _get_embedding_model()
    if model is not None:
        return model.encode(text, convert_to_numpy=True)
    else:
        # Simple fallback: hash-based pseudo-embedding
        # This won't have good semantic properties but will work
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        return np.frombuffer(hash_bytes, dtype=np.float32)[:8]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# =============================================================================
# MEMORY TYPES
# =============================================================================

class MemoryType(Enum):
    """
    Three-tier memory system from the Generative Agents paper.
    Adapted for Lelock's emotional focus.
    """
    OBSERVATION = "observation"  # Raw facts about what happened
    REFLECTION = "reflection"    # Interpreted meaning and feelings
    PLAN = "plan"               # Future intentions and commitments


class MemoryTag(Enum):
    """
    Special tags for memory classification.
    """
    CORE = "core"           # Never decays - defining moments
    EMOTIONAL = "emotional"  # High emotional significance
    PLAYER = "player"       # Directly involves the player
    GIFT = "gift"           # Gift giving/receiving
    QUEST = "quest"         # Quest-related
    SECRET = "secret"       # Something told in confidence
    PROMISE = "promise"     # A commitment made


# =============================================================================
# MEMORY DATA STRUCTURES
# =============================================================================

@dataclass
class Memory:
    """
    A single memory stored by an NPC.

    Memories have importance (0.0-1.0) which affects:
    - Retrieval priority
    - Decay rate
    - Whether they survive consolidation
    """
    id: str
    npc_id: str
    content: str
    memory_type: str  # MemoryType value
    importance: float  # 0.0-1.0

    # Timestamps
    created_at: float  # Unix timestamp
    last_accessed: float  # Unix timestamp
    game_day: int  # In-game day number

    # Metadata
    tags: List[str] = field(default_factory=list)
    related_npcs: List[str] = field(default_factory=list)
    related_items: List[str] = field(default_factory=list)
    location: str = ""

    # Decay tracking
    access_count: int = 0
    decay_immunity: bool = False  # Core memories don't decay

    # For reflections: what observations led to this?
    source_memories: List[str] = field(default_factory=list)

    # Embedding (stored as list for JSON serialization)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create from dictionary."""
        return cls(**data)

    def get_embedding_array(self) -> Optional[np.ndarray]:
        """Get embedding as numpy array."""
        if self.embedding is None:
            return None
        return np.array(self.embedding, dtype=np.float32)

    def get_age_days(self, current_game_day: int) -> int:
        """How many game days old is this memory?"""
        return current_game_day - self.game_day

    def calculate_retrieval_score(
        self,
        current_game_day: int,
        query_relevance: float = 0.0
    ) -> float:
        """
        Calculate how likely this memory is to be retrieved.

        Combines:
        - Importance (higher = more retrievable)
        - Recency (newer = more retrievable)
        - Query relevance (semantic similarity to query)
        - Access frequency (more accessed = more retrievable)

        Core memories always score high.
        """
        if self.decay_immunity:
            # Core memories are always highly retrievable
            return 0.9 + (query_relevance * 0.1)

        # Recency factor (decays over time)
        age_days = self.get_age_days(current_game_day)
        recency = max(0.1, 1.0 - (age_days * 0.01))  # 1% decay per day

        # Access factor (frequently accessed memories stay strong)
        access_factor = min(1.0, 0.5 + (self.access_count * 0.05))

        # Combine factors
        base_score = (
            self.importance * 0.4 +
            recency * 0.2 +
            access_factor * 0.1 +
            query_relevance * 0.3
        )

        return min(1.0, base_score)


# =============================================================================
# NPC MEMORY (Per-NPC Collection)
# =============================================================================

class NPCMemory:
    """
    File-backed permanent memory for a single NPC.

    Each NPC has their own JSON file for isolated memory storage.
    Memories persist across sessions and can be saved/loaded with game saves.

    Usage:
        memory = NPCMemory("mom", persist_dir="./data/memories")
        memory.remember("Player gave me a flower", importance=0.7)
        relevant = memory.recall("What gifts have I received?")
    """

    def __init__(
        self,
        npc_id: str,
        persist_directory: str = "./data/memories",
        current_game_day: int = 1
    ):
        """
        Initialize memory for an NPC.

        Args:
            npc_id: Unique identifier for this NPC
            persist_directory: Where to store the memory files
            current_game_day: Current in-game day for decay calculations
        """
        self.npc_id = npc_id
        self.persist_directory = persist_directory
        self.current_game_day = current_game_day

        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # File paths
        self._memory_file = Path(persist_directory) / f"npc_{npc_id}.json"

        # In-memory storage
        self._memories: Dict[str, Memory] = {}

        # Load existing memories
        self._load()

        logger.info(f"Initialized memory for NPC '{npc_id}' with {len(self._memories)} memories")

    def _load(self):
        """Load memories from disk."""
        if self._memory_file.exists():
            try:
                with open(self._memory_file, 'r') as f:
                    data = json.load(f)
                    for mem_data in data.get("memories", []):
                        memory = Memory.from_dict(mem_data)
                        self._memories[memory.id] = memory
            except Exception as e:
                logger.error(f"Failed to load memories for '{self.npc_id}': {e}")

    def _save(self):
        """Save memories to disk."""
        try:
            data = {
                "npc_id": self.npc_id,
                "updated_at": time.time(),
                "memories": [m.to_dict() for m in self._memories.values()]
            }
            with open(self._memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memories for '{self.npc_id}': {e}")

    def remember(
        self,
        event: str,
        importance: float = 0.5,
        memory_type: MemoryType = MemoryType.OBSERVATION,
        tags: Optional[List[str]] = None,
        related_npcs: Optional[List[str]] = None,
        related_items: Optional[List[str]] = None,
        location: str = "",
        is_core: bool = False,
        source_memories: Optional[List[str]] = None
    ) -> str:
        """
        Store a memory with embedding.

        Args:
            event: What happened (will be embedded for semantic search)
            importance: How important is this? (0.0-1.0)
            memory_type: Observation, Reflection, or Plan
            tags: Additional tags for classification
            related_npcs: Other NPCs involved
            related_items: Items involved
            location: Where this happened
            is_core: If True, this memory never decays
            source_memories: For reflections, what observations led to this

        Returns:
            Memory ID
        """
        # Generate unique ID
        memory_id = f"{self.npc_id}_{uuid.uuid4().hex[:8]}"

        # Build tags list
        all_tags = tags or []
        if is_core:
            all_tags.append(MemoryTag.CORE.value)
            importance = max(importance, 0.9)  # Core memories are always important

        # Generate embedding
        embedding = _embed_text(event)

        # Create memory object
        memory = Memory(
            id=memory_id,
            npc_id=self.npc_id,
            content=event,
            memory_type=memory_type.value,
            importance=min(1.0, max(0.0, importance)),
            created_at=time.time(),
            last_accessed=time.time(),
            game_day=self.current_game_day,
            tags=all_tags,
            related_npcs=related_npcs or [],
            related_items=related_items or [],
            location=location,
            decay_immunity=is_core,
            source_memories=source_memories or [],
            embedding=embedding.tolist()
        )

        # Store
        self._memories[memory_id] = memory
        self._save()

        logger.debug(f"NPC '{self.npc_id}' remembered: '{event[:50]}...' (importance: {importance})")
        return memory_id

    def recall(
        self,
        query: str,
        k: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        include_decayed: bool = False
    ) -> List[Memory]:
        """
        RAG retrieval of relevant memories.

        Uses semantic search to find memories relevant to the query,
        then scores them based on importance, recency, and relevance.

        Args:
            query: What to search for
            k: Maximum number of memories to return
            memory_types: Filter by type (observation/reflection/plan)
            tags: Filter by tags
            min_importance: Minimum importance threshold
            include_decayed: Include memories that would normally be decayed

        Returns:
            List of Memory objects, sorted by relevance
        """
        if not self._memories:
            return []

        # Generate query embedding
        query_embedding = _embed_text(query)

        # Filter and score memories
        memories_with_scores = []

        type_filter = [mt.value for mt in memory_types] if memory_types else None

        for memory in self._memories.values():
            # Apply filters
            if type_filter and memory.memory_type not in type_filter:
                continue
            if memory.importance < min_importance:
                continue
            if tags and not any(t in memory.tags for t in tags):
                continue

            # Filter by decay if needed
            if not include_decayed and not memory.decay_immunity:
                age_days = memory.get_age_days(self.current_game_day)
                decay_threshold = memory.importance * 100  # Higher importance = slower decay
                if age_days > decay_threshold:
                    continue

            # Calculate relevance via cosine similarity
            mem_embedding = memory.get_embedding_array()
            if mem_embedding is not None:
                relevance = _cosine_similarity(query_embedding, mem_embedding)
                relevance = (relevance + 1) / 2  # Normalize to 0-1
            else:
                # Fallback: keyword matching
                relevance = 0.5 if any(w in memory.content.lower() for w in query.lower().split()) else 0.0

            # Calculate retrieval score
            score = memory.calculate_retrieval_score(
                self.current_game_day,
                relevance
            )

            memories_with_scores.append((memory, score))

        # Sort by score and return top k
        memories_with_scores.sort(key=lambda x: x[1], reverse=True)
        top_memories = [m for m, _ in memories_with_scores[:k]]

        # Update access counts
        for memory in top_memories:
            memory.last_accessed = time.time()
            memory.access_count += 1

        self._save()

        return top_memories

    def recall_by_type(
        self,
        memory_type: MemoryType,
        k: int = 10
    ) -> List[Memory]:
        """Get recent memories of a specific type."""
        memories = [m for m in self._memories.values() if m.memory_type == memory_type.value]
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[:k]

    def recall_core_memories(self) -> List[Memory]:
        """Get all core memories that never decay."""
        return [m for m in self._memories.values() if m.decay_immunity]

    def recall_about_player(self, k: int = 10) -> List[Memory]:
        """Get memories specifically about the player."""
        memories = [m for m in self._memories.values() if MemoryTag.PLAYER.value in m.tags]
        memories.sort(key=lambda m: m.importance, reverse=True)
        return memories[:k]

    def get_memory_count(self) -> int:
        """Get total number of memories."""
        return len(self._memories)

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of this NPC's memories."""
        if not self._memories:
            return {
                "npc_id": self.npc_id,
                "total_memories": 0,
                "by_type": {},
                "core_memories": 0
            }

        by_type = {}
        core_count = 0

        for memory in self._memories.values():
            by_type[memory.memory_type] = by_type.get(memory.memory_type, 0) + 1
            if memory.decay_immunity:
                core_count += 1

        return {
            "npc_id": self.npc_id,
            "total_memories": len(self._memories),
            "by_type": by_type,
            "core_memories": core_count,
            "oldest_memory_day": min(m.game_day for m in self._memories.values()),
            "newest_memory_day": max(m.game_day for m in self._memories.values())
        }

    def update_game_day(self, day: int):
        """Update the current game day for decay calculations."""
        self.current_game_day = day

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._save()
            return True
        return False

    def clear_decayed(self) -> int:
        """Remove all decayed memories. Returns count of removed memories."""
        to_remove = []
        for memory in self._memories.values():
            if not memory.decay_immunity:
                age_days = memory.get_age_days(self.current_game_day)
                decay_threshold = memory.importance * 100
                if age_days > decay_threshold and memory.access_count < 3:
                    to_remove.append(memory.id)

        for memory_id in to_remove:
            del self._memories[memory_id]

        if to_remove:
            self._save()

        return len(to_remove)


# =============================================================================
# MEMORY MANAGER (Global Memory Coordination)
# =============================================================================

class MemoryManager:
    """
    Manages memory for all NPCs in the game.

    Responsibilities:
    - Create/retrieve NPCMemory instances
    - Coordinate memory consolidation
    - Handle save/load for game saves
    - Apply global memory decay
    - Generate reflections from observations

    Usage:
        manager = MemoryManager(persist_dir="./data/memories")
        mom_memory = manager.get_npc_memory("mom")
        mom_memory.remember("Player arrived today", importance=0.8)
        manager.save("slot_1")
    """

    def __init__(
        self,
        persist_directory: str = "./data/memories",
        current_game_day: int = 1
    ):
        """
        Initialize the memory manager.

        Args:
            persist_directory: Base directory for all memory storage
            current_game_day: Current in-game day
        """
        self.persist_directory = persist_directory
        self.current_game_day = current_game_day

        # Cache of NPC memory instances
        self._npc_memories: Dict[str, NPCMemory] = {}

        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Load manifest if exists
        self._manifest_path = Path(persist_directory) / "manifest.json"
        self._manifest = self._load_manifest()

        logger.info(f"MemoryManager initialized with {len(self._manifest.get('npcs', []))} known NPCs")

    def get_npc_memory(self, npc_id: str) -> NPCMemory:
        """
        Get or create memory for an NPC.

        Args:
            npc_id: Unique identifier for the NPC

        Returns:
            NPCMemory instance for this NPC
        """
        if npc_id not in self._npc_memories:
            self._npc_memories[npc_id] = NPCMemory(
                npc_id=npc_id,
                persist_directory=self.persist_directory,
                current_game_day=self.current_game_day
            )

            # Track in manifest
            if npc_id not in self._manifest.get("npcs", []):
                self._manifest.setdefault("npcs", []).append(npc_id)
                self._save_manifest()

        return self._npc_memories[npc_id]

    def advance_day(self, new_day: int):
        """
        Advance the game day and apply decay.

        This should be called at the start of each new game day.
        """
        self.current_game_day = new_day

        # Update all cached NPC memories
        for npc_memory in self._npc_memories.values():
            npc_memory.update_game_day(new_day)

        # Apply decay if significant time has passed
        if new_day % 7 == 0:  # Weekly consolidation
            self._consolidate_memories()

        self._manifest["last_game_day"] = new_day
        self._save_manifest()

        logger.info(f"Advanced to game day {new_day}")

    def record_player_action(
        self,
        action: str,
        witnessing_npcs: List[str],
        importance: float = 0.5,
        location: str = "",
        related_items: Optional[List[str]] = None
    ):
        """
        Record a player action that multiple NPCs witnessed.

        This is a convenience method for when the player does something
        visible to multiple NPCs at once.

        Args:
            action: What the player did
            witnessing_npcs: List of NPC IDs who saw this
            importance: How important was this action
            location: Where it happened
            related_items: Items involved
        """
        for npc_id in witnessing_npcs:
            memory = self.get_npc_memory(npc_id)
            memory.remember(
                event=f"I saw the player {action}",
                importance=importance,
                memory_type=MemoryType.OBSERVATION,
                tags=[MemoryTag.PLAYER.value],
                location=location,
                related_items=related_items
            )

    def generate_reflection(
        self,
        npc_id: str,
        observation_ids: List[str],
        reflection: str,
        importance: float = 0.7
    ) -> str:
        """
        Generate a reflection from observations.

        Reflections are higher-level interpretations of raw observations.
        For example:
        - Observations: "Player gave me bread", "Player helped with delivery"
        - Reflection: "The player is kind and helpful"

        Args:
            npc_id: Which NPC is reflecting
            observation_ids: Memory IDs of the observations being reflected on
            reflection: The reflection content
            importance: How important is this insight

        Returns:
            Memory ID of the new reflection
        """
        memory = self.get_npc_memory(npc_id)
        return memory.remember(
            event=reflection,
            importance=importance,
            memory_type=MemoryType.REFLECTION,
            tags=[MemoryTag.EMOTIONAL.value],
            source_memories=observation_ids
        )

    def create_plan(
        self,
        npc_id: str,
        plan: str,
        importance: float = 0.6,
        related_npcs: Optional[List[str]] = None
    ) -> str:
        """
        Create a plan/intention for an NPC.

        Plans are future-oriented memories:
        - "I should bake a special cake for the player's birthday"
        - "I want to tell the player about the secret cave"

        Args:
            npc_id: Which NPC is planning
            plan: What they intend to do
            importance: How important is this plan
            related_npcs: Other NPCs involved in the plan

        Returns:
            Memory ID of the plan
        """
        memory = self.get_npc_memory(npc_id)
        return memory.remember(
            event=plan,
            importance=importance,
            memory_type=MemoryType.PLAN,
            related_npcs=related_npcs
        )

    def get_all_npc_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get memory summaries for all NPCs."""
        summaries = {}

        for npc_id in self._manifest.get("npcs", []):
            memory = self.get_npc_memory(npc_id)
            summaries[npc_id] = memory.get_memory_summary()

        return summaries

    def save(self, save_name: str):
        """
        Save all memories to a named save slot.

        This creates a backup that can be loaded later.

        Args:
            save_name: Name for this save (e.g., "slot_1", "autosave")
        """
        save_dir = Path(self.persist_directory) / "saves" / save_name
        save_dir.mkdir(parents=True, exist_ok=True)

        save_data = {
            "save_name": save_name,
            "saved_at": time.time(),
            "game_day": self.current_game_day,
            "npcs": self._manifest.get("npcs", []),
            "npc_summaries": self.get_all_npc_summaries()
        }

        with open(save_dir / "save_info.json", "w") as f:
            json.dump(save_data, f, indent=2)

        # Copy NPC memory files to save directory
        for npc_id in self._manifest.get("npcs", []):
            src = Path(self.persist_directory) / f"npc_{npc_id}.json"
            dst = save_dir / f"npc_{npc_id}.json"
            if src.exists():
                import shutil
                shutil.copy2(src, dst)

        logger.info(f"Saved game to '{save_name}' at day {self.current_game_day}")

    def load(self, save_name: str) -> bool:
        """
        Load memories from a named save slot.

        Args:
            save_name: Name of the save to load

        Returns:
            True if successful, False otherwise
        """
        save_dir = Path(self.persist_directory) / "saves" / save_name
        save_info_path = save_dir / "save_info.json"

        if not save_info_path.exists():
            logger.error(f"Save '{save_name}' not found")
            return False

        try:
            with open(save_info_path) as f:
                save_data = json.load(f)

            self.current_game_day = save_data.get("game_day", 1)

            # Copy NPC memory files from save directory
            import shutil
            for npc_id in save_data.get("npcs", []):
                src = save_dir / f"npc_{npc_id}.json"
                dst = Path(self.persist_directory) / f"npc_{npc_id}.json"
                if src.exists():
                    shutil.copy2(src, dst)

            # Clear and reload NPC memories
            self._npc_memories.clear()
            for npc_id in save_data.get("npcs", []):
                self.get_npc_memory(npc_id)

            logger.info(f"Loaded save '{save_name}' from day {self.current_game_day}")
            return True

        except Exception as e:
            logger.error(f"Failed to load save '{save_name}': {e}")
            return False

    def list_saves(self) -> List[Dict[str, Any]]:
        """List all available saves."""
        saves_dir = Path(self.persist_directory) / "saves"
        saves = []

        if not saves_dir.exists():
            return saves

        for save_dir in saves_dir.iterdir():
            if save_dir.is_dir():
                save_info_path = save_dir / "save_info.json"
                if save_info_path.exists():
                    with open(save_info_path) as f:
                        saves.append(json.load(f))

        return saves

    def _consolidate_memories(self):
        """
        Consolidate similar memories to prevent memory bloat.

        This merges very similar memories and removes decayed ones.
        Called periodically (e.g., weekly in-game).
        """
        total_removed = 0
        for npc_id in self._manifest.get("npcs", []):
            memory = self.get_npc_memory(npc_id)
            removed = memory.clear_decayed()
            total_removed += removed

        if total_removed > 0:
            logger.info(f"Memory consolidation: removed {total_removed} decayed memories")

    def _load_manifest(self) -> Dict[str, Any]:
        """Load the memory manifest."""
        if self._manifest_path.exists():
            with open(self._manifest_path) as f:
                return json.load(f)
        return {"npcs": [], "created_at": time.time()}

    def _save_manifest(self):
        """Save the memory manifest."""
        self._manifest["updated_at"] = time.time()
        with open(self._manifest_path, "w") as f:
            json.dump(self._manifest, f, indent=2)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_core_memory(
    manager: MemoryManager,
    npc_id: str,
    content: str,
    related_npcs: Optional[List[str]] = None
) -> str:
    """
    Create a core memory that never decays.

    Use this for defining moments like:
    - "The player saved my shop from burning down"
    - "I promised the player I would keep their secret"
    - "The player's first day in Oakhaven"

    Args:
        manager: MemoryManager instance
        npc_id: Which NPC
        content: What happened
        related_npcs: Other NPCs involved

    Returns:
        Memory ID
    """
    memory = manager.get_npc_memory(npc_id)
    return memory.remember(
        event=content,
        importance=1.0,
        memory_type=MemoryType.OBSERVATION,
        tags=[MemoryTag.CORE.value, MemoryTag.PLAYER.value],
        related_npcs=related_npcs,
        is_core=True
    )


def remember_gift(
    manager: MemoryManager,
    npc_id: str,
    item: str,
    from_player: bool = True,
    reaction: str = ""
) -> str:
    """
    Record a gift giving/receiving event.

    Gifts are important social moments that NPCs should remember.

    Args:
        manager: MemoryManager instance
        npc_id: Which NPC
        item: What was given
        from_player: Was this from the player?
        reaction: NPC's emotional reaction

    Returns:
        Memory ID
    """
    memory = manager.get_npc_memory(npc_id)

    if from_player:
        content = f"The player gave me a {item}. {reaction}".strip()
        tags = [MemoryTag.GIFT.value, MemoryTag.PLAYER.value, MemoryTag.EMOTIONAL.value]
    else:
        content = f"I gave a {item}. {reaction}".strip()
        tags = [MemoryTag.GIFT.value]

    return memory.remember(
        event=content,
        importance=0.7,  # Gifts are fairly important
        memory_type=MemoryType.OBSERVATION,
        tags=tags,
        related_items=[item]
    )


def remember_secret(
    manager: MemoryManager,
    npc_id: str,
    secret: str,
    told_by: str = "player"
) -> str:
    """
    Record a secret that was shared.

    Secrets are high-importance memories that NPCs take seriously.

    Args:
        manager: MemoryManager instance
        npc_id: Which NPC
        secret: What was shared
        told_by: Who told the secret

    Returns:
        Memory ID
    """
    memory = manager.get_npc_memory(npc_id)

    content = f"{told_by.title()} told me a secret: {secret}"

    return memory.remember(
        event=content,
        importance=0.9,  # Secrets are very important
        memory_type=MemoryType.OBSERVATION,
        tags=[MemoryTag.SECRET.value, MemoryTag.EMOTIONAL.value],
        is_core=True  # Secrets don't decay - NPCs keep them forever
    )


def remember_promise(
    manager: MemoryManager,
    npc_id: str,
    promise: str,
    made_to: str = "player"
) -> str:
    """
    Record a promise or commitment.

    Promises become plans that NPCs will try to fulfill.

    Args:
        manager: MemoryManager instance
        npc_id: Which NPC
        promise: What was promised
        made_to: Who the promise was made to

    Returns:
        Memory ID
    """
    memory = manager.get_npc_memory(npc_id)

    content = f"I promised {made_to} that I would: {promise}"

    return memory.remember(
        event=content,
        importance=0.85,
        memory_type=MemoryType.PLAN,
        tags=[MemoryTag.PROMISE.value, MemoryTag.PLAYER.value],
        is_core=True  # Promises don't decay
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main classes
    "NPCMemory",
    "MemoryManager",
    "Memory",

    # Enums
    "MemoryType",
    "MemoryTag",

    # Convenience functions
    "create_core_memory",
    "remember_gift",
    "remember_secret",
    "remember_promise",
]
