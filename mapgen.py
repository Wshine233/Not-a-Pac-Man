import copy
import json
import os.path
import queue
import random

import arcade

MAX_TILE_COUNT = 256
MIN_ENTRY_COUNT = 3
MAX_ENTRY_COUNT = 6

MAP_UNIT_RESOURCES_PATH = "assets/map/"
TILE_SCALE = 3
MAP_MODELS = {}
MAP_UNITS = {}
UNITS_WEIGHT = {}

generate_step_count = 0


def load_resources():
    f = open(MAP_UNIT_RESOURCES_PATH + "Tiles.json")
    json_obj = json.load(f)
    f.close()

    for model in json_obj['models']:
        MAP_MODELS[model['id']] = model

    for unit in json_obj['tiles']:
        uid = unit['id']
        model_id = unit['model_id']
        MAP_UNITS[uid] = MapUnit(MAP_UNIT_RESOURCES_PATH + MAP_MODELS[model_id]['path'], TILE_SCALE, uid,
                                 unit['rotation'], unit['connect'], unit['entry'], unit['wall'])
        UNITS_WEIGHT[uid] = unit['weight']


class MapUnit(arcade.Sprite):
    def __init__(self, file_path: str, scale: float, uid: int, angle: int, connect: list, entry: list, wall: bool):
        super().__init__(file_path, scale)
        self.id = uid
        self.connect = connect
        self.angle = angle
        self.entry = entry
        self.is_wall = wall
        self.passable = False
        self.is_portal = False
        self.portal_id = None
        self.portal_des = [-1, -1]
        self.direction = None

    def placeable(self, connect_info) -> bool:
        """如果四个方向中有一个方向的可选单元里，没有可与当前单元邻接的，则无法放置"""
        for i in range(4):
            if connect_info[i].isdisjoint(self.connect[i]):
                return False
        return True

    def set_portal(self, pos, pid):
        self.is_portal = True
        self.portal_des = pos
        self.portal_id = pid

    def copy_sprite(self) -> arcade.Sprite:
        return copy.copy(self)


def get_from_center(map_info_2d: list[list[MapUnit]], get_func) -> list[int, int] | None:
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    row_cot = len(map_info_2d)
    col_cot = len(map_info_2d[0])
    vis = get_vis_matrix(map_info_2d)

    center = [row_cot // 2, col_cot // 2]
    vis[center[0]][center[1]] = True
    q = queue.Queue()
    q.put(center)

    while q.not_empty:
        pos = q.get()
        cell = map_info_2d[pos[0]][pos[1]]
        if get_func(cell):
            return pos

        for i in range(4):
            next_pos = [pos[0] + dir_vec[i][0], pos[1] + dir_vec[i][1]]
            if not in_bound(next_pos, row_cot, col_cot) or vis[next_pos[0]][next_pos[1]]:
                continue
            vis[next_pos[0]][next_pos[1]] = True
            q.put(next_pos)
    return None


def set_passable(map_info_2d: list[list[MapUnit]]):
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    row_cot = len(map_info_2d)
    col_cot = len(map_info_2d[0])
    vis = get_vis_matrix(map_info_2d)

    start_pos = get_from_center(map_info_2d, lambda x: not x.is_wall)
    vis[start_pos[0]][start_pos[1]] = True
    q = queue.Queue()
    q.put(start_pos)

    while not q.empty():
        pos = q.get()
        cell = map_info_2d[pos[0]][pos[1]]
        cell.passable = True

        for i in range(4):
            next_pos = [pos[0] + dir_vec[i][0], pos[1] + dir_vec[i][1]]
            if not in_bound(next_pos, row_cot, col_cot) or vis[next_pos[0]][next_pos[1]] \
                    or map_info_2d[next_pos[0]][next_pos[1]].is_wall:
                continue
            vis[next_pos[0]][next_pos[1]] = True
            q.put(next_pos)


def distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def choose_portal(map_info_2d: list[list[MapUnit]]) -> list[int, list]:
    edges = get_edge(map_info_2d)
    entry_list = list(filter(lambda x: map_info_2d[x[0]][x[1]].passable, edges))
    random.shuffle(entry_list)
    portal_list = []
    min_dis = None

    for i in range(1, len(entry_list) // 2 * 2, 2):
        portal_list.append([entry_list[i], entry_list[i-1]])
        dis = distance(entry_list[i], entry_list[i-1])
        min_dis = min(min_dis, dis) if min_dis is not None else dis
    return [min_dis, portal_list]


def set_portal(map_info_2d: list[list[MapUnit]]):
    min_dis = -1
    portal_list = []
    for _ in range(8000):
        portal = choose_portal(map_info_2d)
        if portal[0] is None:
            continue
        if min_dis < portal[0]:
            min_dis = portal[0]
            portal_list = portal[1]

    if not portal_list:
        # 没有找到portal则直接不设置
        return
    for i in range(len(portal_list)):
        pair = portal_list[i]
        map_info_2d[pair[0][0]][pair[0][1]].set_portal(pair[1], i)
        map_info_2d[pair[1][0]][pair[1][1]].set_portal(pair[0], i)


def copy_2d_list(x):
    return [copy.copy(ele) for ele in x]


def in_bound(next_pos, row: int, col: int):
    return 0 <= next_pos[0] < row and 0 <= next_pos[1] < col


def get_neighbour_pos(map_info, pos) -> list:
    """获取周围的格子坐标"""
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    neighbour = [[pos[0] + dir_vec[i][0], pos[1] + dir_vec[i][1]] for i in range(4)
                 if in_bound([pos[0] + dir_vec[i][0], pos[1] + dir_vec[i][1]], len(map_info), len(map_info[0]))]
    return neighbour


def get_connect_info(map_info, pos) -> list:
    dir_vec = [[-1, 0], [0, 1], [1, 0], [0, -1]]
    ans = []
    wall = get_wall()
    for i in range(4):
        next_pos = [pos[0] + dir_vec[i][0], pos[1] + dir_vec[i][1]]
        if in_bound(next_pos, len(map_info), len(map_info[0])):
            ans.append(map_info[next_pos[0]][next_pos[1]])
        else:
            ans.append(set(MAP_UNITS.keys()))
    return ans


def get_vis_matrix(map_info):
    row = len(map_info)
    col = len(map_info[0])
    return [[False for _ in range(col)] for _ in range(row)]


def collapse(map_info, x: int, y: int, num: int, force=False) -> list:
    num_set = {num}
    if not force and map_info[x][y].isdisjoint(num_set):
        return []  # 原先该格就不能放这个num

    map_info = copy_2d_list(map_info)
    map_info[x][y] = num_set
    vis = get_vis_matrix(map_info)
    vis[x][y] = True
    q = queue.Queue()
    q.put([x, y])
    while not q.empty():
        pos = q.get()
        next_pos = get_neighbour_pos(map_info, pos)
        for npos in next_pos:
            """对于每一个有效位置，更新候选集合的可选情况"""
            if vis[npos[0]][npos[1]]:
                continue

            unit_set = map_info[npos[0]][npos[1]]
            new_set = set()
            connect_info = get_connect_info(map_info, npos)

            for _id in unit_set:
                if MAP_UNITS[_id].placeable(connect_info):
                    # 可放置则继续留在候选集合内
                    new_set.add(_id)

            if len(new_set) == 0:
                # 有一个格子无法放任何单元则说明坍缩失败，需要回溯
                return []

            # 可坍缩，将该位置入队，如果前后一样则不需要入队
            if unit_set != new_set:
                vis[npos[0]][npos[1]] = True
                map_info[npos[0]][npos[1]] = new_set
                q.put(npos)
    return map_info


def get_direction(pos, row_cot, col_cot) -> int:
    """获取一个坐标所在的边缘方向，0、1、2、3、4分别代表上、右、下、左、中，四个角的情况会被算作左右方向"""
    if pos[1] == 0:
        return 3
    if pos[1] == col_cot - 1:
        return 1
    if pos[0] == 0:
        return 0
    if pos[0] == row_cot - 1:
        return 2
    return 4


def get_entry(direction, shuffle=False, seed=0) -> list:
    ls = []
    for tile in MAP_UNITS.values():
        if tile.entry[direction]:
            ls.append(tile.id)
    if shuffle:
        # random.seed = seed
        random.shuffle(ls)
    return ls


def get_wall():
    ls = list(filter(lambda x: x.is_wall, MAP_UNITS.values()))
    return random.choice(ls).id


def get_edge(map_info: list[list]):
    max_col = len(map_info[0]) - 1
    max_row = len(map_info) - 1
    range_horizontal = range(1, max_col)  # 地图宽度必须大于3
    range_vertical = range(1, max_row)
    edges = list(map(lambda x: [0, x], range_horizontal)) \
            + list(map(lambda x: [max_row, x], range_horizontal)) \
            + list(map(lambda x: [x, 0], range_vertical)) \
            + list(map(lambda x: [x, max_col], range_vertical))
    return edges


def set_entry(seed, map_info, min_entry, max_entry) -> list:
    """在地图边缘随机添加出入口，数量一定是偶数"""
    max_col = len(map_info[0]) - 1
    max_row = len(map_info) - 1
    edges = get_edge(map_info)

    new_map = []
    while not new_map:
        """不断生成entry然后collapse直到合法为止"""
        new_map = copy_2d_list(map_info)
        wall = get_wall()
        # random.seed = seed
        cot = random.randint(min_entry, max_entry)
        cot = cot // 2 * 2
        random.shuffle(edges)

        for pos in edges[0:cot]:
            dir_num = get_direction(pos, max_row + 1, max_col + 1)
            entry = get_entry(dir_num, shuffle=True, seed=seed)[0]
            new_map = collapse(new_map, pos[0], pos[1], entry, force=True)
            if not new_map:
                break

        if not new_map:
            continue

        for pos in edges[cot:] + [[0, max_col], [max_row, max_col], [0, 0], [max_row, 0]]:
            new_map = collapse(new_map, pos[0], pos[1], wall, force=True)
            if not new_map:
                break

    return new_map


def random_select(set_ele: set, seed):
    # random.seed = seed
    cot = len(set_ele)
    return list(set_ele)[random.randint(0, cot - 1)]


def shuffle_by_weight(ele_list: list, weight_list: list, seed: int):
    # random.seed = seed
    rand_list = []
    for i in range(len(ele_list)):
        num = ele_list[i]
        rand_list += [num] * weight_list[i]
    for i in range(len(ele_list) - 1):
        index = random.randint(0, len(rand_list) - 1)
        num = rand_list[index]
        index = ele_list.index(num)
        ele_list[i], ele_list[index] = ele_list[index], ele_list[i]
        rand_list = list(filter(lambda x: x != num, rand_list))


def dfs_gen(map_info, row_cot, col_cot, seed):
    min_entropy = MAX_TILE_COUNT + 1
    min_cell = []
    sorted_cell = []
    for i in range(row_cot):
        for j in range(col_cot):
            """找到Entropy最小的进行Collapse，虽说最小但也一定要大于1"""
            cell = map_info[i][j]
            entropy = len(cell)
            if entropy <= 1:
                continue
            if min_entropy > entropy:
                min_entropy = entropy
                min_cell = [[i, j, cell]]
                continue
            if min_entropy == entropy:
                min_cell.append([i, j, cell])
            sorted_cell.append([i, j, cell])

    """每次collapse都保证了没有为0的，所以当没找到大于1的最小时，则说明地图生成完毕"""
    if min_entropy > MAX_TILE_COUNT:
        return map_info

    """先把每个cell打乱，然后再把每个cell的可选tiles按权重打乱，然后循环尝试collapse，成功一个就结束，进入下一次迭代"""
    random.shuffle(sorted_cell)
    sorted_cell.sort(key=lambda x: len(x[2]))
    random.shuffle(min_cell)
    for cell in sorted_cell:
        global generate_step_count
        if generate_step_count > 200:
            return []
        generate_step_count += 1

        ls = list(cell[2])
        shuffle_by_weight(ls, list(map(lambda x: UNITS_WEIGHT[x], ls)), seed)
        for uid in ls:
            new_map = collapse(map_info, cell[0], cell[1], uid)
            new_map = dfs_gen(new_map, row_cot, col_cot, seed) if new_map else new_map
            if new_map:
                return new_map  # 后续递归的所有坍缩均成功，返回生成好的地图
            # 否则继续循环
        # 没有成功生成，换下一个格子
    return []  # 依然没有成功，返回[]


def to_sprite_map_info(map_info: list):
    info = []
    for i in range(len(map_info)):
        row = map_info[i]
        row_info = []
        info.append(row_info)
        for j in range(len(row)):
            cell = row[j]
            if len(cell) > 1:
                raise KeyError('Multiple unit')
            uid = list(cell)[0]
            unit = MAP_UNITS[uid].copy_sprite()
            d = get_direction([i, j], len(map_info), len(map_info[0]))
            unit.direction = d if d < 4 else None
            row_info.append(unit)
    return info


def try_generate_map(seed, row_cot, col_cot):
    global generate_step_count
    generate_step_count = 0
    random.seed(seed)
    map_info = [[set(MAP_UNITS.keys()) for _ in range(col_cot)] for _ in range(row_cot)]
    map_info = set_entry(seed, map_info, MIN_ENTRY_COUNT, MAX_ENTRY_COUNT)
    map_info = dfs_gen(map_info, row_cot, col_cot, seed)

    print(f"Map generate step count: {generate_step_count}")
    return map_info


def generate_map(seed, row_cot, col_cot):
    map_info = []
    while not map_info:
        map_info = try_generate_map(seed, row_cot, col_cot)

    map_info = to_sprite_map_info(map_info)
    set_passable(map_info)
    set_portal(map_info)
    map_info = get_map_sprites(map_info)
    return map_info


def get_map_sprites(map_info: list) -> list:
    map_seq = [cell for row in map_info for cell in row]
    return map_seq


def save_map(map_info: list):
    map_obj = []
    for row in map_info:
        r = []
        map_obj.append(r)
        for cell in row:
            r.append(list(cell))

    if not os.path.exists("cache/map"):
        os.makedirs("cache/map")
    with open(f"cache/map/{random.randint(100000000, 999999999)}.json", mode='w') as f:
        json.dump(map_obj, f)


def in_bound_2d(pos: list, center: list, width: float, height: float) -> bool:
    left = center[0] - width / 2
    right = center[0] + width / 2
    top = center[1] - height / 2
    bottom = center[1] + height / 2
    return left <= pos[0] < right and top <= pos[1] < bottom


load_resources()
