from sim import GameSim
from tensorforce.agents import PPOAgent, DQNAgent, VPGAgent, TRPOAgent, DRLAgent, DDPGAgent, NAFAgent, DQFDAgent
from treys import Card, Evaluator, Deck
import argparse
import subprocess
from tqdm import tqdm
import os
import numpy as np

NUMBER_OF_PLAYERS = 3


# Temp Directory Required for Batch Job
tmp = os.environ.get('TMPDIR')
tmp = '.'  # remove for batch job submission

# Design parser to look for agent specification
parser = argparse.ArgumentParser()
parser.add_argument("--agent", help="select an agent type [ppo, vpg, dqn]")

# Parse command line argument
args = parser.parse_args()

# pick agent based on specification
if args.agent == "ppo":  # Proximity Policy Optimization
    agent = PPOAgent(
        states={"type": 'float', "shape": (1, 610)},
        actions={"up": dict(type="float", min_value=0.0, max_value=1.0),
                 "down": dict(type="float", min_value=0.0, max_value=1.0),
                 "left": dict(type="float", min_value=0.0, max_value=1.0),
                 "right": dict(type="float", min_value=0.0, max_value=1.0),
                 },
        network='auto',
        memory=10000,
    )
elif args.agent == "dqn":  # Deep Q-Learning
    agent = DQNAgent(
        states={"type": 'float', "shape": (1, 613)},
        actions={"up": dict(type="float", min_value=0.0, max_value=1.0),
                 "down": dict(type="float", min_value=0.0, max_value=1.0),
                 "left": dict(type="float", min_value=0.0, max_value=1.0),
                 "right": dict(type="float", min_value=0.0, max_value=1.0),
                 },
        network='auto',
        memory=10000,
    )

elif args.agent == "vpg":  # Vanilla Policy Gradient
    agent = VPGAgent(
        states={"type": 'float', "shape": (1, 610)},
        actions={"up": dict(type="float", min_value=0.0, max_value=1.0),
                 "down": dict(type="float", min_value=0.0, max_value=1.0),
                 "left": dict(type="float", min_value=0.0, max_value=1.0),
                 "right": dict(type="float", min_value=0.0, max_value=1.0),
                 },
        network='auto',
        memory=10000,
    )

else:
    print("Available agents: vpg, ppo, dqn")
    exit()

print("agent ready", agent)
agent.initialize()  # Set up base of agent


try:  # Looks to see if a saved model is available and loads it
    lastEpoch = int(os.listdir(tmp + "/saved/sim_rew_mult/" +
                               args.agent)[2].split("-")[0])

    agent.restore(directory=tmp + "/saved/sim_rew_mult/" + args.agent)
    print("restored")
except Exception as e:  # starts fresh if no saved model is available
    print(e)
    lastEpoch = 0


epochs = 100000
level_index = 1


for epoch in tqdm(range(lastEpoch, epochs)):
    # print(epoch)
    simulation = GameSim(level_index)
    # penalize over-estimation
    saved_pos = [None]*NUMBER_OF_PLAYERS
    factor_streak = [1]*NUMBER_OF_PLAYERS
    old_reward = [None]*NUMBER_OF_PLAYERS
    turns = 0
    bad_move_count = 0
    agent.reset()
    while not simulation.gameOver() and turns < 300 and bad_move_count < 900:
        if turns == 300 or bad_move_count == 900 or simulation.gameOver():
            break
        for player in range(NUMBER_OF_PLAYERS):
            if turns == 300 or bad_move_count == 900 or simulation.gameOver():
                break
            # print(player)
            # if player done, continue
            state = simulation.get_state()
            state.append(float(player))
            state = [state]
            moved = False
            # print(len(state))
            # exit()

            # print(simulation.players)
            # print(simulation.item_watch())
            while moved == False:
                if bad_move_count == 900 or turns == 300 or simulation.gameOver():
                    break
                action = agent.act(np.asarray(state))
                #print(action)
                if simulation.move_check(player, action):
                    #print('GOOD MOVE')
                    moved = True
                    #print(player)
                    old_pos, new_pos = simulation.movePlayer(player, action)
                    reward, factor_streak[player] = simulation.simple_reward(
                        old_pos, new_pos, player, saved_pos[player], factor_streak[player], old_reward[player])
                    print(str(old_pos) + " " + str(new_pos) + " " +str(reward))
                    # Update Items
                    simulation.item_update(new_pos)
                    # Update Statuses
                    #for i in range(NUMBER_OF_PLAYERS):
                        #simulation.updatePlayer(i)
                    saved_pos[player] = old_pos
                    old_reward[player] = reward
                    turns += 1
                    #print('valid turn count: ' + str(turns))
                    if not simulation.gameOver():
                        if turns != 300:
                            agent.observe(reward=reward, terminal=False)
                        else:
                            agent.observe(reward=reward, terminal=True)
                            break
                    elif simulation.gameOver():
                        agent.observe(reward=reward, terminal=True)
                        break
                        # if level_index == 20:
                        #     level_index = 1
                        # else:
                        #     level_index += 1
                        print("term")
                else:
                    bad_move_count += 1
                    #print('invalid move count: '+ str(bad_move_count))
                    #print('invalid_move')
                    reward = simulation.invalid_move_reward()
                    if bad_move_count != 900:
                        agent.observe(reward=reward, terminal=False)
                    else:
                        agent.observe(reward=reward, terminal=True)
                        break

    if (epoch % 10) == 0:
        #subprocess.call("rm " + tmp + "/saved/sim_rew_mult/" +
                         #args.agent + "/*", shell=True)
        fName = str(epoch) + "-agent"
        agent.save(directory=tmp + "/saved/sim_rew_mult/" +
                   args.agent, filename=fName)
        print("agent saved")

print("Done")
