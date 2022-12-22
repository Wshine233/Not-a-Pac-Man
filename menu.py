import arcade.gui

WARN_TEXT = """The game contains light horror 
elements, disturbing sound effects
and rapid flashes of color. 
Please ensure your own safety 
before playing.

DO NOT wear headphones for the best experience."""
START_TEXT = """Press 'Z' To Start

 'NOT  A  PAC-MAN' """

FONT_NAME = 'The Impostor'
FONT_NOTICE_NAME = 'Super Mario Bros. 2'


class MenuView(arcade.View):
    gui = None
    start_label = None
    timer = 0

    def __init__(self, window):
        super().__init__(window)
        self.v_box = None
        self.gui = arcade.gui.UIManager(window)

    def on_show_view(self):
        self.set_ui()
        self.timer = 0

    def set_ui(self):
        # UI里的文字无法调整居中对齐就离谱
        self.gui.enable()
        arcade.set_background_color(arcade.color.WHITE)

        self.v_box = arcade.gui.UIBoxLayout()
        label = arcade.gui.UITextArea(text=WARN_TEXT, text_color=arcade.color.BLACK,
                                      width=1000, height=400,
                                      font_size=24, font_name=FONT_NOTICE_NAME)
        self.v_box.add(label.with_space_around(0, 0, 100, 0))

        self.start_label = arcade.gui.UITextArea(text=START_TEXT, text_color=arcade.color.GRAY,
                                                 width=320, height=100,
                                                 font_size=18, font_name=FONT_NAME)
        self.v_box.add(self.start_label.with_space_around(0, 0, 0, 0))

        self.gui.add(
            arcade.gui.UIAnchorWidget(
                anchor_x='center_x',
                anchor_y='center_y',
                child=self.v_box
            )
        )

    def on_draw(self):
        self.clear()
        self.gui.draw()

        if self.timer % 1.9 > 1.2:
            arcade.draw_lrtb_rectangle_filled(0, self.window.width - 1, 400, 0, arcade.color.WHITE)

    def on_update(self, delta_time: float):
        self.timer += delta_time

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.Z:
            self.window.show_game_view()
