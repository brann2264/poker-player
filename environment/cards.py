from collections import Counter
from enum import IntEnum
from collections import namedtuple
import numpy as np
import operator
import pandas as pd
import random

class card:

    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        self.values = {14:"Ace", 13:"King", 12:"Queen", 11:"Jack", 10:"10", 9:"9", 8:"8", 7:"7", 6:"6", 5:"5", 4:"4", 3:"3", 2:"2"}
    
    def __eq__ (self, other):
        return (self.value == other.value)

    def __ne__ (self, other):
        return (self.value != other.value)

    def __lt__ (self, other):
        return (self.value < other.value)

    def __le__ (self, other):
        return (self.value <= other.value)

    def __gt__ (self, other):
        return (self.value > other.value)

    def __ge__ (self, other):
        return (self.value >= other.value)
    
    def __add__ (self, int):
        return card(self.suit, self.value+1)
    
    def __sub__ (self, int):
        return card(self.suit, self.value-1)
    
    def __repr__(self):
        return f'{self.values[self.value]} of {self.suit}'

class card_array:

    def __init__(self, cards):
        self.cards = np.array(cards)
        self.suits = np.array([card.suit for card in cards])
        self.values = np.array([card.value for card in cards])

class hand_evaluator:

    def __init__(self):
        pass

    def isDouble(self, cards_array):
        doubles = []
        values_counter = Counter(cards_array.values)
        for key in values_counter.keys():
            if values_counter[key] == 2:
                doubles.append(key)
        if len(doubles) != 0:
            return np.sort(doubles)
        return 0

    def isTriple(self, cards_array):
        triples = []
        values_counter = Counter(cards_array.values)
        for key in values_counter.keys():
            if values_counter[key] == 3:
                triples.append(key)
        if len(triples) != 0:
            return np.sort(triples)
        return 0

    def isFour(self, cards_array):
        values_counter = Counter(cards_array.values)
        for key in values_counter.keys():
            if values_counter[key] == 4:
                return key
        return 0

    def isFullHouse(self, cards_array):
        triples = self.isTriple(cards_array)
        doubles = self.isDouble(cards_array)
        if np.all(triples != 0) and np.all(doubles != 0):
            return triples[-1]
        return 0

    def isFlush(self, cards_array):
        suits_counter = Counter(cards_array.suits)
        for key in suits_counter.keys():
            if suits_counter[key] >= 5:
                return key
        return 0

    def isStraight(self, cards_array):
        sorted_cards = np.array(sorted(set(cards_array.values)))
        sorted_cards -= np.arange(len(sorted_cards))
        same_counter = Counter(sorted_cards)
        for key in same_counter.keys():
            if same_counter[key] >= 5:
                return np.arange(same_counter[key]) + key
        return 0

    def isStraightFlush(self, cards_array):
        flush = self.isFlush(cards_array)
        if np.all(flush != 0):
            return self.isStraight(card_array(cards_array.cards[cards_array.suits == flush]))
        return 0

    def isRoyalFlush(self, cards_array):
        straight_flush = self.isStraightFlush(cards_array)
        if np.all(straight_flush != 0):
            if np.all(straight_flush[-5:] == np.arange(5)+10):
                return np.arange(5)+10
        return 0

    def getBestHand(self, cards_array):
        combos = [self.isRoyalFlush(cards_array), self.isStraightFlush(cards_array), self.isFour(cards_array), 
                  self.isFullHouse(cards_array), self.isFlush(cards_array), self.isStraight(cards_array), 
                  self.isTriple(cards_array), self.isDouble(cards_array), cards_array.cards]
        for ranking, combo in enumerate(combos):
            if np.all(combo != 0):
                # if triple
                if ranking == 6:
                    high_singles = np.sort(cards_array.values[cards_array.values != combos[0]])[-2:]
                    return ranking, (combo[0], high_singles)
                # if double
                if ranking == 7:
                    # if two double
                    if len(combo) >= 2:
                        not_double_value1 = cards_array.values != combo[-1]
                        not_double_value2 = cards_array.values != combo[-2]
                        high_single = np.sort(cards_array.values[np.logical_and(not_double_value1, not_double_value2)])[-1]
                        return ranking, (combo[-2:], high_single)

                    high_singles = np.sort(cards_array.values[cards_array.values != combo[-1]])[-3:]
                    return ranking, (combo[-1], high_singles)
                # if singles only
                if ranking == 8:
                    return ranking, np.sort(cards_array.values)[-5:]

                return ranking, combo 