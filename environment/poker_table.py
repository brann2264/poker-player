import gym
from gym.spaces import Discrete
from deck import deck
import numpy as np
import random

class PokerTable(gym.Env):

    def __init__(self, render_mode=None, players=4, budget=100, big_blind=2, small_blind=1):
        
        # Table Invariants
        self.num_players = players
        self.players = np.array([])
        self.budget = budget
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.render_mode = render_mode

        # One-hot encoding positions
        self.start_pos = random.randint(0, self.num_players)
        self.dealer_position = None
        self.small_position = None
        self.big_position = None

        # Game Variants
        self.deck = None
        self.total_pot = 0
        self.round_pot = 0
        self.individual_pots = 0
        self.call_amt = 0
        self.last_raise = 0
        self.table_cards = None

        # {0: Preflop, 1: Flop, 2: Turn, 3: River, 4: Showdown}
        self.stage = None

        # Rewards
        self.done = False
        self.illegal_moves_reward = -1
        self.round_start_funds = None
        self.round_end_funds = None
        self.fund_history = None 
        self.reward = None

        self.legal_moves = None
        # {0: Fold, 1: Check, 2: Call, 3: Raise, 4: All in}
        self.action_space = Discrete(5)
        self.observation = None

    def reset(self):
        self.obersvation = None
        self.reward = None 
        self.done = False
        self.fund_history = None

        for player in self.players:
            player.money = self.budget
    
    def step(self, action):
        
        
    def start_round(self):

        self.table_cards = np.array([])
        self.deck = deck(randomize=True)
        self.stage = 0 #Preflop
        self.round_pot = 0
        self.total_pot = 0
        self.individual_pots = np.zeros(len(self.num_players))
        
        self.rand_pos = self.rand_pos+1 if self.rand_pos+1 < self.num_players else 0
        self.dealer_position = np.eye(1, self.num_players, self.rand_pos)
        self.small_position = np.eye(1, self.num_players, self.rand_pos+1 if self.rand_pos+1 < self.num_players else 0)
        self.big_position = np.eye(1, self.num_players, self.rand_pos+2 if self.rand_pos+2 < self.num_players else self.rand_pos+2-self.num_players)

        for player in self.players:
            player.hand = np.array([])
    
    def next_stage(self):

        if self.stage == 0:
            for player in self.players:
                player.hand = np.append(player.hand, [self.deck.draw(), self.deck.draw()])
        
        if self.stage == 1:
            self.deck = np.append(self.cards, [self.deck.draw(), self.deck.draw(), self.deck.draw()])
        
        if self.stage == 2:
            self.deck = np.append(self.cards, self.deck.draw())
        
        if self.stage == 3:
            self.deck = np.append(self.cards, self.deck.draw())
        
        if self.stage == 4:


        