
from new_state_sim import GameSim
from tensorforce.agents import PPOAgent, DQNAgent, VPGAgent, TRPOAgent, DRLAgent, DDPGAgent, NAFAgent, DQFDAgent
#from treys import Card, Evaluator, Deck
import argparse
import subprocess
from tqdm import tqdm
import os
import numpy as np
import random
#import pdb

# Temp Directory Required for Batch Job
tmp = os.environ.get('TMPDIR')
#tmp = '.'  # remove for batch job submission

# Design parser to look for agent specification
parser = argparse.ArgumentParser()
parser.add_argument("--agent", help="select an agent type [ppo, vpg, dqn]")

# Parse command line argument
args = parser.parse_args()

# pick agent based on specification
if args.agent == "ppo":  # Proximity Policy Optimization
    agent = PPOAgent(
        states={"type": 'float', "shape": (1, 1733)},
        actions={"up": dict(type="float", min_value=0.0, max_value=1.0),
                 "down": dict(type="float", min_value=0.0, max_value=1.0),
                 "left": dict(type="float", min_value=0.0, max_value=1.0),
                 "right": dict(type="float", min_value=0.0, max_value=1.0),
                 },
        network='auto',
        memory=25000,
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
    lastEpoch = int(os.listdir(tmp + "/saved/player_pun/" +
                               args.agent)[2].split("-")[0])

    agent.restore(directory=tmp + "/saved/player_pun/" + args.agent)
    print("restored")
except Exception as e:  # starts fresh if no saved model is available
    print("DID NOT RESTORE")
    lastEpoch = 0


epochs = 2000000

for epoch in tqdm(range(lastEpoch, epochs + 1)):
    #print(epoch)
    #pdb.set_trace()
    map_num = random.randint(1,20)
    simulation = GameSim(map_num)
    # penalize over-estimation
    #print('THIS IS A RESET OF THE SHIT')
    saved_pos = None
    factor_streak = 1
    old_reward = None
    turns = 0
    bad_move_count = 0
    old_distance = None
    player = 2
    counter = 0
    done = False
    agent.reset()
    while simulation.gameOver() == False and turns < 100 and bad_move_count < 150:
        # print(player)
        counter += 1
        # if player done, continue
        state = simulation.get_state()
        state.append(float(turns))
        state = [state]
        moved = False
        # print(len(state))
        # exit()
        # print(simulation.players)
        # print(simulation.item_watch())
        action = agent.act(np.asarray(state))
        # print(action)
        if simulation.move_check(player, action):
            #print('GOOD MOVE')
            turns += 1
            moved = True
            # print(player)
            old_pos, new_pos = simulation.movePlayer(player, action)
            #print(old_reward)
            reward = simulation.reward_2(
                old_pos, new_pos, player, saved_pos)
            #print('factor streak in player' + str(factor_streak))
            #print(map_num)
            print(str(old_pos) + " " + str(new_pos) + " " + str(reward))
            # Update Items
            simulation.item_update(new_pos)
            # Update Statuses
            # for i in range(NUMBER_OF_PLAYERS):
            # simulation.updatePlayer(i)
            #print(reward)
            #print(old_reward)
            saved_pos = old_pos
            #old_distance = distance
            #print('valid turn count: ' + str(turns))
            if simulation.gameOver() == False:
                if turns != 100:
                    agent.observe(reward=reward, terminal=False)
                else:
                    done = True
                    agent.observe(reward=reward, terminal=2)
            elif simulation.gameOver() == True:
                done = True
                agent.observe(reward=reward, terminal=True)
                # if level_index == 20:
                #     level_index = 1
                # else:
                #     level_index += 1
                print("term")
        else:
            bad_move_count += 1
            #print('invalid move count: '+ str(bad_move_count))
            # print('invalid_move')
            reward = simulation.invalid_move_reward()
            if bad_move_count != 150:
                agent.observe(reward=reward, terminal=False)
            else:
                done = True
                agent.observe(reward=reward, terminal=2)
    f = open(tmp+"/saved/fin", "a+")
    f.write(simulation.item_ret() + str(turns) + "\n")
    f.close()
    if epoch % 10 == 0:
        subprocess.call("cp " + tmp + "/saved/fin ~/Agent_Watch/observations", shell=True)
    if (epoch % 100000) == 0:
        subprocess.call("rm " + tmp + "/saved/player_pun/" +
                         args.agent + "/*", shell=True)
        fName = str(epoch) + "-agent"
        agent.save(directory=tmp + "/saved/player_pun/" +
                   args.agent, filename=fName)
        print("agent saved")

print("Done")
