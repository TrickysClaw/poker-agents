"""Card deck management."""
import random
from .types import Card, Rank, Suit


class Deck:
    def __init__(self, seed: int | None = None):
        self.cards: list[Card] = []
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.cards = [Card(rank=r, suit=s) for s in Suit for r in Rank]
        self.rng.shuffle(self.cards)

    def deal(self, n: int = 1) -> list[Card]:
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt
