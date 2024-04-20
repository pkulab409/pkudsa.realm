"""
下面的四个类是bot允许查看的类：ChessType, Chess, Board, Action
其中Board类不允许直接调用
还有一些实用函数

为了避免一方直接篡改该文件的内容，应需要将该文件复制一份分别供两方使用  # important
"""
import copy
from collections import namedtuple
from enum import Enum

chess_number: int = 3  # 暂时不许更改

board_size: int = 8
max_turn_number: int = 60
max_spend_time: float = 0.1  # 最多耗时0.1秒

safe_area = frozenset({(4, 4), (3, 3), (3, 4), (4, 3)})
safe_area_add_for_chess: int = 50
safe_area_add_for_home: int = 20

home_initial_hp: int = 2000  # 初始基地生命值


class ChessType(Enum):
    """
    棋子枚举类
    """
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
                     moving_set=frozenset({(0, 1), (-1, 0), (0, 0), (1, 0), (0, -1)}),
                     atk_set=frozenset(
                         {(0, 1), (2, -1), (1, 2), (2, 1), (0, -2), (-2, 0), (-1, 0), (0, 2), (1, 0),
                          (-2, -1), (-1, -1), (-1, -2), (-2, 1), (-1, 1), (1, 1), (2, 0), (1, -2), (1, -1),
                          (-1, 2), (0, -1)}))
_infantry = _ChessData(name=ChessType.Infantry, hp_limit=1800, atk=200,
                       moving_set=frozenset({(0, 1), (-1, 0), (0, 0), (1, 0), (0, -1)}),
                       atk_set=frozenset({(0, 1), (1, 0), (-1, 0), (0, -1)}))
_home = _ChessData(name=ChessType.Home, hp_limit=float('inf'), atk=0, moving_set=frozenset(), atk_set=frozenset())


def get_chess_datas(*, use_dict: bool = False) -> list | dict:
    """
    调用此函数来获得三个兵种的属性数据（生命上限、攻击力、移动范围、攻击范围）

    返回的数据是一个列表（或可以改为字典），依次是各个兵种对应的_ChessData类，只可用于调用静态的属性数据
    use_dict设为True时返回的是字典数据，采用这种方式返回还会附带一个_home数据（也是_ChessData类）
    """
    if not use_dict:
        return [_cavalry, _bowman, _infantry]
    else:
        return {ChessType.Cavalry: _cavalry, ChessType.Bowman: _bowman, ChessType.Infantry: _infantry,
                ChessType.Home: _home}


class Chess:
    """
    返回给玩家的layout中数据的类型
    """

    def __init__(self, *, name: ChessType, hp: int, side: str):
        self.name: ChessType = name  # 棋子类型
        self.hp: int = hp  # 剩余生命
        self.side: side = side  # 哪一方


Action = namedtuple("Action", "op dx dy")


class Board:
    def __init__(self, *, turn_number, layout, side, total_turn, spend_time):
        self.layout: list[list[Chess | None]] = layout  # 棋盘8*8嵌套列表
        self.my_side: str = side  # W方，或者"E"为E方
        self.my_storage: any = None  # 跨turn存储
        self.total_turn: int = total_turn  # 总轮数
        self.turn_number: int = turn_number  # 当前轮次序号，首轮为0
        self.action_history: list[list[Action | None]] = []  # 行动历史，下标为轮次，值为list_action
        self.spend_time: dict = spend_time  # 双方总耗时


"""
##################### 下面开始是实用函数。注意一些函数是只依赖于layout（或其他数据）的，所以不放在Board类之中 #####################
"""


def calculate_real_atk(one: ChessType, other: ChessType) -> int:
    # 计算经过加成后的真实攻击数据
    datas = get_chess_datas(use_dict=True)
    first = datas[one]
    if one == ChessType.Bowman and other == ChessType.Infantry:
        return first.atk * 2
    elif one == ChessType.Infantry and other == ChessType.Home:
        return first.atk * 3
    else:
        return first.atk


def is_terminal(layout, *, total_turn: int = None, turn_number: int = None) -> bool:
    """
    判断一个layout局面游戏是否已经结束，若结束返回True

    可选参数：total_turn, turn_number
    二者必须同时提供或不提供。这里total_turn需要提供总轮数，turn_number需要提供当前轮次数（还未移动棋子前）
    当turn_number大于等于total_turn时也视为结束，返回True
    （注意：最后一轮(turn_number==total_turn-1)不视为结束，该轮结束后(turn_number==total_turn)视为结束）
    """
    if total_turn:
        if turn_number >= total_turn:
            return True
    west_home = layout[0][0]
    east_home = layout[-1][-1]
    if west_home is None or east_home is None:
        return True
    elif west_home.hp > 0 and east_home.hp > 0:
        return False
    else:
        return True


def calculate_hp_sum(layout) -> dict:
    # 计算双方当前总血量
    west_hp, east_hp = 0, 0
    for i in range(len(layout)):
        for chess in layout[i]:
            if chess:
                if chess.side == 'W':
                    west_hp += chess.hp
                else:
                    east_hp += chess.hp
    return {'W': west_hp, 'E': east_hp}


def generate_legal_successors(layout, side: str) -> list[list[Action | None]]:
    """
    从当前棋局layout和side（哪一方）计算对每单个棋子允许的下一步
    返回一个长为3的数组，数据依次是各个棋子允许行动的列表
    需要注意的是：这不代表该轮次三次行动的可行范围，而是只代表对每个棋子的行动可行范围。因为有可能棋子同时行动会发生冲突
    所以原则上要调用三次该函数

    （注意Action(op='move',dx=0,dy=0)和None等效；已死亡棋子只允许行动None）
    如[[Action(op='move',dx=1,dy=1),None],[None],[Action(op='attack',dx=1,dy=0),None]
    """
    own_chess_pos = dict()
    all_pos = set()
    enemy_pos = set()
    for i in range(board_size):
        for j in range(board_size):
            chess = layout[i][j]
            if chess:
                if chess.side == side:
                    own_chess_pos[chess.name] = (i, j)
                else:
                    enemy_pos.add((i, j))
                all_pos.add((i, j))
    datas = get_chess_datas(use_dict=True)
    results = [[None] for _ in range(chess_number)]
    for chess_name, (x, y) in own_chess_pos.items():
        if chess_name == ChessType.Home:
            continue
        actions = [None]
        chess_data = datas[chess_name]
        for u, v in chess_data.moving_set:
            new_x, new_y = x + u, y + v
            if 0 <= new_x < board_size and 0 <= new_y < board_size and ((new_x, new_y) not in all_pos):
                actions.append(Action(op='move', dx=u, dy=v))
        for u, v in chess_data.atk_set:
            atk_x, atk_y = x + u, y + v
            if (atk_x, atk_y) in enemy_pos:
                actions.append(Action(op='attack', dx=u, dy=v))
        results[chess_name.value] = actions
    return results


def do_in_turn_action(layout, side: str, *, name: ChessType, action: Action | None, use_copy: bool = False) -> list[
    list[Chess | None]]:
    """
    对单个行动计算行动后的layout
    需提供当前局面layout 哪一方side 行动棋子类型name 行动action
    原则上调用三次该函数才能计算出一个轮次结束后的棋局。请在调用三次完成之后务必调用do_after_turn来结算
    （应该注意turn中途血量小于0的棋子不会立即死亡）

    该函数不会彻底检验action是否合法，若不合法可能会导致输出的layout是奇怪的
    该函数是直接对layout以及其中的Chess类进行操作，若不希望这一点请将use_copy设为True
    """
    assert name.value in (0, 1, 2)
    if use_copy:
        layout = copy.deepcopy(layout)
    if action is None or action == Action(op='move', dx=0, dy=0):
        return layout
    for i in range(board_size):
        for j in range(board_size):
            chess = layout[i][j]
            if chess and chess.name == name and chess.side == side:
                if action.op == 'move':
                    layout[i + action.dx][j + action.dy], layout[i][j] = chess, None
                elif action.op == 'attack':
                    atk_chess = layout[i + action.dx][j + action.dy]
                    atk_chess.hp -= calculate_real_atk(name, atk_chess.name)
                else:
                    raise Exception('Illegal action!')
                return layout
    raise Exception('No such chess!')


def do_after_turn(layout, *, use_copy: bool = False) -> list[list[Chess | None]]:
    """
    一个轮次结束之后结算turn。给士兵、基地回血并让血量小于等于0的士兵死亡

    该函数是直接对layout以及其中的Chess类进行操作，若不希望这一点请将use_copy设为True
    """
    if use_copy:
        layout = copy.deepcopy(layout)
    datas = get_chess_datas(use_dict=True)
    for i in range(board_size):
        for j in range(board_size):
            if i == j == 0 or i == j == board_size - 1:
                continue
            chess = layout[i][j]
            if chess is not None:
                if (i, j) in safe_area:
                    # 自身加血
                    chess.hp += safe_area_add_for_chess
                    chess.hp = min(chess.hp, datas[chess.name].hp_limit)
                    # 基地加血
                    if chess.side == 'W':
                        layout[0][0].hp += safe_area_add_for_home
                    else:
                        layout[board_size - 1][board_size - 1].hp += safe_area_add_for_home
                if chess.hp <= 0:
                    chess.hp = 0
                    layout[i][j] = None
    return layout
