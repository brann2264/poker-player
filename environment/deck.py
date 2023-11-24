import random
import numpy as np
from cards import card

class deck:
   
    def __init__(self, randomize=True):
        self.suits = {"Diamonds": 0, "Clubs": 1, "Hearts":2, "Spades":3}
        self.values = {14:"Ace", 13:"King", 12:"Queen", 11:"Jack", 10:"10", 9:"9", 8:"8", 7:"7", 6:"6", 5:"5", 4:"4", 3:"3", 2:"2"}
        self.cards = np.array([])

        self.shuffle_deck(randomize)
    
    def shuffle_deck(self, randomize=True):
        self.cards = np.array([])
        for value in self.values.keys():
            for suit in self.suits.keys():
                self.cards = np.append(self.cards, card(suit, value))
        
        if randomize:
            np.random.shuffle(self.cards)

        return self.cards
    
    def __repr__(self):
        return f"{self.cards}"

    def draw(self):
        drawn_card = self.cards[0]
        self.cards = self.cards[1:]
        return drawn_card

class player:

    def __init__(self):
        self.hand = np.array([])
        self.money = 0
        self.status = True
        self.role = 4
        self.action = False
        self.high = None
        # {1: Dealer, 2: Little Blind, 3: Big Blind, 4: Nothing}
    
    def call(self, deck):
        self.money -= deck.call_amt

    def fold(self):
        self.status = False

    def raise_money(self, board, raise_amt):
        board.call_amt = raise_amt
        self.money -= board.call_amt


class board:

    def __init__(self, deck, blind_amt, players, buy_in, call_amt=0):
        self.cards = np.array([])
        self.pot = 0
        self.buy_in = buy_in
        self.call_amt = 0
        self.blind = blind_amt
        self.players = players
        self.deck = deck
    
    def show(self):
        if len(self.cards) == 0:
            num = 3
        else:
            num = 1    
        for card in range(num):
            self.cards = np.append(self.cards, self.deck.draw())
        return self.cards
    
    def deal_hands(self):
        for player in self.players:
            player.hand = np.append(player.hand, [self.deck.draw(), self.deck.draw()])
    
    def reset(self):
        for player in self.players:
            player.hand = []
        self.deck.shuffle_deck()
        self.cards = []
    
    def card_sort(self, cards):
        values_order = np.argsort(cards)[::-1]
        suits_order = np.argsort(np.array([card.suit for card in cards[values_order]]))
        
        return cards, values_order, suits_order
    
    def player_board(self, player):
        return np.append(self.cards, player.hand)

    def isStraight(self, cards):
        cards, values_order, _ = self.card_sort(cards)
        
        same = 0
        for num in range(len(cards)-1):
            if cards[values_order][num] == cards[values_order][num+1]+1:
                same += 1
                if same >= 4:
                    return cards[values_order][num-3:num+2]
            else:
                same = 0
    
    def isFlush(self, cards):
        cards, _, suits_order = self.card_sort(cards)
        
        same = 0
        for num in range(len(cards)-1):
            if cards[suits_order][num].suit == cards[suits_order][num+1].suit:
                same += 1
                if same >= 4:
                    return cards[suits_order][num-3:num+2]
            else:
                same = 0

    def isStraightFlush(self, cards):
        return self.isFlush(self.isStraight(cards))
    
    def isRoyalFlush(self, cards):
        if self.isStraightFlush(cards)[0].value == 14:
            return self.isStraightFlush(cards)

    def isFour(self, player):
        card_values, _ = self.player_board(player)
        high_single = 0
        same_count = 0

        for n in range(len(card_values)-1):
            if card_values[n] == card_values[n+1]:
                same_count += 1
                if same_count == 3:
                    #if four of a kind is the greatest four in array, the fifth in array is the high single
                    if high_single == 0:
                        high_single = card_values[n+2]
                    return True, (card_values[n], high_single)
            elif card_values[n] > high_single:
                high_single = card_values[n]
                same_count = 0
            else:
                same_count = 0
        return False, None
    
    def isTriple(self, player):
        card_values, _ = self.player_board(player)
        same_count = 0
        
        for n in range(len(card_values)-1):
            if card_values[n] == card_values[n+1]:
                same_count += 1
                if same_count == 2:
                    return True, card_values[n]
            else:
                same_count = 0
        return False, None
    
    def isDouble(self, player):
        card_values, _ = self.player_board(player)
        doubles = []
        
        for n in range(len(card_values)-1):
            if card_values[n] == card_values[n+1]:
                if same_count == 2:
                    return True, card_values[n]
            else:
                same_count = 0
        return False, None
