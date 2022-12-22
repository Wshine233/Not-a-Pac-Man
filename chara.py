import arcade

CHARA_PATH = 'assets/mob/chara.png'

GOD_MODE_COLOR = arcade.color_from_hex_string('#ffdf00')
IDLE_COLOR = arcade.color.GRAY
DATA_ERROR_COLOR = arcade.color.WHITE


class Chara(arcade.Sprite):
    def __init__(self, life):
        super().__init__(CHARA_PATH)
        self.direction = 3
        self.color = IDLE_COLOR
        self.coord_pos = [0, 0]
        self.passing_portal = True  # 先设置为True，防止刚出生就在Portal上
        self.god_mode = False
        self.god_mode_time = 0
        self.life = life
        self.data_error = False

    def update_angle(self):
        if self.direction == 0:
            self.angle = -90
        elif self.direction == 1:
            self.angle = -180
        elif self.direction == 2:
            self.angle = 90
        elif self.direction == 3:
            self.angle = 0

    def update_state(self):
        self.color = IDLE_COLOR
        if self.god_mode:
            self.color = GOD_MODE_COLOR
        if self.data_error:
            self.color = DATA_ERROR_COLOR

    def set_god_mode(self, active, time=0):
        self.god_mode = active
        self.god_mode_time = time

    def set_data_error(self, active):
        if self.life <= 0:
            return
        self.data_error = active
        self.color = DATA_ERROR_COLOR if active else IDLE_COLOR


