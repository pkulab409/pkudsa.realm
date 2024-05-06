import realm
import random


@realm.api_decorator
def update(board):
    return random.choice(realm.get_valid_actions(board.layout, board.my_side))
