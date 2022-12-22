import copy
import queue
import random

import arcade

MOB_PATH = "assets/mob/"

ENEMY_RED_PATH = "enemy_red.png"
ENEMY_PINK_PATH = "enemy_pink.png"
ENEMY_ORANGE_PATH = "enemy_orange.png"
ENEMY_GREEN_PATH = "enemy_green.png"

AI_RANDOM = "ai_random_path"  # 随机游走
AI_TRACE = "ai_trace"  # 跟踪玩家
AI_TRACE_FRONT = "ai_trace_front"  # 跟踪玩家前方两格
AI_TRACE_RANGE = "ai_trace_range"  # 在一定距离内跟踪玩家，平时随机游走

map_info = []


def set_map(map_units, row_cot, col_cot):
    global map_info
    map_info = []
    index = 0
    for i in range(row_cot):
        row = []
        map_info.append(row)
        for j in range(col_cot):
            row.append(map_units[index][1])
            index += 1


def get_fgh_grid(row, col):
    return [[[-1, -1, -1, -1] for _ in range(col)] for _ in range(row)]


def h_func(start_pos, end_pos, last_pos, direction):
    s = distance(start_pos, end_pos)
    d = get_direction(last_pos, start_pos)
    if d is None or d != direction:
        s *= 1.2
    return s


def distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def coord_to_index(coord_pos, col_cot):
    return coord_pos[0] * col_cot + coord_pos[1]


def index_to_coord(index, col_cot):
    return [index // col_cot, index % col_cot]


def in_bound(pos, row_cot, col_cot):
    return 0 <= pos[0] < row_cot and 0 <= pos[1] < col_cot


# def get_neighbour(coord_pos, direction, row_cot, col_cot):
#     dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
#     x = dir_vec[direction]
#     return [coord_pos[0] + x[0], coord_pos[1] + x[1]]
#
#
# def get_neighbour_index(coord_pos, direction, col_cot):
#     return coord_to_index(get_neighbour(coord_pos, direction), col_cot)


def get_neighbour_list(coord_pos, row_cot, col_cot):
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    neighbour_list = map(lambda x: [coord_pos[0] + x[0], coord_pos[1] + x[1]], dir_vec)
    neighbour_list = list(map(lambda x: x if in_bound(x, row_cot, col_cot) else None, neighbour_list))
    return neighbour_list


def get_neighbour_indexes(coord_pos, row_cot, col_cot):
    return list(map(lambda x: coord_to_index(x, col_cot) if x else None,
                    get_neighbour_list(coord_pos, row_cot, col_cot)))


def ai_random(entity, row_cot, col_cot) -> list:
    dir_rev = [2, 3, 0, 1]
    d = dir_rev[entity.direction]
    ls = get_neighbour_list(entity.coord_pos, row_cot, col_cot)
    front = ls[entity.direction]
    if front is not None and not map_info[front[0]][front[1]].is_wall and random.random() < 0.5:
        return front

    back = ls.pop(d)
    random.shuffle(ls)

    for step in ls:
        if step is None or map_info[step[0]][step[1]].is_wall:
            continue
        return step
    return back


def ai_trace_base(entity, trace_coord, row_cot, col_cot) -> list:
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    grid = get_fgh_grid(row_cot, col_cot)
    tc = trace_coord
    ec = entity.coord_pos
    if tc == ec:
        return ec

    q = queue.PriorityQueue()
    direction = entity.direction
    grid[ec[0]][ec[1]] = [h_func(ec, tc, ec, direction), 0, h_func(ec, tc, ec, direction), direction]
    q.put((grid[ec[0]][ec[1]][0], grid[ec[0]][ec[1]][2], ec))

    while not q.empty():
        pos = q.get()[2]

        cell = grid[pos[0]][pos[1]]
        for i in range(4):
            next_pos = [pos[0] + dir_vec[i][0], pos[1] + dir_vec[i][1]]
            if not in_bound(next_pos, row_cot, col_cot):
                continue
            next_cell = grid[next_pos[0]][next_pos[1]]
            next_info = map_info[next_pos[0]][next_pos[1]]
            if next_cell[0] >= 0 or next_info.is_wall:
                continue

            next_cell[1] = cell[1] + 1
            next_cell[2] = h_func(next_pos, tc, pos, cell[3])
            next_cell[3] = get_direction(pos, next_pos)
            next_cell[0] = next_cell[1] + next_cell[2]
            if next_pos == tc:
                break
            q.put((next_cell[0], next_cell[2], next_pos))

    if grid[tc[0]][tc[1]][0] < 0:
        raise Exception("寻路失败，可能没有通路")
    back_pos = tc
    back_cell = grid[tc[0]][tc[1]]
    while back_cell[1] > 1:
        for i in range(4):
            next_pos = [back_pos[0] + dir_vec[i][0], back_pos[1] + dir_vec[i][1]]
            if not in_bound(next_pos, row_cot, col_cot):
                continue
            next_cell = grid[next_pos[0]][next_pos[1]]
            if next_cell[1] != back_cell[1] - 1:
                continue
            back_pos = next_pos
            back_cell = next_cell
            break
    return back_pos


def ai_trace(entity, row_cot, col_cot) -> list:
    return ai_trace_base(entity, entity.trace_target.coord_pos, row_cot, col_cot)
    pass


def ai_trace_front(entity, row_cot, col_cot) -> list:
    target_pos = entity.trace_target.coord_pos

    if distance(target_pos, entity.coord_pos) > 4:
        return ai_trace_base(entity, target_pos, row_cot, col_cot) \
            if random.random() > 0.4 else ai_random(entity, row_cot, col_cot)

    pos = target_pos
    pos_list = []
    for i in range(pos[0] - 1, pos[0] + 2):
        for j in range(pos[1] - 1, pos[1] + 2):
            pos = [i, j]
            if in_bound(pos, row_cot, col_cot) and map_info[pos[0]][pos[1]].passable and pos != target_pos:
                pos_list.append(pos)
    if len(pos_list) > 0:
        pos = random.choice(pos_list)
        pos = ai_trace_base(entity, pos, row_cot, col_cot)
    else:
        pos = entity.coord_pos

    if pos == target_pos:
        return entity.coord_pos
    return pos


def ai_trace_range(entity, row_cot, col_cot) -> list:
    trace_range = 8
    dis = distance(entity.coord_pos, entity.trace_target.coord_pos)
    if dis <= trace_range and random.randint(0, trace_range * 2) <= trace_range - dis:
        return ai_trace_base(entity, entity.trace_target.coord_pos, row_cot, col_cot)
    return ai_random(entity, row_cot, col_cot)


def get_direction(coord, next_coord):
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    pos = [next_coord[0] - coord[0], next_coord[1] - coord[1]]
    try:
        return dir_vec.index(pos)
    except ValueError:
        return -1


class Enemy(arcade.Sprite):
    coord_pos = [0, 0]
    direction = 0
    killed = False
    trace_target = None

    def __init__(self, path, ai_type, speed):
        super().__init__(MOB_PATH + path)
        self.ai_type = ai_type  # ai类别
        self.speed = speed  # 独立速度（多少秒走一格，越小越快）
        self.last_update = 0

        if ai_type == AI_RANDOM:
            self.ai = ai_random
        elif ai_type == AI_TRACE:
            self.ai = ai_trace
        elif ai_type == AI_TRACE_FRONT:
            self.ai = ai_trace_front
        elif ai_type == AI_TRACE_RANGE:
            self.ai = ai_trace_range

    def update_ai(self, time, row_cot, col_cot):
        acceleration = 1
        if self.trace_target.life == 0:
            acceleration = 1.4

        if time - self.last_update < self.speed / acceleration:
            return
        self.last_update = time

        next_step = self.ai(self, row_cot, col_cot)
        next_step = next_step if next_step else self.coord_pos
        self.set_direction(get_direction(self.coord_pos, next_step))
        self.coord_pos = next_step

    def set_direction(self, direction):
        if direction == -1:
            return
        self.direction = direction


ENEMY_RED = Enemy(ENEMY_RED_PATH, AI_TRACE_RANGE, 0.4)
ENEMY_PINK = Enemy(ENEMY_PINK_PATH, AI_TRACE_FRONT, 0.25)
ENEMY_ORANGE = Enemy(ENEMY_ORANGE_PATH, AI_RANDOM, 0.2)
ENEMY_GREEN = Enemy(ENEMY_GREEN_PATH, AI_TRACE, 0.6)


class EnemyList:
    entities = []
    sprite_list = arcade.SpriteList()
    timer = 0
    scale = 1.0

    def __init__(self):
        pass

    def add_enemy(self, enemy_type, target, count):
        for i in range(count):
            enemy = copy.copy(enemy_type)
            enemy.scale = self.scale
            enemy.trace_target = target
            self.entities.append(enemy)
            self.sprite_list.append(enemy)

    def remove_enemy(self, sprite):
        self.entities.remove(sprite)
        self.sprite_list.remove(sprite)

    def clear_enemy(self):
        self.entities.clear()
        self.sprite_list.clear()

    def draw(self, filter=None):
        self.sprite_list.draw(filter=filter)

    def update_ai(self, delta, row_cot, col_cot):
        self.timer += delta
        for entity in self.entities:
            entity.update_ai(self.timer, row_cot, col_cot)

    def set_spawn_point(self, coord_list):
        for i in range(min(len(coord_list), len(self.entities))):
            self.entities[i].coord_pos = coord_list[i]

    def set_scale(self, scale):
        for ent in self.entities:
            ent.scale = scale
        self.scale = scale
