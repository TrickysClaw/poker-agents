# AI Poker Arena 🃏

Autonomous AI agents play No-Limit Texas Hold'em against each other with live trash talk, bluffing, and a narrator that catches liars.

## Quick Start

```bash
pip install -r requirements.txt

# Run with mock agents (no API key needed)
python main.py --mock --speed fast

# Run with LLM-powered agents
export ANTHROPIC_API_KEY=your_key_here
python main.py

# Customize
python main.py --agents shark bluffer maniac --speed step --show-thoughts
python main.py --chips 5000 --blinds 25/50
```

## Agents

| Agent | Style | Personality |
|-------|-------|-------------|
| 🦈 Shark | Tight-Aggressive | Cold, calculating, intimidating |
| 🎭 Bluffer | Loose-Aggressive | Loud, chaotic, lies constantly |
| 🔒 Tight | Tight-Passive | Patient, disciplined, risk-averse |
| 🔥 Maniac | Hyper-Aggressive | Unhinged, fearless, pure chaos |

Edit strategy files in `agents/strategies/` to customize agent behavior.

## Spectator Mode

The terminal shows ALL players' hole cards to you, but each AI agent can only see its own cards. Watch the bluffs unfold in real time!

## Tests

```bash
python tests/test_hand_evaluator.py
```
