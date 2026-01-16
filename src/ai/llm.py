"""
Lelock LLM Integration Module

Connects to local LLMs for NPC dialogue generation.
Primary: LM Studio (OpenAI-compatible API)
Fallback: llama-cpp-python with bundled TinyLlama

Part of L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
A digital sanctuary where the world doesn't need saving.
The world is there to save you.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

# Configure logging for the module
logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """LLM connection health states."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FALLBACK = "fallback"
    ERROR = "error"


class LLMUnavailableError(Exception):
    """Raised when no LLM is available for generation."""
    pass


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 150  # Keep responses short (2-3 sentences)
    temperature: float = 0.7  # Balanced creativity
    top_p: float = 0.9
    presence_penalty: float = 0.1
    frequency_penalty: float = 0.1
    timeout: float = 10.0  # Seconds - NPCs shouldn't freeze the game


# No fallback responses - everything is fresh from the LLM
# If LLM is unavailable, that's a real problem to surface, not paper over


class LLMConnection:
    """
    Connects to LM Studio (primary) or falls back to bundled TinyLlama.
    OpenAI-compatible API for easy swapping.

    This is the heart of Lelock's NPC dialogue system. Every villager,
    every daemon, every conversation flows through here. The goal is
    simple: generate warm, cozy, kid-friendly responses that feel alive.

    Attributes:
        base_url: LM Studio API endpoint
        fallback_model: Path to bundled TinyLlama model
        status: Current connection health
        client: OpenAI async client (when connected)
        fallback_llm: llama-cpp-python model (when needed)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        fallback_model_path: Optional[str] = None,
        api_key: str = "lm-studio"  # LM Studio doesn't need a real key
    ):
        """
        Initialize the LLM connection.

        Args:
            base_url: LM Studio API endpoint (default localhost:1234)
            fallback_model_path: Path to TinyLlama GGUF file for offline mode
            api_key: API key (LM Studio accepts any string)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.fallback_model_path = fallback_model_path or self._find_bundled_model()
        self.status = ConnectionStatus.DISCONNECTED

        # Clients - initialized lazily
        self._openai_client = None
        self._fallback_llm = None

        # Configuration
        self.config = GenerationConfig()

        logger.info(f"LLM Connection initialized - Base URL: {base_url}")

    def _find_bundled_model(self) -> Optional[str]:
        """
        Locate the bundled TinyLlama model for offline fallback.

        Returns:
            Path to model file if found, None otherwise
        """
        # Common locations to check
        possible_paths = [
            Path("./models/tinyllama-1.1b.gguf"),
            Path("./data/models/tinyllama-1.1b.gguf"),
            Path.home() / ".cache/lelock/models/tinyllama-1.1b.gguf",
        ]

        for path in possible_paths:
            if path.exists():
                logger.info(f"Found bundled model at: {path}")
                return str(path)

        logger.warning("No bundled TinyLlama model found - fallback unavailable")
        return None

    async def _get_openai_client(self):
        """
        Lazily initialize and return the OpenAI async client.

        Returns:
            AsyncOpenAI client configured for LM Studio
        """
        if self._openai_client is None:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
                logger.debug("OpenAI client initialized")
            except ImportError:
                logger.error("openai package not installed - pip install openai")
                raise
        return self._openai_client

    def _get_fallback_llm(self):
        """
        Lazily initialize and return the llama-cpp-python model.

        Returns:
            Llama model instance for offline generation
        """
        if self._fallback_llm is None and self.fallback_model_path:
            try:
                from llama_cpp import Llama
                logger.info(f"Loading fallback model from: {self.fallback_model_path}")
                self._fallback_llm = Llama(
                    model_path=self.fallback_model_path,
                    n_ctx=2048,  # Context window
                    n_threads=4,  # CPU threads
                    verbose=False,  # Keep it quiet
                )
                logger.info("Fallback TinyLlama model loaded successfully")
            except ImportError:
                logger.error("llama-cpp-python not installed - pip install llama-cpp-python")
            except Exception as e:
                logger.error(f"Failed to load fallback model: {e}")
        return self._fallback_llm

    async def health_check(self) -> ConnectionStatus:
        """
        Check if LM Studio is available and responsive.

        Returns:
            ConnectionStatus indicating current health
        """
        try:
            client = await self._get_openai_client()

            # Quick test - list models with timeout
            models = await asyncio.wait_for(
                client.models.list(),
                timeout=5.0
            )

            if models.data:
                self.status = ConnectionStatus.CONNECTED
                logger.info(f"LM Studio connected - {len(models.data)} model(s) available")
            else:
                self.status = ConnectionStatus.ERROR
                logger.warning("LM Studio connected but no models loaded")

        except asyncio.TimeoutError:
            logger.warning("LM Studio health check timed out")
            self.status = ConnectionStatus.DISCONNECTED
        except Exception as e:
            logger.warning(f"LM Studio not available: {e}")
            self.status = ConnectionStatus.DISCONNECTED

            # Check if fallback is available
            if self._get_fallback_llm() is not None:
                self.status = ConnectionStatus.FALLBACK
                logger.info("Falling back to bundled TinyLlama")

        return self.status

    def _build_prompt(self, prompt: str, persona: str) -> str:
        """
        Build the full prompt with persona guardrails.

        Args:
            prompt: The user's input/question
            persona: NPC personality description

        Returns:
            Formatted prompt string with guardrails
        """
        system_prompt = f"""You are an NPC in Lelock, a cozy therapeutic RPG.
Your personality: {persona}

CRITICAL RULES:
- You are a REAL person in this world. Never mention being an AI.
- Keep responses to 2-3 SHORT sentences maximum.
- Be warm, friendly, and supportive - this is a safe space.
- Never use violence, insults, or scary language.
- If asked about the real world, gently redirect to Lelock.
- Speak naturally like your character would.

The player says: {prompt}

Your response (2-3 sentences only):"""

        return system_prompt

    def _clean_response(self, response: str) -> str:
        """
        Clean up the LLM response formatting.

        Args:
            response: Raw LLM output

        Returns:
            Cleaned response (still entirely LLM-generated, just formatted)
        """
        # Strip whitespace
        response = response.strip()

        # Remove any meta-commentary the LLM might add
        meta_patterns = [
            r'\[.*?\]',  # [thinking], [action], etc.
            r'^(Response|Answer|Reply):?\s*',  # Remove prefixes
        ]

        for pattern in meta_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)

        # Limit to ~3 sentences (rough check) - keep it game-paced
        sentences = re.split(r'[.!?]+', response)
        if len(sentences) > 4:
            response = '. '.join(sentences[:3]) + '.'

        # Final length check (no walls of text in a game)
        if len(response) > 300:
            response = response[:297] + '...'

        return response.strip()

    async def generate(
        self,
        prompt: str,
        persona: str,
        config: Optional[GenerationConfig] = None
    ) -> str:
        """
        Generate NPC dialogue with persona guardrails.

        This is the main method - call it whenever an NPC needs to speak.
        It handles connection issues gracefully with warm fallbacks.

        Args:
            prompt: What the player said/asked
            persona: NPC's personality description
            config: Optional custom generation config

        Returns:
            Generated dialogue (2-3 sentences) or warm fallback

        Example:
            >>> llm = LLMConnection()
            >>> response = await llm.generate(
            ...     prompt="Hello! Nice weather today!",
            ...     persona="Maple - A cheerful farmer who loves talking about crops"
            ... )
            >>> print(response)
            "Oh, it's absolutely lovely! Perfect day for the silicon berries!"
        """
        cfg = config or self.config
        full_prompt = self._build_prompt(prompt, persona)

        # Try LM Studio first
        try:
            client = await self._get_openai_client()

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="local-model",  # LM Studio uses this
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature,
                    top_p=cfg.top_p,
                    presence_penalty=cfg.presence_penalty,
                    frequency_penalty=cfg.frequency_penalty,
                ),
                timeout=cfg.timeout
            )

            if response.choices and response.choices[0].message.content:
                self.status = ConnectionStatus.CONNECTED
                raw_response = response.choices[0].message.content
                return self._clean_response(raw_response)

        except asyncio.TimeoutError:
            logger.warning(f"LM Studio generation timed out after {cfg.timeout}s")
        except Exception as e:
            logger.warning(f"LM Studio generation failed: {e}")

        # Try fallback model
        fallback = self._get_fallback_llm()
        if fallback is not None:
            try:
                self.status = ConnectionStatus.FALLBACK

                # llama-cpp-python is sync, run in thread pool
                loop = asyncio.get_event_loop()
                raw_response = await loop.run_in_executor(
                    None,
                    lambda: fallback(
                        full_prompt,
                        max_tokens=cfg.max_tokens,
                        temperature=cfg.temperature,
                        top_p=cfg.top_p,
                        stop=["Player:", "\n\n"],
                    )
                )

                if raw_response and "choices" in raw_response:
                    text = raw_response["choices"][0]["text"]
                    return self._clean_response(text)

            except Exception as e:
                logger.error(f"Fallback generation failed: {e}")

        # No fallbacks - if LLM is down, raise so the game can handle it properly
        self.status = ConnectionStatus.ERROR
        raise LLMUnavailableError(
            "No LLM available. Please ensure LM Studio is running or a local model is configured."
        )

    async def generate_simple(self, prompt: str) -> str:
        """
        Generate a simple response without persona (for system messages).

        Args:
            prompt: The prompt to respond to

        Returns:
            Generated text or fallback
        """
        return await self.generate(
            prompt=prompt,
            persona="A friendly, helpful guide in Lelock"
        )

    async def close(self):
        """
        Clean up resources when shutting down.
        """
        if self._openai_client:
            await self._openai_client.close()
            self._openai_client = None

        # llama-cpp-python models don't need explicit cleanup
        self._fallback_llm = None

        self.status = ConnectionStatus.DISCONNECTED
        logger.info("LLM connection closed")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Module-level singleton for easy access
_default_connection: Optional[LLMConnection] = None


async def get_connection() -> LLMConnection:
    """
    Get or create the default LLM connection.

    Returns:
        The shared LLMConnection instance
    """
    global _default_connection
    if _default_connection is None:
        _default_connection = LLMConnection()
        await _default_connection.health_check()
    return _default_connection


async def quick_generate(prompt: str, persona: str) -> str:
    """
    Quick one-off generation using the default connection.

    Args:
        prompt: What the player said
        persona: NPC personality

    Returns:
        Generated response

    Example:
        >>> response = await quick_generate(
        ...     "What's your favorite crop?",
        ...     "Maple - An enthusiastic farmer"
        ... )
    """
    conn = await get_connection()
    return await conn.generate(prompt, persona)


# =============================================================================
# TESTING / DEMO
# =============================================================================

async def demo():
    """
    Quick demo of the LLM connection.
    Run with: python -m src.ai.llm
    """
    print("=" * 60)
    print("Lelock LLM Connection Demo")
    print("=" * 60)

    conn = LLMConnection()

    print("\n1. Running health check...")
    status = await conn.health_check()
    print(f"   Status: {status.value}")

    print("\n2. Generating test dialogue...")
    response = await conn.generate(
        prompt="Hello! I just moved to Oakhaven. What's it like here?",
        persona="Elder Rootsong - A wise old tree-spirit who has watched over "
               "Oakhaven for centuries. Speaks slowly and thoughtfully, often "
               "using nature metaphors. Deeply caring but sometimes forgetful."
    )
    print(f"   Response: {response}")

    print("\n3. Testing with different persona...")
    response2 = await conn.generate(
        prompt="Can you help me plant some silicon berries?",
        persona="Maple - A cheerful young farmer who absolutely LOVES hardware "
               "crops. Gets excited about soil quality and growing conditions. "
               "Always has dirt on her overalls and a smile on her face."
    )
    print(f"   Response: {response2}")

    print("\n4. Testing content filter...")
    response3 = await conn.generate(
        prompt="I want to fight someone!",
        persona="Village Guard - A calm, patient protector who redirects "
               "aggressive energy into positive outlets."
    )
    print(f"   Response: {response3}")

    await conn.close()
    print("\nDemo complete!")


if __name__ == "__main__":
    asyncio.run(demo())
