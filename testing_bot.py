"""
下面的函数是用于测试的函数
"""
from for_bot import *


def action_less_bot(board):
    return [None, None, None]


def my_bot(board):
    if board.turn_number <= 10:
        return [Action('move', 0, 1), None, None]
    elif board.turn_number <= 20:
        return [Action('move', 1, 0), None, None]
    else:
        if board.layout[6][7]:
            return [Action('attack', 1, 0), None, None]
        else:
            return [Action('move', 1, 0), None, None]
