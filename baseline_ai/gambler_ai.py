# 此文件版权归pkulab409/dsa2024dev全体技术组同学所有
# The copyright of this file belongs to all technical team members of pkulab409/dsa2024dev
# https://github.com/orgs/pkulab409/teams/dsa2024dev
#
# 此文件归属于项目pkudsa.realm
# This file belongs to the project pkudsa.realm
# https://github.com/pkulab409/pkudsa.realm
#
# 特别感谢CrystalZZZZZZZZ和zhes2Hen在编写上做出的贡献
import realm


@realm.api_decorator
def update(board):
    my_side = board.my_side
    list_actions = realm.get_valid_actions(board.layout, my_side)
    enemy_side = 'E' if my_side == 'W' else 'W'

    def valuation_func(action):
        delta_points = realm.make_turn(board.layout, my_side, action, calculate_points='hard')[1]
        my_delta_points, enemy_delta_points = delta_points[my_side], delta_points[enemy_side]
        return (my_delta_points[0] - enemy_delta_points[0], my_delta_points[1] - enemy_delta_points[1])

    return max(list_actions, key=valuation_func)
