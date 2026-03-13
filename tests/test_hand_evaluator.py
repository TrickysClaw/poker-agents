"""Unit tests for the hand evaluator."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.types import Card, Rank, Suit, HandRank
from engine.hand_evaluator import evaluate_hand


def c(rank_val, suit_str):
    suit_map = {"h": Suit.HEARTS, "d": Suit.DIAMONDS, "c": Suit.CLUBS, "s": Suit.SPADES}
    return Card(Rank(rank_val), suit_map[suit_str])


def test_royal_flush():
    cards = [c(14,"s"), c(13,"s"), c(12,"s"), c(11,"s"), c(10,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.ROYAL_FLUSH, f"Expected Royal Flush, got {r.rank}"


def test_straight_flush():
    cards = [c(9,"h"), c(8,"h"), c(7,"h"), c(6,"h"), c(5,"h")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.STRAIGHT_FLUSH, f"Expected Straight Flush, got {r.rank}"


def test_four_of_a_kind():
    cards = [c(14,"s"), c(14,"h"), c(14,"d"), c(14,"c"), c(13,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.FOUR_OF_A_KIND


def test_full_house():
    cards = [c(13,"s"), c(13,"h"), c(13,"d"), c(10,"c"), c(10,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.FULL_HOUSE


def test_flush():
    cards = [c(14,"d"), c(10,"d"), c(8,"d"), c(5,"d"), c(2,"d")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.FLUSH


def test_straight():
    cards = [c(10,"s"), c(9,"h"), c(8,"d"), c(7,"c"), c(6,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.STRAIGHT


def test_ace_low_straight():
    cards = [c(14,"s"), c(2,"h"), c(3,"d"), c(4,"c"), c(5,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.STRAIGHT
    assert r.values == (5,), f"Ace-low straight high should be 5, got {r.values}"


def test_three_of_a_kind():
    cards = [c(7,"s"), c(7,"h"), c(7,"d"), c(13,"c"), c(2,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.THREE_OF_A_KIND


def test_two_pair():
    cards = [c(14,"s"), c(14,"h"), c(8,"d"), c(8,"c"), c(3,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.TWO_PAIR


def test_one_pair():
    cards = [c(10,"s"), c(10,"h"), c(14,"d"), c(8,"c"), c(3,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.ONE_PAIR


def test_high_card():
    cards = [c(14,"s"), c(10,"h"), c(8,"d"), c(5,"c"), c(3,"s")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.HIGH_CARD


def test_7_card_best_hand():
    # 7 cards: should find the best 5
    cards = [c(14,"s"), c(14,"h"), c(14,"d"), c(13,"c"), c(13,"s"), c(2,"h"), c(3,"d")]
    r = evaluate_hand(cards)
    assert r.rank == HandRank.FULL_HOUSE


def test_hand_comparison():
    flush = evaluate_hand([c(14,"d"), c(10,"d"), c(8,"d"), c(5,"d"), c(2,"d")])
    pair = evaluate_hand([c(10,"s"), c(10,"h"), c(14,"d"), c(8,"c"), c(3,"s")])
    assert flush > pair


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
    print("\nAll tests done!")
