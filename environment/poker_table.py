import gym
from gym.spaces import Discrete
from deck import deck
import numpy as np
import random
from cards import hand_evaluator, card_array

class PokerTable(gym.Env):

    def __init__(self, render_mode=None, budget=100, big_blind=2, small_blind=1):
        
        # Table Invariants
        self.num_players = 0
        self.players = []
        self.budget = budget
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.render_mode = render_mode
        self.hand_eval = hand_evaluator()

        # Role Indexes
        self.dealer_position = None
        self.small_position = None
        self.big_position = None

        # Game Variants
        self.deck = None
        self.total_pot = 0
        self.round_pot = 0
        self.call_amt = 0
        self.last_raise = 0
        self.last_player_raised = None
        self.min_raise = 0
        self.table_cards = None
        self.player_order = None
        self.player_turn = 0

        # {1: Preflop, 2: Flop, 3: Turn, 4: River, 5: Showdown}
        self.stage = None

        # Rewards
        self.done = False
        self.illegal_moves_reward = -1
        self.round_start_funds = None
        self.round_end_funds = None
        self.fund_history = None 
        self.reward = None

        self.legal_moves = None
        # {0: Fold, 1: Check, 2: Call, 3: Min Raise, 4: 1.5x Min Raise, 5: 2x Min Raise, 5: 3x Min Raise, 6: 4x Min Raise, 7: 5x Min Raise, 8: All in}
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
        pass
        
    def start_game(self):

        # Resets game variables
        self.table_cards = np.array([])
        self.deck = deck(randomize=True)
        self.stage = 0 #Preflop
        self.round_pot = 0
        self.total_pot = 0
        self.player_turn = 0
        self.round_pot = 0
        self.min_raise = 0
        self.call_amt = 0
        self.last_raise = 0
        self.last_player_raised = None
        
        # Shifts each position down to the next player
        self.dealer_position = self.dealer_position+1 if self.dealer_position+1 < self.num_players else 0
        self.small_position = self.dealer_position+1 if self.dealer_position+1 < self.num_players else 0
        self.big_position = self.small_position+1 if self.small_position+1 < self.small_position else 0

        # Resets players hands
        for player in self.players:
            player.hand = np.array([])
            player.status = "In"

        self.next_stage()
        self.next_player()
    
    def next_stage(self):
        self.stage += 1 

        # Preflop
        if self.stage == 1:
            self.players[self.small_position].money -= self.small_blind
            self.players[self.big_position].money -= self.big_blind
            self.players[self.small_position].round_bet_already += self.small_blind
            self.players[self.big_position].round_bet_already += self.big_blind
            self.round_pot = self.small_blind + self.big_blind
            self.call_amt = self.big_blind
            self.min_raise = self.big_blind

            # Set up turn order
            if self.big_position+1 >= self.num_players:
                self.player_order = self.players
            else:
                self.player_order = self.players[self.big_position+1:] + self.players[:self.big_position+1] 

            # Deal hands
            for player in self.players:
                player.hand = np.append(player.hand, [self.deck.draw(), self.deck.draw()])
        else:
            self.player_turn = 0
            self.total_pot += self.round_pot
            self.round_pot = 0
            self.min_raise = 0
            self.call_amt = 0
            self.last_raise = 0
            self.last_player_raised = None

            for player in self.player_order:
                player.round_bet_already = 0

            if self.stage == 2:
                self.table_cards = np.append(self.table_cards, [self.deck.draw(), self.deck.draw(), self.deck.draw()])
            
            if self.stage == 3 or self.stage == 4:
                self.table_cards = np.append(self.table_cards, self.deck.draw())
        
        if self.stage == 5:
            self.eval_win()
        

    def next_player(self):

        # if action goes back to the same person who raised
        if self.last_player_raised == self.player_order[self.player_turn]:
            self.next_stage()
        # if everyone checks 
        elif self.round_pot == 0:
            self.next_stage()
        # if it makes it back to first person without anyone raising in preflop
        elif self.stage == 1 and self.player_turn == 0 and self.last_player_raised == None and self.round_pot == self.num_players*self.big_blind:
            self.next_stage()

        if self.player_order[self.player_turn].status == "In":
            action = input()
            self.process_action(action)
        # Moves to the next player if the player is out or all-in
        else: 
            self.player_turn = self.player_turn + 1 if self.player_turn+1 != len(self.player_order) else 0
        
        if self.check_game_over():
            self.eval_win()
        else:
            self.next_player(self)
        

    def process_action(self, action):

        if self.check_legal(action):
            # {0: Fold, 1: Check, 2: Call, 3: Min Raise, 4: 1.5x Min Raise, 5: 2x Min Raise, 6: 3x Min Raise, 7: 4x Min Raise, 8: 5x Min Raise, 9: All in}
            if action == 0: # Fold
                self.player_order[self.player_turn].status = "Out"
            # 1: Check -> do nothing
            elif action == 2: # Call
                self.player_order[self.player_turn].money -= self.call_amt - self.player_order[self.player_turn].round_bet_already
                self.round_pot += self.call_amt - self.player_order[self.player_turn].round_bet_already
                self.player_order[self.player_turn].round_bet_already += self.call_amt - self.player_order[self.player_turn].round_bet_already
            elif action in [3,4,5,6,7,8]: # Raises
                mult_dict = {3:1, 4:1.5, 5:2, 6:3, 7:4, 8:5}
                multiplier = mult_dict[action]

                self.player_order[self.player_turn].money -= self.call_amt + multiplier*self.min_raise - self.player_order[self.player_turn].round_bet_already
                self.round_pot += self.call_amt + multiplier*self.min_raise - self.player_order[self.player_turn].round_bet_already
                self.player_order[self.player_turn].round_bet_already += self.call_amt + multiplier*self.min_raise - self.player_order[self.player_turn].round_bet_already
                self.call_amt = self.call_amt + multiplier*self.min_raise
                self.min_raise *= 2*multiplier  # Minimum raise is twice the last raise amount
                self.last_player_raised = self.player_order[self.player_turn]
            elif action == 9: # All in
                self.round_pot += self.player_order[self.player_turn].money
                self.player_order[self.player_turn].round_bet_already += self.player_order[self.player_turn].money
                if self.player_order[self.player_turn].money > self.min_raise + self.call_amt:
                    self.min_raise = 2*(self.player_order[self.player_turn].money - self.call_amt)
                if self.player_order[self.player_turn].money > self.call_amt:
                    self.call_amt = self.player_order[self.player_turn].money
                self.player_order[self.player_turn].money = 0
                self.last_player_raised = self.player_order[self.player_turn]
                self.player_order[self.player_turn].status = "All In"
                
            self.player_turn = self.player_turn + 1 if self.player_turn+1 != len(self.player_order) else 0
  
        else:
            # Does not increment player_turn by 1 if move is not legal
            pass
            #self.return_obs_illegal()
        
        self.next_player()
    
    def record_history(self):
        pass

    def get_obs(self):
        pass

    def check_game_over(self):
        players_in = 0
        for player in self.player_order:
            players_in += 1 if player.status == "In" else 0
        
        if players_in <= 1:
            return True
        return False

    def eval_win(self):
        # Reveal rest of the cards if not revealed already
        for x in range(len(self.table_cards)-5):
            self.table_cards = np.append(self.table_cards, self.deck.draw())
        # Gets best hand of each player in    
        players_in = []
        for player in self.player_order:
            if player.status != "Out":
                player.high = self.hand_eval.getBestHand(card_array(np.append(self.table_cards, player.hand)))
                players_in.append(player)
        # Sort players in by their combo ranking
        players_in.sort(reverse=True, key=lambda x:x.high[0])
        ties = [players_in[0]]
        # Find all players who have the same winning combo type
        for player in players_in[1:]:
            if player.high[0] != ties[0].high[0]:
                break
            else:
                ties.append(player)
        # Compare combos
        winner = self.hand_eval([player.high[1] for player in ties])

        for player in ties[winner]:
            player.money += self.total_pot/len(winner)

        self.record_history()
        self.start_game()
        

    def check_legal(self, action):
        # {0: Fold, 1: Check, 2: Call, 3: Min Raise, 4: 1.5x Min Raise, 5: 2x Min Raise, 6: 3x Min Raise, 7: 4x Min Raise, 8: 5x Min Raise, 9: All in}

        active_player_money = self.player_order[self.player_turn].money
        # Fold and all-in are always legal moves
        legal_moves = [0, 9]
        # Check if check is legal
        if self.player_order[self.player_turn].round_bet_already == self.call_amt:
            legal_moves.append(1)
        # Check if call is legal
        if active_player_money > self.call_amt - self.player_order[self.player_turn].round_bet_already and self.call_amt - self.player_order[self.player_turn].round_bet_already !=0:
            legal_moves.append(2)
        # Check if raising by X amount is legal
        raise_dict = {1:3, 1.5:4, 2:5, 3:6, 4:7, 5:8}
        for mult in [1, 1.5, 2, 3, 4, 5]:
            if active_player_money >= self.call_amt + mult*self.min_raise:
                legal_moves.append(raise_dict[mult])
        
        return action in legal_moves
    
    def add_player(self, player):
        self.players.append(player)
        self.num_players += 1
        player.money = self.budget
        self.dealer_position = random.randint(0,self.num_players-1)




        