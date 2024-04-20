"""
下面的四个类是bot允许调用的类：ChessType, Chess, Board, Action
以及可以获得游戏数据的函数get_chess_datas
"""
from collections import namedtuple
from enum import Enum


class ChessType(Enum):
    Cavalry = 0
    Bowman = 1
    Infantry = 2
    Home = -1


_ChessData = namedtuple('_ChessData', 'name hp_limit atk moving_set atk_set')
_cavalry = _ChessData(name=ChessType.Cavalry, hp_limit=800, atk=400,
                      moving_set=frozenset(
                          {(0, 1), (-1, -1), (0, 0), (-1, 1), (1, 1), (2, 0), (1, -1), (0, -1), (-2, 0),
                           (-1, 0), (0, 2), (1, 0),
                           (0, -2)}), atk_set=frozenset({(0, 1), (1, 0), (-1, 0), (0, -1)}))
_bowman = _ChessData(name=ChessType.Bowman, hp_limit=300, atk=500,
                     moving_set=frozenset({(0, 1), (1, 0), (-1, 0), (0, -1)}),
                     atk_set=frozenset(
                         {(0, 1), (2, -1), (1, 2), (2, 1), (0, -2), (-2, 0), (-1, 0), (0, 2), (1, 0),
                          (-2, -1), (-1, -1), (-1, -2), (-2, 1), (-1, 1), (1, 1), (2, 0), (1, -2), (1, -1),
                          (-1, 2), (0, -1)}))
_infantry = _ChessData(name=ChessType.Infantry, hp_limit=1800, atk=200,
                       moving_set=frozenset({(0, 1), (1, 0), (-1, 0), (0, -1)}),
                       atk_set=frozenset({(0, 1), (1, 0), (-1, 0), (0, -1)}))


def get_chess_datas(*, use_dict=False) -> list | dict:
    """
    use_dict设为True时返回的是字典数据
    """
    if not use_dict:
        return [_cavalry, _bowman, _infantry]
    else:
        return {ChessType.Cavalry: _cavalry, ChessType.Bowman: _bowman, ChessType.Infantry: _infantry}


class Chess:
    def __init__(self, *, name, hp, side):
        self.name = name  # 棋子类型
        self.hp = hp  # 剩余生命
        self.side = side  # 哪一方


class Board:
    def __init__(self, *, turn_number, layout, side, total_turn, spend_time):
        self.layout = layout  # 棋盘8*8嵌套列表
        self.my_side = side  # W方，或者"E"为E方
        self.my_storage = None  # 跨turn存储
        self.total_turn = total_turn  # 总轮数
        self.turn_number = turn_number  # 当前轮次序号，首轮为0
        self.action_history = []  # 行动历史，下标为轮次，值为list_action
        self.spend_time = spend_time  # 双方总耗时


Action = namedtuple("Action", "op dx dy")
