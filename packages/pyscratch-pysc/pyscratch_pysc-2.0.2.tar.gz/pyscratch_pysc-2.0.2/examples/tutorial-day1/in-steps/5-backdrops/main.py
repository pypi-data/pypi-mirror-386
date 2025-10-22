import pyscratch as pysc
from pyscratch import game
import chest, enemy, friend
       
# background
bg0 = pysc.load_image("assets/undersea_bg.png")
bg0 = pysc.scale_to_fit_aspect(bg0, (1024, 576))
game.add_backdrop('sea', bg0)

bg1 = pysc.load_image("assets/Cat In Space Wallpaper Hq.jpg")
bg1 = pysc.scale_to_fit_aspect(bg1, (1024, 576))
game.add_backdrop('lose', bg1)


game.switch_backdrop('sea')



def background():
    while True:
        yield 1/game.framerate
        if game['score'] < 0: 
            game.switch_backdrop('lose')
game.when_game_start().add_handler(background)


# starting the game
game.update_screen_mode((1024, 576))
game.start(show_mouse_position=True)


