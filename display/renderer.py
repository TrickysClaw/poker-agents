"""Terminal UI renderer using Rich."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from engine.types import GameState, Player, Street, HandResult

console = Console()

SUIT_COLORS = {"♥": "red", "♦": "red", "♣": "white", "♠": "white"}


def card_str(card) -> str:
    color = SUIT_COLORS.get(card.suit.value, "white")
    return f"[{color}]{card}[/{color}]"


def render_state(state: GameState, show_all_cards: bool = True):
    """Render the current game state."""
    console.clear()
    pot_total = state.pot + sum(p.current_bet for p in state.players)

    # Header
    header = f"🃏 [bold]AI POKER ARENA[/bold]  |  Pot: [green]${pot_total}[/green]  |  Street: [bold]{state.street.value.upper()}[/bold]"
    console.print(Panel(header, box=box.DOUBLE))

    # Community Cards — BIG in the middle
    if state.community_cards:
        cards_display = "   ".join(card_str(c) for c in state.community_cards)
        # Show empty slots for unrevealed cards
        remaining = 5 - len(state.community_cards)
        if remaining > 0:
            cards_display += "   " + "   ".join("[dim]🂠[/dim]" for _ in range(remaining))
        console.print(Panel(
            f"\n  {cards_display}\n",
            title="[bold]🂠 COMMUNITY CARDS[/bold]",
            box=box.HEAVY,
            border_style="yellow",
            padding=(1, 4),
        ))
    else:
        console.print(Panel(
            "\n  [dim]🂠   🂠   🂠   🂠   🂠[/dim]\n",
            title="[bold]🂠 COMMUNITY CARDS[/bold]",
            box=box.HEAVY,
            border_style="dim",
            padding=(1, 4),
        ))

    # Players
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Player", min_width=20)
    table.add_column("Chips", min_width=10)
    table.add_column("Cards", min_width=15)
    table.add_column("Status", min_width=15)

    roles = _get_roles(state)
    for i, p in enumerate(state.players):
        name = f"{p.emoji} {p.name}"
        chips = f"[green]${p.chips}[/green]"
        if show_all_cards and p.hole_cards:
            cards = " ".join(card_str(c) for c in p.hole_cards)
        else:
            cards = "[dim]🂠 🂠[/dim]"
        if p.folded:
            cards = "[dim]folded[/dim]"
        status = roles.get(i, "")
        if p.all_in:
            status += " [bold red]ALL IN[/bold red]"
        table.add_row(name, chips, cards, status)

    console.print(table)

    # Action log (last 8)
    if state.action_log:
        log = "\n".join(state.action_log[-8:])
        console.print(Panel(log, title=f"[bold]{state.street.value.upper()}[/bold]", box=box.ROUNDED))

    # Chat feed (last 6)
    if state.chat_history:
        chat_lines = []
        for msg in state.chat_history[-6:]:
            chat_lines.append(f'{msg["emoji"]} {msg["name"]}: "{msg["msg"]}"')
        console.print(Panel("\n".join(chat_lines), title="💬 Chat", box=box.ROUNDED))


def render_new_cards(street_name: str, new_cards: list, all_community: list):
    """Highlight new community cards being revealed."""
    new = " ".join(card_str(c) for c in new_cards)
    board = " ".join(card_str(c) for c in all_community)
    console.print(Panel(
        f"[bold]New cards:[/bold] {new}\n[dim]Board:[/dim] {board}",
        title=f"🂠 [bold]{street_name.upper()} REVEALED[/bold]",
        box=box.DOUBLE,
        border_style="yellow",
    ))


def render_info_round_start(state: GameState):
    """Show info round header."""
    console.print(Panel(
        f"[italic]Agents are sizing each other up before {state.street.value}...[/italic]",
        title=f"🗣️  [bold]INFO ROUND — {state.street.value.upper()}[/bold]",
        box=box.ROUNDED,
        border_style="cyan",
    ))


def render_info_chat(player_emoji: str, player_name: str, msg: str):
    """Show a single info round chat message."""
    console.print(f"  {player_emoji} [bold]{player_name}[/bold]: [italic]\"{msg}\"[/italic]")


def render_showdown(state: GameState, winner: Player, won: int, hands: dict, contenders: list[Player], narrator_notes: list[str]):
    """Render the showdown."""
    console.clear()
    board = " ".join(card_str(c) for c in state.community_cards)

    lines = [f"Board: {board}\n"]
    for p in contenders:
        cards = " ".join(card_str(c) for c in p.hole_cards)
        hand_str = str(hands[p.name]) if p.name in hands else "?"
        marker = " ← [bold green]WINNER[/bold green]" if p.name == winner.name else ""
        lines.append(f"{p.emoji} {p.name}: {cards} → {hand_str}{marker}")

    if narrator_notes:
        lines.append("")
        for note in narrator_notes:
            lines.append(f"[italic yellow]{note}[/italic yellow]")

    lines.append(f"\n🏆 {winner.emoji} {winner.name} wins [bold green]${won}[/bold green]")

    console.print(Panel("\n".join(lines), title="🏆 [bold]SHOWDOWN[/bold]", box=box.DOUBLE))

    # Final chat
    if state.chat_history:
        chat_lines = []
        for msg in state.chat_history[-4:]:
            chat_lines.append(f'{msg["emoji"]} {msg["name"]}: "{msg["msg"]}"')
        console.print(Panel("\n".join(chat_lines), title="💬 Final Words", box=box.ROUNDED))


def render_fold_win(winner: Player, won: int, state: GameState):
    """Render win by fold."""
    console.print(Panel(
        f"🏆 {winner.emoji} {winner.name} wins [bold green]${won}[/bold green] — everyone else folded!",
        title="[bold]WINNER[/bold]",
        box=box.DOUBLE,
    ))


def _get_roles(state: GameState) -> dict[int, str]:
    n = len(state.players)
    roles = {state.dealer_idx: "← Dealer"}
    roles[(state.dealer_idx + 1) % n] = "← SB"
    roles[(state.dealer_idx + 2) % n] = "← BB"
    return roles
