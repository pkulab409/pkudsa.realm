from testing_bot import action_less_bot, my_bot
from new_core import Core, GameException

if __name__ == "__main__":
    west_play = my_bot
    east_play = action_less_bot
    try:
        my_core = Core(west_play=west_play, east_play=east_play)
        my_core.run()
    except GameException as e:
        print('West' if e.side == 'W' else 'East' + ' wrong: ' + e.message,
              e.origin_exception if e.origin_exception else '')
    except BaseException as e:
        print('Core Error!', e)
