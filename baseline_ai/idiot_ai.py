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
import random


@realm.api_decorator
def update(board):
    return random.choice(realm.get_valid_actions(board.layout, board.my_side))
