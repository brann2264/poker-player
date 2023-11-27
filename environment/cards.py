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
    """
    All check functions return 0 if false, or the cards that make up that combo if true, in sorted order from high to low.
    """

    def __init__(self):
        pass

    def isDouble(self, cards_array):
        """
        Returns the number value of the doubles sorted in descending order
        """
        doubles = []
        values_counter = Counter(cards_array.values)
        for key in values_counter.keys():
            if values_counter[key] == 2:
                doubles.append(key)
        if len(doubles) != 0:
            return np.sort(doubles)[::-1]
        return 0

    def isTriple(self, cards_array):
        """
        Returns the number values of the triples sorted in descending order
        """
        triples = []
        values_counter = Counter(cards_array.values)
        for key in values_counter.keys():
            if values_counter[key] == 3:
                triples.append(key)
        if len(triples) != 0:
            return np.sort(triples)[::-1]
        return 0

    def isFour(self, cards_array):
        """
        Returns the number value of the four-of-a-kind 
        """
        values_counter = Counter(cards_array.values)
        for key in values_counter.keys():
            if values_counter[key] == 4:
                return key
        return 0

    def isFullHouse(self, cards_array):
        """
        Returns the number value of the triple in the full house
        """
        triples = self.isTriple(cards_array)
        doubles = self.isDouble(cards_array)
        if np.all(triples != 0) and np.all(doubles != 0):
            return triples[-1]
        return 0

    def isFlush(self, cards_array):
        """
        Returns the values of the greatest flush
        """
        suits_counter = Counter(cards_array.suits)
        for key in suits_counter.keys():
            if suits_counter[key] >= 5:
                flush_values = np.sort(cards_array.values[cards_array.suits == key])
                return flush_values[-5:]
        return 0

    def isStraight(self, cards_array):
        """
        Returns the values of the straight in descending order
        """
        sorted_cards = np.array(sorted(set(cards_array.values)))
        sorted_cards -= np.arange(len(sorted_cards))
        same_counter = Counter(sorted_cards)
        for key in same_counter.keys():
            if same_counter[key] >= 5:
                return (np.arange(same_counter[key],0,-1) + key)[:5]
        return 0

    def isStraightFlush(self, cards_array):
        """
        Returns the values of the straight flush in descending order
        """
        flush = self.isFlush(cards_array)
        if np.all(flush != 0):
            return self.isStraight(card_array(cards_array.cards[np.isin(cards_array.values,flush)]))
        return 0

    def isRoyalFlush(self, cards_array):
        """
        Returns the values of the royal flush in descending order
        """
        straight_flush = self.isStraightFlush(cards_array)
        if np.all(straight_flush != 0):
            if np.all(straight_flush[-5:] == np.arange(5)+10):
                return (np.arange(5)+10)[::-1]
        return 0

    def getBestHand(self, cards_array):
        combos = [self.isRoyalFlush(cards_array), self.isStraightFlush(cards_array), self.isFour(cards_array), 
                  self.isFullHouse(cards_array), self.isFlush(cards_array), self.isStraight(cards_array), 
                  self.isTriple(cards_array), self.isDouble(cards_array), cards_array.cards]
        for ranking, combo in enumerate(combos):
            if np.all(combo != 0):
                # if double
                if ranking == 7:
                    # if two double
                    if len(combo) >= 2:
                        not_double_value1 = cards_array.values != combo[-1]
                        not_double_value2 = cards_array.values != combo[-2]
                        high_single = np.sort(cards_array.values[np.logical_and(not_double_value1, not_double_value2)])[-1]
                        return ranking-0.5, (combo[-2:], high_single)

                    high_singles = np.sort(cards_array.values[cards_array.values != combo[-1]])[-3:]
                    return ranking, (combo[-1], high_singles)
                # if singles only, obtain highest five
                if ranking == 8:
                    return ranking, np.sort(cards_array.values)[-5:]
                
                return ranking, combo
    
    def compareSingles(self, singles_list):
        """
        singles_list: array-like of array-like of ints
        Compares the values of singles and returns a np array of indexes
        """
        # Convert to a single int to compare
        singles_as_int = np.array([])
        for singles in singles_list:
            singles_as_int= np.append(singles_as_int, int("".join(str(x-2) for x in singles))) # -2 Prevents a 12, 11 from outvaluing a 13, 9
        high = np.argmax(singles_as_int)
        idx = np.array([])
        # Calculate ties
        for id, val in enumerate(singles_as_int):
            if val == singles_as_int[high]:
                idx = np.append(idx, id)
        return idx

    
    def compareCombo(self, ranking, combos):
        """
        ranking: value of the combo
        combos: list of the arrays returned from the check functions
        Compares the same combos and finds the one that is greater and returns the index(es) of the greatest one(s)
        """
        # One hand given
        # if len(combos) == 1:
        #     return 0
        # Comparing royals, straight flushes, straights, four-of-a-kinds, full houses, triples
        if ranking in [0,1,2,3,5,6]:
            combos = np.array(combos)
            high = np.max(combos[:,0])
            return np.argwhere(combos[:,0]==high)

        # Comparing flushes. Flushes are ranked by their high cards, effectively like comparing singles
        elif ranking == 4:
            return self.compareSingles(combos)
                
        # Comparing two doubles
        elif ranking == 6.5:
            combos_as_ints = []
            for combo in combos:
                combos_as_ints.append(int("".join(str(x-2) for x in combo)))
            high = np.argmax(combos_as_ints)
            idx = np.array([])
            # Caculate single high as tiebreakers
            for id, val in enumerate(combos_as_ints):
                if val == combos_as_ints[high]:
                    if combos[id][1] > combos[high][1]:
                        high = id
                        idx = np.array([id])
                    elif combos[id][1] == combos[high][1]:
                        idx = np.append(idx, id)
            return idx 
        
        # Comparing single double
        elif ranking == 7:
            high = 0
            idx = np.array([])
            for id, combo in enumerate(combos):
                if combo[id] > combos[high]:
                    high = id
                    idx = np.array([id])
                elif combo[id] == combos[high]:
                    idx = np.append(idx, id)
        # Comparing singles
        elif ranking == 8:
            return self.compareSingles(combos)
