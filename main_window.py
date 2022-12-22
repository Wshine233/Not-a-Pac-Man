import mapgen
import arcade
import game
import credit
import menu

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 920

FONT_PATH = 'assets/font/The Impostor.ttf'
FONT_NOTICE_PATH = 'assets/font/Super Mario Bros. 2.ttf'

arcade.load_font(FONT_PATH)
arcade.load_font(FONT_NOTICE_PATH)


class MainWindow(arcade.Window):
    game_view = None
    credit_view = None
    menu_view = None
    fail_view = None

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.game_view = game.GameView(self)
        self.credit_view = credit.CreditView(self)
        self.menu_view = menu.MenuView(self)
        self.fail_view = credit.FailView(self)

    def show_game_view(self):
        self.hide_view()
        view = self.game_view
        map_info = mapgen.generate_map(None, 18, 18)
        view.load_game(map_info, 18, 18)

        self.show_view(view)
        view.start_game()

    def show_credit(self):
        self.show_view(self.credit_view)

    def show_failed_view(self):
        self.show_view(self.fail_view)

    def show_menu(self):
        self.show_view(self.menu_view)


window = MainWindow(SCREEN_WIDTH, SCREEN_HEIGHT, 'Not a Pac-Man')
window.show_menu()

arcade.run()
