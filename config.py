"""Game configuration."""
import os
from pathlib import Path

# Load .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), value)

GAME_CONFIG = {
    "starting_chips": 1000,
    "small_blind": 10,
    "big_blind": 20,
    "max_hands": 1,
    "display_speed": "normal",
    "show_thoughts": False,
    "show_all_cards": True,
}

# Auto-detect which LLM provider to use based on env vars
LLM_PROVIDER = "gemini" if os.environ.get("GEMINI_API_KEY") else (
    "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "mock"
)

LLM_CONFIG = {
    "provider": LLM_PROVIDER,
    # Gemini
    "gemini_model": "gemini-2.0-flash",
    "gemini_api_key_env": "GEMINI_API_KEY",
    # Anthropic (fallback)
    "anthropic_model": "claude-sonnet-4-20250514",
    # Shared
    "temperature": 0.8,
    "max_tokens": 300,
}

AGENT_PROFILES = {
    "shark": {"emoji": "🦈", "strategy": "shark.md"},
    "bluffer": {"emoji": "🎭", "strategy": "bluffer.md"},
    "tight": {"emoji": "🔒", "strategy": "tight.md"},
    "maniac": {"emoji": "🔥", "strategy": "maniac.md"},
}
