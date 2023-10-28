import torch
from torch import nn
from torchvision import transforms as T
from PIL import Image
import numpy as np
from pathlib import Path
from collections import deque, namedtuple
import random, datetime, os, copy

import gymnasium as gym
from gym.spaces import Box
from gym.wrappers import FrameStack

from nes_py.wrappers import JoypadSpace

from tensordict import TensorDict
from torchrl.data import TensorDictReplayBuffer, LazyMemmapStorage

class Player():
    def __init__(self, state_dim, action_dim, save_dir):
        # Action Variables
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.save_dir = save_dir

        self.net = PokerDQN(self.state_dim, self.action_dim).float()
        self.net = self.net.to(device=self.device)

        self.exploration_rate = 1
        self.exploration_rate_decay = 0.99999975
        self.exploration_rate_min = 0.1

        self.curr_step = 0
        self.save_every = 5e5

        # Memory Variables
        self.memory = TensorDictReplayBuffer(storage=LazyMemmapStorage(max_size=100000))
        self.batch_size = 32

        # Learn Variables
        self.gamma = 0.9
        self.optimizer = torch.optim.Adam(self.net.parameters(), lr=1e-4)
        self.loss_fn = nn.SmoothL1Loss()
        self.sync_steps = 3

    def act(self, state):
        #Explore
        if np.random.rand() < self.exploration_rate:
            action_id = np.random.randint(self.action_dim)
        #Exploit
        else:
            state = state[0].__array__() if isinstance(state, tuple) else state.__array__()
            state = torch.tensor(state)
            action_values = self.net(state, model="online")
            action_id = torch.argmax(action_values, axis=1).item()

        self.exploration_rate += self.exploration_rate_decay
        self.exploration_rate = max(self.exploration_rate, self.exploration_rate_min)
        self.curr_step += 1

        return action_id

    def cache(self, state, next_state, action, reward, done):
        # Adds current info to memory
        def first_if_tuple(x):
            return x[0] if isinstance(x, tuple) else x
        state = first_if_tuple(state).__array__()
        next_state = first_if_tuple(next_state).__array__()
        state = torch.tensor(state)
        next_state = torch.tensor(next_state)
        action = torch.tensor([action])
        reward = torch.tensor([reward])
        done = torch.tensor([done])

        self.memory.add(TensorDict({"state": state, "next_state": next_state, "action": action, "reward": reward, "done": done}, batch_size=[]))
    
    def recall(self):
        # Retrieves the last batch of memories from the memory
        memory_batch = self.memory.sample(batch_size=self.batch_size)
        state, next_state, action, reward, done = (memory_batch.get(key) for key in ("state", "next_state", "action", "reward", "done"))

        return state, next_state, action, reward, done
    
    def Q_current(self, state, action):
        return self.net(state, model="current")[np.arange(0, self.batch_size), action]

    def Q_target(self, reward, next_state, done):
        # Current reward + Q of the next state
        with torch.no_grad():
            current_Q_pred = self.net(next_state, model="current")
            best_action = torch.argmax(current_Q_pred, axis=1)
            next_Q = self.net(next_state, model="target")[np.arange(0, self.batch_size), best_action]
        return (reward + (1 - done.float()) * self.gamma * next_Q).float()
    
    def optim_Q_current(self, current_est, target):
        loss = self.loss_fn(current_est, target)
        self.optimizer.zero_grad()
        loss.bacmward()
        self.optimizer.step()
        return loss.item()
    
    def sync_target(self):
        self.net.target.load_state_dict(self.net.current.state_dict())

    def learn(self):
        if self.curr_step % self.sync_steps == 0:
            self.sync_target
    
        state, next_state, action, reward, done = self.recall()
        td_current_est = self.Q_current(state, action)
        td_target = self.Q_target(reward, next_state, done)
        loss = self.optim_Q_current(td_current_est, td_target)
        return loss
    
    def save(self):
        torch.save(self.net.state_dict(), self.save_dir)

class PokerDQN(nn.Module):

    def __init__(self, num_states, num_actions):
        super().__init__()
        self.current = nn.Sequential(nn.Linear(num_states, 64),
                                   nn.ReLU(),
                                   nn.Linear(64, 64),
                                   nn.ReLU(),
                                   nn.Linear(64, num_actions))
        self.target = copy.deepcopy(self.current)
    
    def forward(self, x, model):
        if model == "current":
            return self.current(x)
        if model == "target":
            return self.target

