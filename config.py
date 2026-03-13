"""Game configuration."""

GAME_CONFIG = {
    "starting_chips": 1000,
    "small_blind": 10,
    "big_blind": 20,
    "max_hands": 1,
    "display_speed": "normal",
    "show_thoughts": False,
    "show_all_cards": True,
}

LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.8,
    "max_tokens": 300,
}

AGENT_PROFILES = {
    "shark": {"emoji": "🦈", "strategy": "shark.md"},
    "bluffer": {"emoji": "🎭", "strategy": "bluffer.md"},
    "tight": {"emoji": "🔒", "strategy": "tight.md"},
    "maniac": {"emoji": "🔥", "strategy": "maniac.md"},
}
