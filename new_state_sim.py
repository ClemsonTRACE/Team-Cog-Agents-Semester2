import csv
import os
import operator
import random
import math
tmp = os.environ.get('TMPDIR')
#tmp = "."

SQUARE_TYPES = {537: "plain", 112: "lava",
                369: "jungle", 124: "water"}
TYPE_VALS = {"plain": 0, "water": 1, "lava": 2, "jungle": 3}

DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
DIRECTIONS2 = {"up": 1, "down": 2, "left": 3, "right": 4}

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
        with open('./Maps_Single_Player/Team Cog Map CSVs/Team Cog Map ' + str(level_index) + '.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                self.map.append(list(map(int, row)))

        y = 0
        available_coordinates = []
        for i in self.map:
            x = 0
            for ind in i:
                if ind == 537 or ind == 369:
                    available_coordinates.append((x, y))
                else:
                    pass
                x += 1
            y += 1
        item_coords, player_coords = random.sample(available_coordinates, 2)

        self.obstacles = []
        for i in self.map:
            for ind in i:
                if ind == 537 or ind == 369:
                    self.obstacles.append((0))
                elif ind == 112 or ind == 124:
                    self.obstacles.append(1)
                else:
                    pass

        self.player_location = [x[:] for x in [[0] * 24] * 24]
        self.player_location[player_coords[1]][player_coords[0]] = 1

        self.item_location = [x[:] for x in [[0] * 24] * 24]
        self.item_location[item_coords[1]][item_coords[0]] = 1

        self.mapSize = {"x": len(self.map[0]), "y": len(self.map)}
        self.first_distance = None
        # types of players, matches terrain
        self.types = {"Water": 1, "Lava": 2, "Jungle": 3}

        ### Player ###
        self.player3 = [player_coords[0],
                        player_coords[1], self.types["Jungle"]]
        self.previous_distance = []
        self.previous_action = []
        self.map_index = [level_index]
        ### Items ###
        player_type_stuff = [0, 3]
        item_type = random.sample(player_type_stuff, 1)
        self.items = []
        self.items.append([item_coords[0], item_coords[1],
                           True, item_type[0], 0])
        self.current_distance = []

    def get_state(self):
        state = []
        state.extend(list(map(float, self.map_index)))
        state.extend(list(map(float, self.obstacles)))

        for row in self.item_location:
            state.extend(list(map(float, row)))
        for row in self.player_location:
            state.extend(list(map(float, row)))
        if self.previous_distance != []:
            state.extend(list(map(float, self.previous_distance)))
        else:
            state.extend(list(map(float, [0])))
        if self.previous_action != []:
            state.extend(list(map(float, self.previous_action)))
        else:
            state.extend(list(map(float, [0])))
        distance = self.breadth_first_search((self.player3[0], self.player3[1]), (int(
            self.items[0][0]), int(self.items[0][1])), 2)
        self.current_distance.clear()
        self.current_distance.append(distance)
        state.extend(list(map(float, self.current_distance)))
        return state

    def reward_2(self, old_pos, new_pos, playerID, saved_pos=None):
        on_item = self.item_update(new_pos, playerID)
        if on_item:
            return 50
        else:
            return -1

    def another_reward(self, old_pos, new_pos, playerID, turns, saved_pos=None, old_distance=None):
        on_item = self.position_check(new_pos, playerID)
        distance_list = []
        self.previous_distance.clear()
        if old_distance == None:
            old_distance = 0
            self.previous_distance.append(old_distance)
        else:
            self.previous_distance.append(old_distance)
        if turns == 1:
            self.first_distance = self.getFirstDistance(playerID, old_pos)
        else:
            pass
        player = self.player3
        if on_item and self.gameOver():
            return 100, 0
       #     if turns == self.first_distance:
        #        return 60, 0
        #    elif (turns - self.first_distance) < 10:
        #        return 50, 0
        #    elif (turns - self.first_distance) < 20:
        #        return 40, 0
        #    else:
        #        return 30, 0
        distance = self.breadth_first_search(
            new_pos, (int(self.items[0][0]), int(self.items[0][1])), playerID)
        if distance:
            distance_list.append([distance, self.items[0]])
            closest_distance = distance_list[0][0]
        if old_distance == None:
            old_distance = closest_distance
            return -1, old_distance
        else:
            old_distance = closest_distance
            return -1, old_distance

    def getFirstDistance(self, playerID, old_pos):
        distance = self.breadth_first_search(
            old_pos, (int(self.items[0][0]), int(self.items[0][1])), playerID)
        return distance
    
    # returns boolean if the game is over, TRUE = game over, FALSE = game still going
    def gameOver(self):
        return not any(item[2] for item in self.items)

    def position_check(self, pos, playerID):
        player = pos
        on_item = self.item_update(
            (player[0], player[1]), playerID)
        return on_item

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
        player = self.player3

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

        if self.inBounds(destination, player_type):
            player[0] = destination[0]
            player[1] = destination[1]
            self.player3 = player
        destination = (player[0], player[1])

        return old_position, destination

    def item_update(self, pos, playerID=None):
        ret = False
        for ind, item in enumerate(self.items):
            # print(item)
            if (int(item[0]), int(item[1])) == pos and item[2]:
                self.items[ind][2] = False
                if item[3] == str(playerID):
                    their_item = True
                #print(item)
                print("asdfkfjlksaflkjdsa;lkfdsaf")
                ret = True
        return ret

    # Returns True if all the items have been collected, False if there are still active items
    def item_check(self):
        return not any(item[2] for item in self.items)

    def move_check(self, playerID, movement):
        player = self.player3

        # gets largest value in dictionary, which will correlate with the chosen movement
        max_value = max(movement.items(), key=operator.itemgetter(1))[1]

        # get all directions with that probability
        direction_possibilities = []
        for item in movement.items():
            if item[1] == max_value:
                direction_possibilities.append(item[0])

        direction = random.choice(direction_possibilities)
        state_direction = DIRECTIONS2[direction]
        self.previous_action.clear()
        self.previous_action.append(state_direction)
        step = DIRECTIONS[direction]

        player_pos = (player[0], player[1])
        player_type = player[2]

        destination = tuple(map(operator.add, player_pos, step))
        old_position = player[0], player[1]
        if self.inBounds(destination, player_type):
            return True
        else:
            return False

    def invalid_move_reward(self):
        self.previous_distance.clear()
        self.previous_distance.append(self.current_distance[0])
        return -1

    def item_ret(self):
        count = 0
        for item in self.items:
            if not item[2]:
                count += 1
        return str(count)
    
#    def turn_ret(self):
      #  return str(turns) 

    # finds shortest path between 2 nodes of a graph using BFS
    def breadth_first_search(self, start_pos, item_pos, playerID):
        player = self.player3
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
