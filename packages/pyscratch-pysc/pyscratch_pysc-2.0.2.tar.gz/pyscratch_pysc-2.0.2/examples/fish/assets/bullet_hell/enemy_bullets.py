import pyscratch as pysc
import random
from setting import *
import numpy as np



def create_bullet_attracted(position):
    bullet = pysc.Sprite(frames, "spin", position)
    
    bullet.set_scale(2.3)
    #pysc.game.add_sprite(bullet)
    speed = random.random()*15+5

    bullet.point_towards_sprite(pysc.game.shared_data['player'])


    movement_event = pysc.game.when_timer_reset(20).add_handler(lambda x: bullet.move_indir(speed))
    following_event = pysc.game.when_timer_reset(200, 5).add_handler(lambda x: bullet.point_towards_sprite(pysc.game.shared_data['player']))

    frame_event = pysc.game.when_timer_reset(200).add_handler(lambda x: bullet.next_frame())
    hitting_player_event = pysc.game._create_specific_collision_trigger(bullet, pysc.game.shared_data['player'])

    
    def explode_and_destroy(a):
        bullet.set_animation('star_explosion')
        pysc.game.broadcast_message('player_health', -1)
        movement_event.remove()
        pysc.game.when_timer_reset(200, 1).add_handler(destory)


    def destory(x):
        movement_event.remove()
        frame_event.remove()
        following_event.remove()
        hitting_player_event.remove()
        pysc.game._remove_sprite(bullet)

    when_exit_screen = pysc.game.when_condition_met(lambda: bullet.y > SCREEN_HEIGHT, repeats=1)
    when_exit_screen.add_handler(destory)
    hitting_player_event.add_handler(explode_and_destroy)



def create_bullet_start_pointing(position, _):

    bullet = pysc.Sprite(frames, "spin", position)

    

    bullet.point_towards_sprite(pysc.game.shared_data['player'])
    bullet.set_scale(2.3)
    #pysc.game.add_sprite(bullet)
    speed = random.random()*15+5
    bullet.point_towards_sprite(pysc.game.shared_data['player'])


    movement_event = bullet.when_timer_reset(20).add_handler(lambda x: bullet.move_indir(speed))
    #movement_event = pysc.game.create_timer_trigger(20).on_reset(lambda x: bullet.move_across_dir((random.random()-0.5)*speed*0.3))


    frame_event = bullet.when_timer_reset(200).add_handler(lambda x: bullet.next_frame())
    hitting_player_event = pysc.game._create_specific_collision_trigger(bullet, pysc.game.shared_data['player'])

    
    def explode_and_destroy(a):
        bullet.set_animation('star_explosion')
        pysc.game.broadcast_message('player_health', -1)
        movement_event.remove()
        pysc.game.when_timer_reset(200, 1).add_handler(destory)


    def destory(x):
        movement_event.remove()
        frame_event.remove()
        hitting_player_event.remove()
        pysc.game._remove_sprite(bullet)

    when_exit_screen = pysc.game.when_condition_met(lambda: bullet.y > SCREEN_HEIGHT, repeats=1)
    when_exit_screen.add_handler(destory)
    hitting_player_event.add_handler(explode_and_destroy)
    pass




def create_bullet_move_sine(position, rotation):
    bullet = pysc.Sprite(frames, "square_bullets", position)
    bullet.set_scale(2.3)
    #pysc.game.add_sprite(bullet)
    bullet.set_rotation(rotation+90)
    #speed = random.random()*15+5
    speed = 10


    bullet.sprite_data['phase'] = 0
    movement_event = pysc.game.when_timer_reset(30)
    def move(x):
        bullet.sprite_data['phase']+=.1
        angle = np.tanh(np.cos(.6*bullet.sprite_data['phase']))


        bullet.add_rotation(angle)
                            
        bullet.move_indir(speed)

    
    movement_event.add_handler(move)


    frame_event = pysc.game.when_timer_reset(200).add_handler(lambda x: bullet.next_frame())
    hitting_player_event = pysc.game._create_specific_collision_trigger(bullet, pysc.game.shared_data['player'])

    
    def explode_and_destroy(a):
        bullet.set_animation('star_explosion')
        pysc.game.broadcast_message('player_health', -1)
        movement_event.remove()
        pysc.game.when_timer_reset(200, 1).add_handler(destory)


    def destory(x):
        movement_event.remove()
        frame_event.remove()
        hitting_player_event.remove()
        pysc.game._remove_sprite(bullet)

    when_exit_screen = pysc.game.when_condition_met(lambda: (bullet.y > SCREEN_HEIGHT) or (bullet.y < 0) or (bullet.x <0) or (bullet.x>SCREEN_WIDTH) , repeats=1)
    when_exit_screen.add_handler(destory)
    hitting_player_event.add_handler(explode_and_destroy)





def create_straight_bullet(position, rotation):
    """
    a bullet that moves a straight line
    """
    
    bullet = pysc.Sprite(frames, "spin", position)
    bullet.add_rotation(rotation)
    bullet.set_scale(2.3)
    #pysc.game.add_sprite(bullet)
    speed = random.random()*15+5
    #speed = 15

    movement_event = bullet.when_timer_reset(20).add_handler(lambda x: bullet.move_indir(speed))
    frame_event = bullet.when_timer_reset(200).add_handler(lambda x: bullet.next_frame())
    hitting_player_event = bullet.create_specific_collision_trigger(pysc.game.shared_data['player'])
    when_exit_screen = bullet.when_condition_met(lambda: (bullet.y > SCREEN_HEIGHT) or (bullet.y < 0) or (bullet.x <0) or (bullet.x>SCREEN_WIDTH), repeats=1,)

    
    def explode_and_destroy(a):
        bullet.set_animation('star_explosion')
        pysc.game.broadcast_message('player_health', -1)
        movement_event.remove()
        pysc.game.when_timer_reset(200, 1).add_handler(destory)


    def destory(x):
        #movement_event.remove()
        #frame_event.remove()
        #hitting_player_event.remove()
        #when_exit_screen.remove()
        pysc.game._remove_sprite(bullet)

    when_exit_screen.add_handler(destory)
    hitting_player_event.add_handler(explode_and_destroy)





def create_exploding_bullet(position, rotation):
    """
    a bullet that explode after 1.2 second
    """

    bullet = pysc.Sprite(frames, "spin", position)
    bullet.add_rotation(rotation)
    bullet.set_scale(2.3)
    #pysc.game.add_sprite(bullet)

    speed = 7

    movement_event = pysc.game.when_timer_reset(20, associated_sprites=[bullet]).add_handler(lambda x: bullet.move_indir(speed))
    frame_event = pysc.game.when_timer_reset(200, associated_sprites=[bullet]).add_handler(lambda x: bullet.next_frame())
    hitting_player_event = pysc.game._create_specific_collision_trigger(bullet, pysc.game.shared_data['player'])
    exit_screen_event = pysc.game.when_condition_met(lambda: bullet.y > SCREEN_HEIGHT, repeats=1, associated_sprites=[bullet])
    explosion_event = pysc.game.when_timer_reset(1200,1, associated_sprites=[bullet])
        


    def hit_and_destroy(a):
        bullet.set_animation('star_explosion')
        movement_event.remove()
        pysc.game.when_timer_reset(200, 1).add_handler(destory)

    def spawn_sub_bullets(_):
        for i in range(12):
            create_straight_bullet(bullet._body.position, rotation=i*30)

    def delayed_spawn_sub_bullets(_):
        pysc.game.when_timer_reset(200, 1).add_handler(spawn_sub_bullets)

            
    def destory(x):
        

        #movement_event.remove()
        #frame_event.remove()
        #hitting_player_event.remove()
        #exit_screen_event.remove()
        #explosion_event.remove()
        pysc.game._remove_sprite(bullet)

    exit_screen_event.add_handler(destory)
    hitting_player_event.add_handler(hit_and_destroy)
    hitting_player_event.add_handler(lambda: pysc.game.broadcast_message('player_health', -1))
    explosion_event.add_handler(delayed_spawn_sub_bullets)
    explosion_event.add_handler(hit_and_destroy)




create_bullet_move_sine((355, 0), 90)



