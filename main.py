from testing_bot import west_play, east_play
from new_core import Core, GameException

if __name__ == "__main__":
    try:
        my_core = Core(west_play=west_play, east_play=east_play)
        my_core.run()
    except GameException as e:
        print(f'Turn: {e.turn}')
        print(('West' if e.side == 'W' else 'East') + ' wrong: ' + e.message,
              e.origin_exception if e.origin_exception else '')
    except BaseException as e:
        print('Core Error!', e)
