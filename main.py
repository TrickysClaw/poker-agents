#!/usr/bin/env python3
"""AI Poker Arena — main entry point."""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from engine.types import Player, GameState, Street
from engine.game import Game
from agents.base import MockAgent, LLMAgent, GeminiAgent
from display.renderer import render_state, render_showdown, render_fold_win, render_info_round_start, render_info_chat, render_new_cards, console
from config import GAME_CONFIG, AGENT_PROFILES, LLM_PROVIDER


def parse_args():
    parser = argparse.ArgumentParser(description="🃏 AI Poker Arena — AI agents play Texas Hold'em")
    parser.add_argument("--agents", nargs="+", default=["shark", "bluffer", "tight", "maniac"],
                        choices=list(AGENT_PROFILES.keys()), help="Which agents to play")
    parser.add_argument("--speed", choices=["fast", "normal", "step"], default="normal")
    parser.add_argument("--chips", type=int, default=GAME_CONFIG["starting_chips"])
    parser.add_argument("--blinds", type=str, default=None, help="Blinds as SB/BB, e.g. 25/50")
    parser.add_argument("--show-thoughts", action="store_true", help="Show agent internal reasoning")
    parser.add_argument("--mock", action="store_true", help="Use mock agents (no LLM)")
    return parser.parse_args()


def build_narrator_notes(state: GameState, hands: dict, contenders) -> list[str]:
    """Check chat history for lies and generate narrator commentary."""
    notes = []
    # Simple lie detection: check if agents claimed specific hands
    hand_claims = {
        "aces": "One Pair",
        "pocket aces": "One Pair",
        "flush": "Flush",
        "straight": "Straight",
        "full house": "Full House",
        "trips": "Three Of A Kind",
        "set": "Three Of A Kind",
        "two pair": "Two Pair",
    }

    for msg in state.chat_history:
        name = msg["name"]
        text = msg["msg"].lower()
        if name not in hands:
            continue
        actual_hand = str(hands[name])
        for claim, hand_type in hand_claims.items():
            if claim in text:
                if hand_type not in actual_hand and actual_hand != "Royal Flush":
                    notes.append(f"(Narrator: {name} claimed to have {claim}. {name} actually had {actual_hand}. LIAR! 🤥)")
                    break
    return notes


def main():
    args = parse_args()

    sb = GAME_CONFIG["small_blind"]
    bb = GAME_CONFIG["big_blind"]
    if args.blinds:
        parts = args.blinds.split("/")
        sb, bb = int(parts[0]), int(parts[1])

    # Build players and agents
    players = []
    agents = {}
    
    if args.mock:
        provider = "mock"
    else:
        provider = LLM_PROVIDER

    for name in args.agents:
        profile = AGENT_PROFILES[name]
        p = Player(
            name=name.capitalize(),
            emoji=profile["emoji"],
            chips=args.chips,
            strategy_file=profile["strategy"],
        )
        players.append(p)
        if provider == "gemini":
            agents[p.name] = GeminiAgent(p.name, profile["emoji"], profile["strategy"])
        elif provider == "anthropic":
            agents[p.name] = LLMAgent(p.name, profile["emoji"], profile["strategy"])
        else:
            agents[p.name] = MockAgent()

    if provider == "mock":
        console.print("[yellow]⚠ No API key found — using mock agents[/yellow]")
        console.print("[dim]Set GEMINI_API_KEY or ANTHROPIC_API_KEY for real AI agents[/dim]\n")
    elif provider == "gemini":
        console.print("[green]✨ Using Google Gemini (free tier)[/green]\n")
    elif provider == "anthropic":
        console.print("[green]✨ Using Anthropic Claude[/green]\n")

    # Event handler for rendering
    def on_event(event_type, **kwargs):
        state = kwargs.get("state")
        if event_type in ("deal", "street", "action", "blind"):
            if state:
                render_state(state, show_all_cards=GAME_CONFIG["show_all_cards"])
        elif event_type == "new_cards":
            render_new_cards(kwargs["street"].value, kwargs["new_cards"], state.community_cards)
        elif event_type == "info_round_start":
            if state:
                render_info_round_start(state)
        elif event_type == "chat":
            if kwargs.get("info_round"):
                render_info_chat(kwargs["player"].emoji, kwargs["player"].name, kwargs["msg"])
        elif event_type == "info_round_end":
            pass  # Could add separator here
        elif event_type == "win":
            if kwargs.get("by_fold"):
                render_fold_win(kwargs["winner"], kwargs["won"], state)
        elif event_type == "showdown":
            narrator_notes = build_narrator_notes(
                state, kwargs["hands"], kwargs["contenders"]
            )
            render_showdown(
                state, kwargs["winner"], kwargs["won"],
                kwargs["hands"], kwargs["contenders"], narrator_notes
            )

    game = Game(
        players=players,
        agents=agents,
        small_blind=sb,
        big_blind=bb,
        speed=args.speed,
        on_event=on_event,
        show_thoughts=args.show_thoughts,
    )

    console.print("[bold]🃏 AI Poker Arena[/bold] — Let's play!\n")
    result = game.run()

    console.print("\n[bold green]Game complete![/bold green]")
    if result["winner"]:
        w = result["winner"]
        console.print(f"Winner: {w.emoji} {w.name} — won ${result['won']}")


if __name__ == "__main__":
    main()
