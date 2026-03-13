"""Pot management."""
from .types import Player


class PotManager:
    def __init__(self):
        self.total = 0

    def add(self, amount: int):
        self.total += amount

    def collect_bets(self, players: list[Player]):
        """Move all current bets into the pot."""
        for p in players:
            self.total += p.current_bet
            p.current_bet = 0

    def award(self, winner: Player):
        """Award the pot to the winner."""
        winner.chips += self.total
        won = self.total
        self.total = 0
        return won
