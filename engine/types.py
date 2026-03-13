"""Core types for the poker engine."""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Suit(str, Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(int, Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self) -> str:
        names = {11: "J", 12: "Q", 13: "K", 14: "A"}
        return names.get(self.value, str(self.value))


class HandRank(int, Enum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class Street(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


@dataclass(frozen=True, order=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


@dataclass
class Action:
    type: ActionType
    amount: int = 0  # only for raise

    def __str__(self) -> str:
        if self.type == ActionType.RAISE:
            return f"raises to ${self.amount}"
        return self.type.value + "s"


@dataclass
class HandResult:
    rank: HandRank
    values: tuple  # tiebreaker values, highest first
    cards: list[Card] = field(default_factory=list)  # best 5 cards

    def __gt__(self, other: HandResult) -> bool:
        if self.rank != other.rank:
            return self.rank > other.rank
        return self.values > other.values

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HandResult):
            return NotImplemented
        return self.rank == other.rank and self.values == other.values

    def __ge__(self, other: HandResult) -> bool:
        return self == other or self > other

    def __lt__(self, other: HandResult) -> bool:
        return not self >= other

    def __le__(self, other: HandResult) -> bool:
        return not self > other

    def __str__(self) -> str:
        return str(self.rank)


@dataclass
class Player:
    name: str
    emoji: str
    chips: int
    hole_cards: list[Card] = field(default_factory=list)
    current_bet: int = 0
    total_bet_this_hand: int = 0
    folded: bool = False
    all_in: bool = False
    strategy_file: str = ""

    @property
    def active(self) -> bool:
        return not self.folded and not self.all_in


@dataclass
class GameState:
    players: list[Player]
    community_cards: list[Card] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    street: Street = Street.PREFLOP
    dealer_idx: int = 0
    small_blind: int = 10
    big_blind: int = 20
    chat_history: list[dict] = field(default_factory=list)
    action_log: list[str] = field(default_factory=list)
    min_raise: int = 0


@dataclass
class AgentDecision:
    thought: str
    chat: str
    action: ActionType
    raise_amount: int = 0
