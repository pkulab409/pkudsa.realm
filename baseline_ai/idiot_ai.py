import realm
import random

def get_all_actions(layout, side):
    # 辅助函数，用于给出所有可行行动
    list_actions = [None]
    for id_ in [realm.ChessType.WARRIOR, realm.ChessType.ARCHER, realm.ChessType.PROTECTOR]: #死亡？
        list_actions.extend(realm.get_valid_actions(layout, side, id_)[1:])
    return list_actions

@realm.api_decorator
def update(board):
    my_side = board.my_side
    return random.choice(get_all_actions(board.layout, my_side))
