"""
下面的四个类是bot允许调用的类：ChessType, Chess, Board, Action
"""
from collections import namedtuple
from enum import Enum


class ChessType(Enum):
    Cavalry = 0
    Bowman = 1
    Infantry = 2
    Home = -1


class Chess:
    def __init__(self, *, name, hp, side):
        self.name = name  # 棋子类型
        self.hp = hp  # 剩余生命
        self.side = side  # 哪一方


class Board:
    def __init__(self, *, turn_number, layout, side, total_turn):
        self.layout = layout  # 棋盘8*8嵌套列表
        self.my_side = side  # W方，或者"E"为E方
        self.my_storage = None  # 跨turn存储
        self.total_turn = total_turn  # 总轮数
        self.turn_number = turn_number  # 当前轮次序号，首轮为0
        self.action_history = []  # 行动历史，下标为轮次，值为list_action


Action = namedtuple("Action", "op dx dy")
