# 目标为直接击杀司令
import realm


def get_all_actions(layout, side):
    # 辅助函数，用于给出所有可行行动
    list_actions = [None]
    for id_ in [realm.ChessType.WARRIOR, realm.ChessType.ARCHER, realm.ChessType.PROTECTOR]:
        list_actions.extend(realm.get_valid_actions(layout, side, id_)[1:])
    return list_actions


@realm.api_decorator
def update(board):
    my_side = board.my_side
    list_actions = get_all_actions(board.layout, my_side)
    if len(list_actions) == 1:
        return None
    list_actions.remove(None)
    enemy_side = 'E' if my_side == 'W' else 'W'

    def valuation_func(action):
        delta_points = realm.make_turn(board.layout, my_side, action)[1]
        my_delta_points, enemy_delta_points = delta_points[my_side], delta_points[enemy_side]
        return (my_delta_points[0] - enemy_delta_points[0], my_delta_points[1] - enemy_delta_points[1])

    return max(list_actions, key=valuation_func)
