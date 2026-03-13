"""Agent base — LLM-powered and mock agents."""
from __future__ import annotations
import json
import os
import random
from pathlib import Path

from engine.types import (
    Player, GameState, AgentDecision, ActionType, Street,
)
from config import LLM_CONFIG


STRATEGY_DIR = Path(__file__).parent / "strategies"


class MockAgent:
    """Random agent for testing without LLM."""

    def decide(self, player: Player, state: GameState) -> AgentDecision:
        to_call = state.current_bet - player.current_bet
        quips = [
            "Let's go!", "Hmm...", "I've got a feeling...",
            "You're bluffing.", "Easy money.", "🤔", "All day.",
        ]

        if to_call == 0:
            action = random.choice([ActionType.CHECK, ActionType.RAISE])
        else:
            action = random.choice([ActionType.CALL, ActionType.RAISE, ActionType.FOLD])

        raise_amount = 0
        if action == ActionType.RAISE:
            min_raise_to = state.current_bet + state.min_raise
            max_raise = player.chips + player.current_bet
            if min_raise_to > max_raise:
                action = ActionType.CALL if to_call > 0 else ActionType.CHECK
            else:
                raise_amount = random.randint(min_raise_to, min(min_raise_to * 3, max_raise))

        return AgentDecision(
            thought="Mock agent thinking...",
            chat=random.choice(quips) if random.random() > 0.3 else "",
            action=action,
            raise_amount=raise_amount,
        )


class LLMAgent:
    """LLM-powered agent using Anthropic API."""

    def __init__(self, name: str, emoji: str, strategy_file: str):
        self.name = name
        self.emoji = emoji
        strategy_path = STRATEGY_DIR / strategy_file
        self.strategy = strategy_path.read_text() if strategy_path.exists() else "Play solid poker."
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def _build_prompt(self, player: Player, state: GameState) -> str:
        to_call = state.current_bet - player.current_bet
        board = " ".join(str(c) for c in state.community_cards) if state.community_cards else "None"
        hole = " ".join(str(c) for c in player.hole_cards)

        opponents = []
        for p in state.players:
            if p.name != player.name:
                status = "folded" if p.folded else ("ALL IN" if p.all_in else f"${p.chips}")
                opponents.append(f"  - {p.emoji} {p.name}: {status}")

        recent_chat = ""
        for msg in state.chat_history[-15:]:
            recent_chat += f"  {msg['emoji']} {msg['name']}: \"{msg['msg']}\"\n"

        recent_actions = "\n".join(f"  {a}" for a in state.action_log[-10:])

        return f"""GAME STATE:
- Street: {state.street.value}
- Your cards: {hole}
- Board: {board}
- Pot: ${state.pot + sum(p.current_bet for p in state.players)}
- Your chips: ${player.chips}
- Current bet to call: ${to_call}

OPPONENTS:
{chr(10).join(opponents)}

RECENT ACTIONS:
{recent_actions}

RECENT CHAT:
{recent_chat if recent_chat else '  (no chat yet)'}

Legal actions: fold, check{'' if to_call > 0 else ' (no bet to match)'}, call{f' (${to_call})' if to_call > 0 else ' (nothing to call)'}, raise <amount>, all_in
{'You cannot check — there is a bet of $' + str(to_call) + ' to call.' if to_call > 0 else ''}

Respond with JSON: {{"thought": "...", "chat": "...", "action": "fold|check|call|raise|all_in", "raise_amount": <number or null>}}"""

    def decide(self, player: Player, state: GameState) -> AgentDecision:
        system = f"You are {self.name} ({self.emoji}), a poker player.\n\n{self.strategy}\n\nRespond ONLY with valid JSON. Keep chat under 100 chars. Be in character."
        user = self._build_prompt(player, state)

        try:
            response = self.client.messages.create(
                model=LLM_CONFIG["model"],
                max_tokens=LLM_CONFIG["max_tokens"],
                temperature=LLM_CONFIG["temperature"],
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = response.content[0].text.strip()
            # Extract JSON from response
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            action = ActionType(data.get("action", "fold"))
            return AgentDecision(
                thought=data.get("thought", ""),
                chat=data.get("chat", ""),
                action=action,
                raise_amount=data.get("raise_amount") or 0,
            )
        except Exception as e:
            # Retry once
            try:
                response = self.client.messages.create(
                    model=LLM_CONFIG["model"],
                    max_tokens=LLM_CONFIG["max_tokens"],
                    temperature=0.5,
                    system=system + "\n\nYour previous response was invalid. Respond with ONLY valid JSON, nothing else.",
                    messages=[{"role": "user", "content": user}],
                )
                text = response.content[0].text.strip()
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                data = json.loads(text)
                action = ActionType(data.get("action", "fold"))
                return AgentDecision(
                    thought=data.get("thought", ""),
                    chat=data.get("chat", ""),
                    action=action,
                    raise_amount=data.get("raise_amount") or 0,
                )
            except Exception:
                return AgentDecision(
                    thought=f"Error: {e}",
                    chat="",
                    action=ActionType.FOLD,
                    raise_amount=0,
                )
