import json
import random
import time

import arcade
from arcade import gl

import mapgen
import chara
import item
import enemy

GAME_CONFIG_PATH = "assets/config/level_config.json"

GAME_STATE_READY = 0
GAME_STATE_PLAYING = 1
GAME_STATE_OVER = 2
GAME_STATE_FAIL = 3

GAME_LIFE = 3

UNIT_WIDTH = 16
UNIT_HEIGHT = 16

SOUND_FIRST_READY = arcade.load_sound('assets/sound/ready.wav')
SOUND_MOVE = arcade.load_sound('assets/sound/move.wav')
SOUND_FAIL = arcade.load_sound('assets/sound/hard_noise.wav')
SOUND_LAST_LIFE = arcade.load_sound('assets/sound/soft_noise.wav')
LAST_LIFE_PLAYER = arcade.play_sound(SOUND_LAST_LIFE, volume=0.0, looping=True)


def reverse_direction(direction: int):
    if direction < 0 or direction >= 4:
        raise ValueError("方向只有0、1、2、3")
    return (direction + 2) % 4


class GameView(arcade.View):
    sprite_map_list = None
    sprite_chara_list = None
    sprite_coin_list = None
    sprite_portal_list = None
    enemy_list = None

    map = None
    row_cot = None
    col_cot = None
    chara = chara.Chara(GAME_LIFE)
    config = None

    timer = 0.0
    game_speed = 0.3
    game_state = GAME_STATE_READY

    input_queue = []

    def __init__(self, window):
        # mapgen.load_resources()
        super().__init__(window)
        self.sprite_chara_list = arcade.SpriteList()
        self.sprite_chara_list.append(self.chara)
        self.chara.scale = mapgen.TILE_SCALE
        self.map_left_top = None
        self.map_right_bottom = None

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def get_pos_matrix(self):
        width_unit = UNIT_WIDTH * mapgen.TILE_SCALE
        height_unit = UNIT_HEIGHT * mapgen.TILE_SCALE
        w = self.window.width
        h = self.window.height

        c_x = w / 2
        c_y = h / 2
        lt_x = c_x - self.col_cot * width_unit / 2
        lt_y = c_y - self.row_cot * height_unit / 2
        matrix = []
        for i in range(self.row_cot - 1, -1, -1):
            y = lt_y + i * height_unit + height_unit / 2
            for j in range(self.col_cot):
                matrix.append([lt_x + j * width_unit + width_unit / 2, y])
        return matrix

    def load_game(self, map_seq: list, row_cot: int, col_cot: int):
        self.load_config()
        self.load_map(map_seq, row_cot, col_cot)
        self.load_items()
        self.load_enemies()

    def load_config(self):
        try:
            with open(GAME_CONFIG_PATH) as f:
                self.config = json.load(f)
        except (OSError, TypeError) as e:
            self.config = {
                'enemy': [1, 1, 1, 1]
            }

    def set_map_unit_pos(self, pos_matrix):
        map_seq = self.map
        for i in range(len(map_seq)):
            sprite = map_seq[i][1]
            sprite.position = pos_matrix[i]

    def revert_map_unit_pos(self):
        map_seq = self.map
        for cell in map_seq:
            sprite = cell[1]
            sprite.position = cell[0]

    def load_map(self, map_seq: list, row_cot: int, col_cot: int):
        self.row_cot = row_cot
        self.col_cot = col_cot
        width_unit = UNIT_WIDTH * mapgen.TILE_SCALE
        height_unit = UNIT_HEIGHT * mapgen.TILE_SCALE
        matrix = self.get_pos_matrix()
        self.map_left_top = [matrix[0][0] - width_unit / 2, matrix[0][1] + height_unit / 2]
        self.map_right_bottom = [matrix[-1][0] + width_unit / 2, matrix[-1][1] - height_unit / 2]
        """构造SpriteList，将matrix坐标赋给list"""
        map_unit_list = arcade.SpriteList()
        self.map = []
        for i in range(len(map_seq)):
            sprite = map_seq[i]
            map_unit_list.append(sprite)
            sprite.center_x = matrix[i][0]
            sprite.center_y = matrix[i][1]
            self.map.append([matrix[i], sprite, i])
        self.sprite_map_list = map_unit_list

    def load_items(self):
        self.sprite_coin_list = arcade.SpriteList()
        self.sprite_portal_list = arcade.SpriteList()
        for i in range(len(self.map)):
            cell = self.map[i]
            if not cell[1].passable:
                continue
            if cell[1].is_portal:
                portal = item.Portal(cell[0], mapgen.TILE_SCALE, self.index_to_coord(i), cell[1].portal_id)
                self.sprite_portal_list.append(portal)
            else:
                coin_data = item.Coin(cell[0], mapgen.TILE_SCALE, self.index_to_coord(i))
                self.sprite_coin_list.append(coin_data)

    def load_enemies(self):
        enemy.set_map(self.map, self.row_cot, self.col_cot)
        self.enemy_list = enemy.EnemyList()
        types = [enemy.ENEMY_RED, enemy.ENEMY_PINK, enemy.ENEMY_GREEN, enemy.ENEMY_ORANGE]
        total = 0

        for i in range(4):
            self.enemy_list.add_enemy(types[i], self.chara, self.config['enemy'][i])
            total += self.config['enemy'][i]

        points = list(self.map)
        random.shuffle(points)
        spawn = []
        for unit in points:
            if total <= 0:
                break
            coord = self.index_to_coord(unit[2])
            if not unit[1].passable or coord == self.chara.coord_pos:
                continue
            spawn.append(coord)
            total -= 1
        self.enemy_list.set_spawn_point(spawn)
        self.enemy_list.set_scale(mapgen.TILE_SCALE)

    def get_pos_on_map(self, pos: list):
        for i in range(len(self.map)):
            data = self.map[i]
            if mapgen.in_bound_2d(pos, data[1].position, UNIT_WIDTH * mapgen.TILE_SCALE,
                                  UNIT_HEIGHT * mapgen.TILE_SCALE):
                return i
        return None

    def in_bound(self, pos):
        return 0 <= pos[0] < self.row_cot and 0 <= pos[1] < self.col_cot

    def get_neighbour_index(self, direction, index=None, pos=None):
        dir_map = [[-1, 0], [0, 1], [1, 0], [0, -1]]
        if index is not None:
            pos = self.index_to_coord(index)

        neighbour_pos = [pos[0] + dir_map[direction][0], pos[1] + dir_map[direction][1]]
        if self.in_bound(neighbour_pos):
            index = neighbour_pos[0] * self.col_cot + neighbour_pos[1]
            return index
        return None

    def get_next_step_coord(self, direction):
        """获得下一步该将角色落在哪里，如果无法朝当前角色朝向移动，则返回当前位置（即不移动）"""
        next_index = self.get_neighbour_index(direction, pos=self.chara.coord_pos)
        if next_index is None or self.map[next_index][1].is_wall:
            return self.chara.coord_pos
        return self.index_to_coord(next_index)

    def coord_to_index(self, coord_pos):
        return coord_pos[0] * self.col_cot + coord_pos[1]

    def index_to_coord(self, index):
        return [index // self.col_cot, index % self.col_cot]

    def is_portal(self, pos):
        index = self.coord_to_index(pos)
        return self.map[index][1].is_portal

    def get_portal_des(self, pos):
        index = self.coord_to_index(pos)
        des = self.map[index][1].portal_des
        index = self.coord_to_index(des)
        return [des, reverse_direction(self.map[index][1].direction)]

    def on_draw(self):
        self.clear()

        if self.game_state == GAME_STATE_PLAYING and self.chara.life == 0 and random.random() < 0.005:
            pos = self.get_pos_matrix()
            random.shuffle(pos)
            self.set_map_unit_pos(pos)
        elif self.game_state == GAME_STATE_PLAYING and self.chara.life == 0 and random.random() < 0.1:
            self.revert_map_unit_pos()

        if self.sprite_map_list:
            self.sprite_map_list.draw(filter=gl.NEAREST)
        if self.sprite_portal_list:
            self.sprite_portal_list.draw(filter=gl.NEAREST)
        if self.sprite_coin_list:
            self.sprite_coin_list.draw(filter=gl.NEAREST)
        if self.sprite_chara_list:
            self.sprite_chara_list.draw(filter=gl.NEAREST)
        if self.enemy_list:
            self.enemy_list.draw(filter=gl.NEAREST)

        if self.game_state == GAME_STATE_OVER:
            self.update_fade_out()

    def walk_input_process(self, input_info):
        """处理走路方向的输入"""
        if self.game_state != GAME_STATE_PLAYING or input_info[0] != 'Key':
            return
        if input_info[1] == arcade.key.UP:
            self.chara.direction = 0
        elif input_info[1] == arcade.key.RIGHT:
            self.chara.direction = 1
        elif input_info[1] == arcade.key.DOWN:
            self.chara.direction = 2
        elif input_info[1] == arcade.key.LEFT:
            self.chara.direction = 3
        else:
            return
        self.chara.update_angle()
        # print(self.chara.direction)

    def tick_chara(self):
        if self.game_state != GAME_STATE_PLAYING:
            return

        if self.chara.god_mode:
            self.chara.god_mode_time -= 1
            if self.chara.god_mode_time <= 0:
                self.chara.god_mode = False

        pos = self.chara.coord_pos
        if self.is_portal(pos) and not self.chara.passing_portal:
            pos = self.get_portal_des(pos)
            self.chara.passing_portal = True
            self.chara.direction = pos[1]
            self.chara.update_angle()
            pos = pos[0]
        else:
            pos = self.get_next_step_coord(self.chara.direction)
            if pos != self.chara.coord_pos:
                self.chara.passing_portal = False
                arcade.play_sound(SOUND_MOVE)
        self.chara.coord_pos = pos

    def tick_update_coin(self):
        if self.game_state != GAME_STATE_PLAYING:
            return

        for i in range(len(self.sprite_coin_list.sprite_list) - 1, -1, -1):
            sprite = self.sprite_coin_list.sprite_list[i]
            coin_data = sprite
            if coin_data.coord_pos == self.chara.coord_pos:
                self.sprite_coin_list.pop(i)

        if len(self.sprite_coin_list) == 0:
            self.game_win()

    def tick(self):
        while len(self.input_queue) > 0:
            info = self.input_queue.pop(0)
            self.walk_input_process(info)
        self.tick_chara()
        self.tick_update_coin()
        self.input_queue.clear()

        self.fade_out_tick = True
        pass

    def death_judge(self):
        if self.chara.god_mode:
            return
        pos = self.chara.coord_pos
        flag = True
        for e in self.enemy_list.sprite_list:
            if e.coord_pos == pos:
                self.game_state = GAME_STATE_FAIL
                e.killed = True if flag else False
                flag = False

    def on_update(self, delta_time: float):
        self.timer += delta_time
        if self.timer > self.game_speed:
            self.timer = 0
            self.tick()

        if self.game_state == GAME_STATE_PLAYING:
            self.enemy_list.update_ai(delta_time, self.row_cot, self.col_cot)

        self.update_position(self.sprite_chara_list, self.enemy_list.sprite_list)

        if self.game_state == GAME_STATE_PLAYING:
            self.chara.update_state()
            self.death_judge()

        self.fail_update(delta_time)
        self.ready_update(delta_time)

    def update_position(self, *move_list):
        for entities in move_list:
            for entity in entities:
                index = self.coord_to_index(entity.coord_pos)
                entity.position = self.map[index][0]

    def on_key_press(self, symbol: int, modifiers: int):
        self.input_queue.append(['Key', symbol, modifiers])
        if self.game_state == GAME_STATE_PLAYING and modifiers == 18 and symbol == arcade.key.W:
            self.game_win()

    def choose_spawn_point(self):
        wall = True
        index = None
        while wall:
            index = random.randint(0, len(self.map) - 1)
            info = self.map[index]
            wall = not info[1].passable
        return index

    def start_game(self):
        arcade.play_sound(SOUND_FIRST_READY)
        self.set_ready(first=True)

    """游戏胜利部分"""
    def game_win(self):
        self.game_state = GAME_STATE_OVER
        arcade.stop_sound(LAST_LIFE_PLAYER)

    """游戏结束部分"""
    FADE_DELAY = 120
    fade_out_progress = 0
    fade_out_tick = False
    fade_out_delay = FADE_DELAY
    fade_finish = False

    def reset_fade(self):
        self.fade_out_progress = 0
        self.fade_out_tick = False
        self.fade_out_delay = self.FADE_DELAY
        self.fade_finish = False

    def update_fade_out(self):
        if self.game_state != GAME_STATE_OVER:
            return
        if self.fade_out_delay > 0:
            self.fade_out_delay -= 1
            return

        self.fade_out_progress += 3

        arcade.draw_rectangle_filled(self.window.width / 2, self.window.height / 2, self.window.width, self.window.height,
                                     (255, 255, 255, min(255, self.fade_out_progress)))

        if not self.fade_finish and self.fade_out_progress > 500:
            self.fade_finish = True
            self.after_fade_out()

    def after_fade_out(self):
        self.window.show_credit()

    """游戏失败部分"""
    FAIL_DELAY = 2
    FAIL_DURATION = 5
    fail_timer = 0
    failed = False

    def reset_fail(self):
        self.fail_timer = 0
        self.failed = False
        for cell in self.map:
            cell[1].color = arcade.color.WHITE
        self.revert_map_unit_pos()
        self.chara.set_data_error(False)

    def fail_update(self, delta):
        if self.game_state != GAME_STATE_FAIL:
            return

        self.fail_timer += delta
        if self.fail_timer < self.FAIL_DELAY:
            return
        if self.fail_timer > self.FAIL_DURATION and self.chara.life > 0:
            self.reset_fail()
            self.chara.life -= 1
            self.set_ready()
            return
        elif self.chara.life <= 0 and self.fail_timer > self.FAIL_DURATION - 0.5:
            self.enemy_list.clear_enemy()
            self.chara.set_data_error(True)
            pos_matrix = [[random.randrange(0, self.window.width), random.randrange(0, self.window.height)]
                          for _ in range(self.row_cot * self.col_cot)]
            self.set_map_unit_pos(pos_matrix)

            if self.fail_timer > self.FAIL_DURATION + 0.1:
                time.sleep(2)
                self.window.show_failed_view()
            return

        if not self.failed:
            self.on_fail()
            self.failed = True

        color = arcade.color.RED
        for cell in self.map:
            cell[1].color = color

        pos_matrix = self.get_pos_matrix()
        random.shuffle(pos_matrix)
        self.set_map_unit_pos(pos_matrix)

    def on_fail(self):
        arcade.stop_sound(LAST_LIFE_PLAYER)
        arcade.play_sound(SOUND_FAIL, volume=0.8)
        if self.chara.life > 0:
            self.chara.set_data_error(True)
            ls = list(filter(lambda x: x.killed, self.enemy_list.sprite_list))
            for e in ls:
                self.enemy_list.remove_enemy(e)
        else:
            self.window.background_color = arcade.color.RED
            self.sprite_portal_list.clear()

    """游戏准备部分"""
    READY_DELAY = 3
    ready_timer = 0

    def set_ready(self, first=False):
        self.game_state = GAME_STATE_READY
        self.ready_timer = 0
        index = self.choose_spawn_point()
        self.chara.coord_pos = self.index_to_coord(index)
        self.chara.set_god_mode(True, 20)
        self.READY_DELAY = 6 if first else 3
        if self.chara.life == 0:
            LAST_LIFE_PLAYER.volume = 0.6
            LAST_LIFE_PLAYER.play()

    def ready_update(self, delta):
        if self.game_state != GAME_STATE_READY:
            return

        self.ready_timer += delta
        if self.ready_timer < self.READY_DELAY:
            return

        self.game_state = GAME_STATE_PLAYING
        self.tick_update_coin()
