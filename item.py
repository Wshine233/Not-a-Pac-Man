import arcade

COIN_PATH = 'assets/item/coin.png'

PORTAL_PATH = 'assets/item/portal.png'
PORTAL_COLOR = ['#557fff', '#2adfaa', '#800080', '#7f3fff']


class Item(arcade.Sprite):
    coord_pos = None

    def __init__(self, path, pos, scale, coord_pos):
        super().__init__(path)
        self.position = pos
        self.scale = scale
        self.coord_pos = coord_pos


class Coin(Item):
    def __init__(self, pos, scale, coord_pos):
        super().__init__(COIN_PATH, pos, scale, coord_pos)


class Portal(Item):
    def __init__(self, pos, scale, coord_pos, pid):
        super().__init__(PORTAL_PATH, pos, scale, coord_pos)
        self.color = arcade.color_from_hex_string(PORTAL_COLOR[pid])
