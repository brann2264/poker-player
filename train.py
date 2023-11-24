from agent import Player
from environment.poker_table import PokerTable

episodes = 40

player = Player(state_dim=8, action_dim=6, save_dir=None)
env = PokerTable()

for episode in range(episodes):
    state = env.reset()

    while True:
        action = player.act(state)
        next_state, reward, done, trunc, info = env.step(action)
        player.cache(state, next_state, action, reward, done)
        loss = player.learn()
        state = next_state

        if done or info['flag_get']:
            print(f'Episode {episode} | Loss: {loss}')
            break