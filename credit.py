import arcade
import arcade.gl

SOUND_CREDIT = arcade.load_sound('assets/sound/credit.wav')
TEXTURE_CREDIT_PATH = 'assets/mob/credit.png'

SCROLL_TIME = 140

FONT_NAME = 'The Impostor'
FONT_NOTICE_NAME = 'Super Mario Bros. 2'


class CreditView(arcade.View):
    sprite_credit_list = None
    sprite_credit = arcade.Sprite(TEXTURE_CREDIT_PATH)
    timer = 0

    def __init__(self, window):
        super().__init__(window)
        self.sprite_credit_list = arcade.SpriteList()
        self.sprite_credit_list.append(self.sprite_credit)

    def on_draw(self):
        self.clear()
        self.sprite_credit_list.draw(filter=arcade.gl.NEAREST)

    def on_show_view(self):
        arcade.play_sound(SOUND_CREDIT)
        self.window.background_color = arcade.color.WHITE
        self.sprite_credit.center_x = self.window.width / 2
        self.sprite_credit.top = -150
        self.timer = 0

    def on_update(self, delta_time: float):
        h = self.sprite_credit.height
        self.timer += delta_time
        if self.timer < SCROLL_TIME:
            self.sprite_credit.top = -150 + (h + 250) * self.timer / SCROLL_TIME


class FailView(arcade.View):
    def __init__(self, window):
        super().__init__(window)

    def on_draw(self):
        arcade.set_background_color(arcade.color.BLACK)

        x = self.window.width / 2
        y = self.window.height / 2
        arcade.draw_text(text='You are not HIM.', font_name=FONT_NAME, font_size=20, color=arcade.color.WHITE,
                         start_x=x, start_y=y, anchor_x='center', anchor_y='center')
