"""Hand evaluation — determines the best 5-card hand from 7 cards."""
from itertools import combinations
from collections import Counter
from .types import Card, HandRank, HandResult, Rank


def evaluate_hand(cards: list[Card]) -> HandResult:
    """Evaluate the best 5-card hand from a list of 5-7 cards."""
    if len(cards) == 5:
        return _eval5(cards)
    best = None
    for combo in combinations(cards, 5):
        result = _eval5(list(combo))
        if best is None or result > best:
            best = result
    return best  # type: ignore


def _eval5(cards: list[Card]) -> HandResult:
    """Evaluate exactly 5 cards."""
    ranks = sorted([c.rank.value for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)
    is_flush = len(set(suits)) == 1
    
    # Check straight
    is_straight, straight_high = _check_straight(ranks)

    # Straight flush / Royal flush
    if is_flush and is_straight:
        if straight_high == 14:
            return HandResult(HandRank.ROYAL_FLUSH, (14,), cards)
        return HandResult(HandRank.STRAIGHT_FLUSH, (straight_high,), cards)

    # Group by count
    groups = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    # Four of a kind
    if groups[0][1] == 4:
        quad = groups[0][0]
        kicker = groups[1][0]
        return HandResult(HandRank.FOUR_OF_A_KIND, (quad, kicker), cards)

    # Full house
    if groups[0][1] == 3 and groups[1][1] == 2:
        return HandResult(HandRank.FULL_HOUSE, (groups[0][0], groups[1][0]), cards)

    # Flush
    if is_flush:
        return HandResult(HandRank.FLUSH, tuple(ranks), cards)

    # Straight
    if is_straight:
        return HandResult(HandRank.STRAIGHT, (straight_high,), cards)

    # Three of a kind
    if groups[0][1] == 3:
        trips = groups[0][0]
        kickers = sorted([g[0] for g in groups[1:]], reverse=True)
        return HandResult(HandRank.THREE_OF_A_KIND, (trips, *kickers), cards)

    # Two pair
    if groups[0][1] == 2 and groups[1][1] == 2:
        pairs = sorted([groups[0][0], groups[1][0]], reverse=True)
        kicker = groups[2][0]
        return HandResult(HandRank.TWO_PAIR, (pairs[0], pairs[1], kicker), cards)

    # One pair
    if groups[0][1] == 2:
        pair = groups[0][0]
        kickers = sorted([g[0] for g in groups[1:]], reverse=True)
        return HandResult(HandRank.ONE_PAIR, (pair, *kickers), cards)

    # High card
    return HandResult(HandRank.HIGH_CARD, tuple(ranks), cards)


def _check_straight(ranks: list[int]) -> tuple[bool, int]:
    """Check if sorted ranks form a straight. Returns (is_straight, high_card)."""
    unique = sorted(set(ranks), reverse=True)
    if len(unique) < 5:
        return False, 0
    # Normal straight
    if unique[0] - unique[4] == 4:
        return True, unique[0]
    # Ace-low straight (A-2-3-4-5)
    if unique == [14, 5, 4, 3, 2]:
        return True, 5
    return False, 0
