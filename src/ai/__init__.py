"""
Lelock AI Module
================

This module contains the AI systems that bring Lelock's world to life:
- LLM integration for NPC dialogue
- Memory systems for persistent NPC memories
- Persona management for character guardrails
- Dialogue management for conversations

"No scripts - only souls."

Part of L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

from .llm import (
    LLMConnection,
    ConnectionStatus,
    GenerationConfig,
    LLMUnavailableError,
    get_connection,
    quick_generate,
)

from .memory import (
    NPCMemory,
    MemoryManager,
    Memory,
    MemoryType,
    MemoryTag,
    create_core_memory,
    remember_gift,
    remember_secret,
    remember_promise,
)

from .persona import (
    Persona,
    PersonaManager,
    SafetyGuardrails,
    SafetyLevel,
    ResponseType,
    ParentPersonaRules,
    create_npc_from_profile,
    quick_npc_response,
)

__all__ = [
    # LLM classes
    "LLMConnection",
    "ConnectionStatus",
    "GenerationConfig",
    "LLMUnavailableError",
    # LLM convenience functions
    "get_connection",
    "quick_generate",

    # Memory classes
    "NPCMemory",
    "MemoryManager",
    "Memory",
    # Memory enums
    "MemoryType",
    "MemoryTag",
    # Memory convenience functions
    "create_core_memory",
    "remember_gift",
    "remember_secret",
    "remember_promise",

    # Persona classes
    "Persona",
    "PersonaManager",
    "SafetyGuardrails",
    # Persona enums
    "SafetyLevel",
    "ResponseType",
    # Persona rules
    "ParentPersonaRules",
    # Persona convenience functions
    "create_npc_from_profile",
    "quick_npc_response",
]
