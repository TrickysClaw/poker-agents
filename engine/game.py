"""Game loop — runs a single hand of No-Limit Texas Hold'em."""
from __future__ import annotations
import time
from typing import Protocol, Callable

from .types import (
    Player, GameState, Action, ActionType, Street, AgentDecision, HandRank,
)
from .deck import Deck
from .hand_evaluator import evaluate_hand
from .pot import PotManager


class AgentInterface(Protocol):
    def decide(self, player: Player, state: GameState) -> AgentDecision: ...


class Game:
    def __init__(
        self,
        players: list[Player],
        agents: dict[str, AgentInterface],
        small_blind: int = 10,
        big_blind: int = 20,
        speed: str = "normal",
        on_event: Callable | None = None,
        show_thoughts: bool = False,
    ):
        self.deck = Deck()
        self.pot = PotManager()
        self.agents = agents
        self.show_thoughts = show_thoughts
        self.speed = speed
        self.on_event = on_event or (lambda *a, **kw: None)
        self.state = GameState(
            players=players,
            dealer_idx=0,
            small_blind=small_blind,
            big_blind=big_blind,
        )

    def delay(self):
        if self.speed == "fast":
            time.sleep(0.3)
        elif self.speed == "normal":
            time.sleep(1.5)
        elif self.speed == "step":
            input("  [Press Enter to continue]")

    def run(self) -> dict:
        """Run a single hand. Returns summary dict."""
        s = self.state
        n = len(s.players)

        # Post blinds
        sb_idx = (s.dealer_idx + 1) % n
        bb_idx = (s.dealer_idx + 2) % n
        self._post_blind(s.players[sb_idx], s.small_blind, "Small Blind")
        self._post_blind(s.players[bb_idx], s.big_blind, "Big Blind")
        s.current_bet = s.big_blind
        s.min_raise = s.big_blind

        # Deal hole cards
        self.deck.reset()
        for p in s.players:
            p.hole_cards = self.deck.deal(2)
        self.on_event("deal", state=s)
        self.delay()

        # Betting rounds
        streets = [
            (Street.PREFLOP, 0),
            (Street.FLOP, 3),
            (Street.TURN, 1),
            (Street.RIVER, 1),
        ]

        for street, num_cards in streets:
            s.street = street
            if num_cards > 0:
                cards = self.deck.deal(num_cards)
                s.community_cards.extend(cards)
            self.on_event("street", state=s)
            self.delay()

            if self._count_active() <= 1:
                break

            self._betting_round(street, sb_idx, bb_idx)

            if self._count_active_or_allin() <= 1:
                break

            # Reset bets for next street
            self.pot.collect_bets(s.players)
            s.current_bet = 0
            s.min_raise = s.big_blind
            for p in s.players:
                p.current_bet = 0

        # Collect remaining bets
        self.pot.collect_bets(s.players)
        s.pot = self.pot.total

        # Determine winner
        return self._showdown()

    def _post_blind(self, player: Player, amount: int, label: str):
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet = actual
        player.total_bet_this_hand += actual
        self.state.action_log.append(f"{player.emoji} {player.name} posts {label} ${actual}")
        self.on_event("blind", player=player, amount=actual, label=label)

    def _count_active(self) -> int:
        return sum(1 for p in self.state.players if not p.folded and not p.all_in)

    def _count_active_or_allin(self) -> int:
        return sum(1 for p in self.state.players if not p.folded)

    def _betting_round(self, street: Street, sb_idx: int, bb_idx: int):
        s = self.state
        n = len(s.players)

        if street == Street.PREFLOP:
            start = (bb_idx + 1) % n
        else:
            start = (s.dealer_idx + 1) % n

        last_raiser = -1
        acted = set()
        idx = start

        while True:
            p = s.players[idx]
            if not p.folded and not p.all_in:
                if idx == last_raiser and idx in acted:
                    break

                decision = self._get_decision(p)
                action = self._validate_action(p, decision)
                self._apply_action(p, action)

                if decision.chat:
                    chat_msg = decision.chat[:100]
                    s.chat_history.append({"name": p.name, "emoji": p.emoji, "msg": chat_msg})
                    self.on_event("chat", player=p, msg=chat_msg)

                self.on_event("action", player=p, action=action, state=s)
                self.delay()

                if action.type == ActionType.RAISE or action.type == ActionType.ALL_IN:
                    last_raiser = idx

                acted.add(idx)

                if self._count_active_or_allin() <= 1:
                    break

            idx = (idx + 1) % n

            # If we've gone around and no one raised, we're done
            if idx == start and last_raiser == -1 and start in acted:
                break
            if idx in acted and (last_raiser == -1 or idx == last_raiser):
                break

    def _get_decision(self, player: Player) -> AgentDecision:
        agent = self.agents[player.name]
        return agent.decide(player, self.state)

    def _validate_action(self, player: Player, decision: AgentDecision) -> Action:
        s = self.state
        action_type = decision.action
        amount = decision.raise_amount

        to_call = s.current_bet - player.current_bet

        # Can't check if there's a bet to call
        if action_type == ActionType.CHECK and to_call > 0:
            action_type = ActionType.FOLD

        # Call
        if action_type == ActionType.CALL:
            call_amount = min(to_call, player.chips)
            if call_amount >= player.chips:
                return Action(ActionType.ALL_IN, player.chips)
            return Action(ActionType.CALL, call_amount)

        # Raise
        if action_type == ActionType.RAISE:
            min_raise_to = s.current_bet + s.min_raise
            if amount < min_raise_to:
                amount = min_raise_to
            if amount >= player.chips + player.current_bet:
                return Action(ActionType.ALL_IN, player.chips)
            return Action(ActionType.RAISE, amount)

        # All-in
        if action_type == ActionType.ALL_IN:
            return Action(ActionType.ALL_IN, player.chips)

        # Check
        if action_type == ActionType.CHECK:
            return Action(ActionType.CHECK, 0)

        # Fold
        return Action(ActionType.FOLD, 0)

    def _apply_action(self, player: Player, action: Action):
        s = self.state

        if action.type == ActionType.FOLD:
            player.folded = True
            s.action_log.append(f"{player.emoji} {player.name} folds")

        elif action.type == ActionType.CHECK:
            s.action_log.append(f"{player.emoji} {player.name} checks")

        elif action.type == ActionType.CALL:
            player.chips -= action.amount
            player.current_bet += action.amount
            player.total_bet_this_hand += action.amount
            s.action_log.append(f"{player.emoji} {player.name} calls ${action.amount}")

        elif action.type == ActionType.RAISE:
            raise_cost = action.amount - player.current_bet
            s.min_raise = action.amount - s.current_bet
            player.chips -= raise_cost
            player.total_bet_this_hand += raise_cost
            player.current_bet = action.amount
            s.current_bet = action.amount
            s.action_log.append(f"{player.emoji} {player.name} raises to ${action.amount}")

        elif action.type == ActionType.ALL_IN:
            actual = player.chips
            player.total_bet_this_hand += actual
            player.current_bet += actual
            player.chips = 0
            player.all_in = True
            if player.current_bet > s.current_bet:
                s.min_raise = player.current_bet - s.current_bet
                s.current_bet = player.current_bet
            s.action_log.append(f"{player.emoji} {player.name} goes ALL IN (${actual})")

    def _showdown(self) -> dict:
        s = self.state
        s.street = Street.SHOWDOWN
        contenders = [p for p in s.players if not p.folded]

        if len(contenders) == 1:
            winner = contenders[0]
            won = self.pot.award(winner)
            s.action_log.append(f"🏆 {winner.emoji} {winner.name} wins ${won} (everyone else folded)")
            self.on_event("win", winner=winner, won=won, state=s, by_fold=True)
            return {"winner": winner, "won": won, "by_fold": True, "hands": {}}

        # Evaluate hands
        hands = {}
        best_player = None
        best_result = None
        for p in contenders:
            all_cards = p.hole_cards + s.community_cards
            result = evaluate_hand(all_cards)
            hands[p.name] = result
            if best_result is None or result > best_result:
                best_result = result
                best_player = p

        won = self.pot.award(best_player)  # type: ignore
        s.action_log.append(
            f"🏆 {best_player.emoji} {best_player.name} wins ${won} with {best_result}"  # type: ignore
        )
        self.on_event("showdown", winner=best_player, won=won, state=s, hands=hands, contenders=contenders)
        return {
            "winner": best_player,
            "won": won,
            "by_fold": False,
            "hands": hands,
        }
