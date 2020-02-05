import csv
import os
import operator
import random
import math
tmp = os.environ.get('TMPDIR')
tmp = "."

SQUARE_TYPES = {537: "plain", 112: "lava",
                369: "jungle", 124: "water", 289: "finish"}
TYPE_VALS = {"plain": 0, "water": 1, "lava": 2, "jungle": 3, "finish": 4}

DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


class GameSim:

    ### map ###
    # Initially pulled from csv file, contails the
    # terrain type respresented numerically
    # example -> 0 = plain space, 1 = water, 2 = lava, 3 = jungle, 4 = Finish
    # [[0, 1, 1],
    # [0, 1, 0],
    # [0, 1, 0]]
    #

    ### player ###
    # Contains a singles players status
    # Contains -> [x_pos, y_pos, type]
    # Example -> [0, 1, 0, False]
    # types -> 1 : Water
    #          2 : Lava
    #          3 : Jungle

    ### items ###
    # contains a list of items, initialized from csv
    # Contains -> [x_pos, y_pos, Active, Player Who Can Access]
    # Example -> [2, 2, True, 3]

    def __init__(self, level_index):
        ### map ###
        self.map = []
        with open(tmp + '/Maps/Team Cog Map CSVs/Team Cog Map ' + str(level_index) + '.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                self.map.append(list(map(int, row)))
        self.mapSize = {"x": len(self.map[0]), "y": len(self.map)}

        # types of players, matches terrain
        self.types = {"Water": 1, "Lava": 2, "Jungle": 3}

        ### Player ###
        self.player1 = [0, 0, self.types["Water"]]
        self.player2 = [0, self.mapSize['y'] - 1, self.types["Lava"]]
        self.player3 = [self.mapSize['x'] - 1,
                        self.mapSize['y'] - 1, self.types["Jungle"]]
        self.players = [self.player1, self.player2, self.player3]

        ### Items ###
        self.items = []
        with open(tmp + '/Maps/Team Cog Map Objective CSVs/Team_Cog_Map_Objectives_' + str(level_index) + '.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if str(row[0]) == '20':
                    self.items.append([row[0], row[1], False, row[2]])
                self.items.append([row[0], row[1], True, row[2]])

    # Ensure that the state is not changed
    # Returns a single state with all required variables in array
    # Player -> 1, 2, 3
    def get_state(self):
        state = []
        for row in self.map:
            state.extend(list(map(float, row)))
        state.extend(list(map(float, self.player1)))
        state.extend(list(map(float, self.player2)))
        state.extend(list(map(float, self.player3)))
        for row in self.items:
            state.extend(list(map(float, row)))
        return state

    def reward_2(self, old_pos, new_pos, playerID, saved_pos=None):
        multiplier_reward = None
        on_item, personal_item = self.position_check(new_pos, playerID)
        # print(on_item)
        end = self.gameOver()
        # print(personal_item)
        item_reward_multiplier = len(
            [item[2] for item in self.items if item[2] is False])
        # if(saved_pos):
        # if saved_pos == new_pos:
        # return 0
        if item_reward_multiplier > 1:
            multiplier_reward = 0.5 * item_reward_multiplier
        if end:
            return 6
        if on_item:
            if multiplier_reward != None:
                return 1 + multiplier_reward
            else:
                return 1
        else:
            return 0.0

    def reward(self, old_pos, new_pos, playerID, saved_pos=None):
        factor_streak = [0, 0, 0]
        on_item, on_end = self.position_check(new_pos, playerID)
        total_item_reward = 0
        if self.item_check():
            new_distance = math.hypot(
                int(self.mapSize['x'] - 1) - new_pos[0], 0 - new_pos[1])
            old_distance = math.hypot(
                int(self.mapSize['x'] - 1) - old_pos[0], 0 - old_pos[1])
            if new_distance < old_distance:
                return 1000
            else:
                return -1300
        if(saved_pos):
            if saved_pos == new_pos:
                return -8000
        if on_item:
            return 5000
        if on_end:
            return 10000
        generator = (item for item in self.items if item[2] is True)
        for item in generator:
            old_distance = math.hypot(
                int(item[0]) - old_pos[0], int(item[1]) - old_pos[1])
            new_distance = math.hypot(
                int(item[0]) - new_pos[0], int(item[1]) - new_pos[1])
            if new_distance < old_distance:
                if factor_streak[playerID] == 0:
                    factor_streak[playerID] = 2
                else:
                    factor_streak[playerID] * factor_streak[playerID]
                total_item_reward += 80 * factor_streak[playerID]
            if new_distance > old_distance:
                factor_streak[playerID] = 0
                total_item_reward -= -80
        return total_item_reward

    def simple_reward(self, old_pos, new_pos, playerID, old_distance=None):
        on_item, personal_item = self.position_check(new_pos, playerID)
        distance_list = []
        distance_max = 40
        #print('the factor streak in simple reward is: ' + str(factor_streak))
        #print('the old_reward in simple reward is: ' + str(old_reward))
        player = self.players[playerID]
        available_items = [item for item in self.items if item[2]
                           is True and (item[3] == '0' or item[3] == str(player[2]))]
        if available_items == False:
            old_distance = None
            return 60, old_distance
        for item in available_items:
            distance = self.breadth_first_search(
                new_pos, (int(item[0]), int(item[1])), playerID)
            if distance:
                distance_list.append([distance, item])
        sorted_distance = sorted(distance_list, key=lambda x: x[0])
        closest = sorted_distance[0][1]
        closest_distance = sorted_distance[0][0]
        if on_item:
            old_distance = closest_distance
            return 25, old_distance
        if old_distance == None:
            distance_reward = 1 - \
                (float(closest_distance)/float(distance_max)) ** 0.4
            old_distance = closest_distance
            return distance_reward, old_distance
        elif old_distance > closest_distance:
            distance_reward = 1 - \
                (float(closest_distance)/float(distance_max)) ** 0.4
            old_distance = closest_distance
            return distance_reward, old_distance
        elif int(old_distance) == int(closest_distance):
            old_distance = closest_distance
            return -0.8, old_distance
        elif int(old_distance) < int(closest_distance):
            old_distance = closest_distance
            return -0.8, old_distance
        else:
            return 'Failure'
            # distance_max = self.breadth_first_search(
            #     corner, (int(closest[0]), int(closest[1])), playerID)

            # if old_reward != None and factor_streak != None:
            #     if (distance_reward * factor_streak) > (old_reward):
            #         factor_streak += 1
            #     else:
            #         factor_streak = 1
            # if factor_streak != None:
            #     distance_reward = distance_reward * factor_streak
            # return distance_reward, factor_streak
        # elif int(closest[0]) <= 12 and (int(closest[1]) <= 23 and int(closest[1]) >= 12):
        #     corner = 23, 0
        #     distance_max = self.breadth_first_search(
        #         corner, (int(closest[0]), int(closest[1])), playerID)
        #     distance_reward = 1 - \
        #         (float(closest_distance)/float(distance_max)) ** 0.4
        #     if old_reward != None and factor_streak != None:
        #         if (distance_reward * factor_streak) > (old_reward):
        #             factor_streak += 1
        #         else:
        #             factor_streak = 1
        #     if factor_streak != None:
        #         distance_reward = distance_reward * factor_streak
        #     return distance_reward, factor_streak
        # elif (int(closest[0]) <= 23 and int(closest[0]) >= 12) and int(closest[1]) <= 12:
        #     corner = 0, 23
        #     distance_max = self.breadth_first_search(
        #         corner, (int(closest[0]), int(closest[1])), playerID)
        #     distance_reward = 1 - \
        #         (float(closest_distance)/float(distance_max)) ** 0.4
        #     if old_reward != None and factor_streak != None:
        #         if (distance_reward * factor_streak) > (old_reward):
        #             factor_streak += 1
        #         else:
        #             factor_streak = 1
        #     if factor_streak != None:
        #         distance_reward = distance_reward * factor_streak
        #     return distance_reward, factor_streak
        # else:
        #     corner = 0, 0
        #     distance_max = self.breadth_first_search(
        #         corner, (int(closest[0]), int(closest[1])), playerID)
        #     distance_reward = 1 - \
        #         (float(closest_distance)/float(distance_max))**0.4
        #     if old_reward != None and factor_streak != None:
        #         if (distance_reward * factor_streak) > (old_reward):
        #             factor_streak += 1
        #         else:
        #             factor_streak = 1
        #     if factor_streak != None:
        #         distance_reward = distance_reward * factor_streak
        #     return distance_reward, factor_streak
        return 'failure'

    # returns boolean if the game is over, TRUE = game over, FALSE = game still going
    def gameOver(self):
        return not any(item[2] for item in self.items)
        # player_check = True
        # for player in self.players:
        #     player_check = player_check and not player[3]

        # return not any(player[3] for player in self.players)

    def updatePlayer(self, playerID):
        player = self.players[playerID]
        if self.item_check() and player[0] == (self.mapSize['x'] - 1) and player[1] == 0:
            player[3] = False
        return player[3]

    def position_check(self, pos, playerID):
        player = pos
        # on_item = False
        # on_yours = False
        on_item, on_yours = self.item_update(
            (player[0], player[1]), playerID)
        # if on_one:
        #     on_item = True
        # elif on_personal:
        #     on_yours = True
        #on_end = not self.updatePlayer(playerID)
        return on_item, on_yours

    def inBounds(self, destination, player_type):
        valid = True
        valid = destination[0] >= 0
        valid = valid and destination[1] >= 0
        valid = valid and destination[1] <= (self.mapSize['x'] - 1)
        valid = valid and destination[0] <= (self.mapSize['y'] - 1)
        if not valid:
            return False

        square_val = self.map[int(destination[1])][int(destination[0])]
        square_type = TYPE_VALS[SQUARE_TYPES[square_val]]
        valid = valid and player_type == square_type or square_type == TYPE_VALS['plain']
        return valid

    def movePlayer(self, playerID, movement):
        player = self.players[playerID]

        # gets largest value in dictionary, which will correlate with the chosen movement
        max_value = max(movement.items(), key=operator.itemgetter(1))[1]

        # get all directions with that probability
        direction_possibilities = []
        for item in movement.items():
            if item[1] == max_value:
                direction_possibilities.append(item[0])

        direction = random.choice(direction_possibilities)
        step = DIRECTIONS[direction]

        player_pos = (player[0], player[1])
        player_type = player[2]

        destination = tuple(map(operator.add, player_pos, step))
        old_position = player[0], player[1]
        # print(old_position)
        # print('inbounds?')
        # print(self.inBounds(destination, player_type))

        if self.inBounds(destination, player_type):
            player[0] = destination[0]
            player[1] = destination[1]
            self.players[playerID] = player
        destination = (player[0], player[1])

        return old_position, destination

    def item_update(self, pos, playerID=None):
        ret = False
        their_item = False
        for ind, item in enumerate(self.items):
            # print(item)
            if (int(item[0]), int(item[1])) == pos and item[2]:
                self.items[ind][2] = False
                if item[3] == str(playerID):
                    their_item = True
                    print('restricted item')
                print("asdfkfjlksaflkjdsa;lkfdsaf")
                ret = True
        return ret, their_item

    # Returns True if all the items have been collected, False if there are still active items
    def item_check(self):
        return not any(item[2] for item in self.items)

    def move_check(self, playerID, movement):
        player = self.players[playerID]

        # gets largest value in dictionary, which will correlate with the chosen movement
        max_value = max(movement.items(), key=operator.itemgetter(1))[1]

        # get all directions with that probability
        direction_possibilities = []
        for item in movement.items():
            if item[1] == max_value:
                direction_possibilities.append(item[0])

        direction = random.choice(direction_possibilities)
        step = DIRECTIONS[direction]

        player_pos = (player[0], player[1])
        player_type = player[2]
        # print(player_type)

        destination = tuple(map(operator.add, player_pos, step))
        old_position = player[0], player[1]
        if self.inBounds(destination, player_type):
            return True
        else:
            return False

    def invalid_move_reward(self):
        return -0.65

    def item_watch(self):
        ret = ""
        for item in self.items:
            ret += str(item[2]) + '\n'
        return ret

    # finds shortest path between 2 nodes of a graph using BFS
    def breadth_first_search(self, start_pos, item_pos, playerID):
        player = self.players[playerID]
        R, C = self.mapSize['x'], self.mapSize['y']
        m = self.map
        sr, sc = start_pos[1], start_pos[0]
        rq, cq = [], []
        move_count = 0
        nodes_left_in_layer = 1
        nodes_in_next_layer = 0
        reached_end = False
        visited = [x[:] for x in [[0] * 24] * 24]
        dr = [-1, +1, 0, 0]
        dc = [0, 0, +1, -1]
        queue = [(sr, sc)]
        visited[sr][sc] = 1
        while len(queue) > 0 and not reached_end:
            queue_copy = []
            # print(queue)
            while(len(queue)):
                (r, c) = queue.pop(0)
                if (r, c) == (item_pos[1], item_pos[0]):
                    reached_end = True
                    break
                for i in range(4):
                    cc = c + dc[i]
                    rr = r + dr[i]
                    if rr < 0 or cc < 0:
                        continue
                    if rr >= C or cc >= R:
                        continue
                    if visited[rr][cc] == 1:
                        continue
                    square_val = m[int(rr)][int(cc)]
                    square_type = TYPE_VALS[SQUARE_TYPES[square_val]]
                    if square_type != 4:
                        pass
                    if square_type != 0:
                        if player[2] != square_type:
                            continue
                    queue_copy.append((rr, cc))
                    visited[rr][cc] = 1
            queue = queue_copy
            if not reached_end:
                move_count += 1
        if reached_end:
            return move_count
        else:
            return False


sim = GameSim(1)
print(sim.simple_reward((0, 2), (0, 1), 0, 14))
# print(sim.reward_2((0, 0), (8, 8), 0))

