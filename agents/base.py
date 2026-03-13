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

    TRASH_TALK = [
        "I'm feeling dangerous right now 😈",
        "Anyone else smell weakness at this table?",
        "My cards? Oh, you don't wanna know.",
        "This pot's already mine, just saving you the embarrassment.",
        "I've been waiting for this hand all game.",
        "You really gonna call that? Bold move.",
        "I could win this with my eyes closed.",
        "The way I see it, you're all drawing dead.",
        "Just fold already, save yourself the pain.",
        "Something tells me this is my round.",
        "I wouldn't bet against me if I were you.",
        "Oh this is too easy...",
        "Let's make this interesting 👀",
        "I've got a read on all of you.",
        "Buckle up, this is about to get ugly.",
    ]

    def chat(self, player: Player, state: GameState, round_chat: list[dict]) -> str:
        """Pre-round trash talk."""
        if random.random() > 0.25:
            return random.choice(self.TRASH_TALK)
        return ""

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

    def chat(self, player: Player, state: GameState, round_chat: list[dict]) -> str:
        """Info gathering round — chat before betting."""
        board = " ".join(str(c) for c in state.community_cards) if state.community_cards else "None"
        hole = " ".join(str(c) for c in player.hole_cards)

        others_chat = ""
        for msg in round_chat:
            others_chat += f"  {msg['emoji']} {msg['name']}: \"{msg['msg']}\"\n"

        opponents = []
        for p in state.players:
            if p.name != player.name:
                status = "folded" if p.folded else ("ALL IN" if p.all_in else f"${p.chips}")
                opponents.append(f"  - {p.emoji} {p.name}: {status}")

        prompt = f"""INFO GATHERING ROUND — Talk before betting begins.
This is your chance to strategise, trash talk, bluff, or try to read opponents.

- Street: {state.street.value}
- Your cards: {hole}
- Board: {board}
- Your chips: ${player.chips}

OPPONENTS:
{chr(10).join(opponents)}

WHAT OTHERS SAID THIS ROUND:
{others_chat if others_chat else '  (you speak first)'}

Say something to the table. Stay in character. You can:
- Bluff about your hand
- Try to intimidate
- Be friendly to extract info
- Comment on what others said
- Stay quiet if that's your style

Respond with ONLY your message (plain text, max 150 chars). No JSON."""

        system = f"You are {self.name} ({self.emoji}), a poker player.\n\n{self.strategy}\n\nStay in character. Be entertaining."

        try:
            response = self.client.messages.create(
                model=LLM_CONFIG["model"],
                max_tokens=100,
                temperature=LLM_CONFIG["temperature"],
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip().strip('"')[:150]
        except Exception:
            return ""

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
