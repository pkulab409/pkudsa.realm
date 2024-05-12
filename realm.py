# 此文件版权归pkulab409/dsa2024dev全体技术组同学所有
# The copyright of this file belongs to all technical team members of pkulab409/dsa2024dev
# https://github.com/orgs/pkulab409/teams/dsa2024dev
#
# 此文件归属于项目pkudsa.realm
# This file belongs to the project pkudsa.realm
# https://github.com/pkulab409/pkudsa.realm
#
# 特别感谢zhes2Hen和Renko6626在编写上做出的贡献
import api
from enum import Enum
from collections import namedtuple
from typing import Optional, TypedDict, Generator


class ChessType(Enum):
    COMMANDER = 0
    WARRIOR = 1
    ARCHER = 3
    PROTECTOR = 2


class Final(Enum):
    WIN = 0
    COMMANDER_DEAD = 1
    LESS_POINT = 2
    NONE = 3
    OTHER = 4


_all_players_storage: dict[int, dict] = {}
_action_history: list[Optional['Action']] = []

_tencent_id: dict[int, ChessType] = {100: ChessType.COMMANDER, 101: ChessType.ARCHER, 102: ChessType.PROTECTOR,
                                     103: ChessType.WARRIOR}
_game_id: dict[ChessType, int] = {ChessType.COMMANDER: 100, ChessType.ARCHER: 101, ChessType.PROTECTOR: 102,
                                  ChessType.WARRIOR: 103}

_chess_to_int: dict[tuple[str, ChessType], int] = {(i, j): (4 * (i == 'E') + j.value) for i in 'WE' for j in ChessType}
_int_to_chess: dict[int, tuple[str, ChessType]] = {value: key for key, value in _chess_to_int.items()}


class LayoutDetails(TypedDict):  # 仅用于标注
    side: str
    chess_id: ChessType
    hp: int
    pos: tuple[int, int]


class Layout:
    def __init__(self, pos_to_chess: dict[int, int], chess_details: list[Optional[tuple[int, int]]]):
        self.pos_to_chess: dict[int, int] = pos_to_chess  # 从int_pos到int_chess_id
        self.chess_details: list[Optional[tuple[int, int]]] = chess_details  # 从int_chess_id到int_pos,hp

    def set_chess_new_pos(self, int_chess_id: int, new_int_pos: Optional[int]):
        old_pos, hp = self.chess_details[int_chess_id]
        if new_int_pos is None:
            self.chess_details[int_chess_id] = None
            self.pos_to_chess.pop(old_pos)
        elif old_pos != new_int_pos:
            self.pos_to_chess.pop(old_pos)
            self.pos_to_chess[new_int_pos] = int_chess_id
            self.chess_details[int_chess_id] = (new_int_pos, hp)

    def set_hp(self, int_chess_id: int, hp: int, *, hp_addition: bool = False):
        pos, old_hp = self.chess_details[int_chess_id]
        if hp_addition:
            self.chess_details[int_chess_id] = (pos, old_hp + hp)
        else:
            self.chess_details[int_chess_id] = (pos, hp)

    def copy(self) -> 'Layout':
        return Layout(self.pos_to_chess.copy(), self.chess_details.copy())

    def details(self) -> Generator[LayoutDetails, None, None]:
        for int_chess_id, chess in enumerate(self.chess_details):
            if chess is None:
                continue
            int_pos, hp = chess
            side, chess_id = _int_to_chess[int_chess_id]
            yield {'side': side, 'chess_id': chess_id, 'hp': hp, 'pos': (int_pos // 8, int_pos % 8)}


Action = namedtuple("Action", "chess_id mdr mdc adr adc")


class Board:
    def __init__(self, context, storage: dict, action_history: list[Optional[Action]]):

        self.turn_number: int = context.round - 1
        if self.turn_number % 2 == 0:
            self.my_side: str = "W"
            enemy_side = "E"
        else:
            self.my_side: str = "E"
            enemy_side = "W"

        # 生成layout和血量
        my_hp_sum, enemy_hp_sum = 0, 0
        my_bots, enemy_bots = context.me.get_bots(), context.enemy.get_bots()
        pos_to_chess: dict[int, int] = {}
        chess_details: list[Optional[tuple[int, int]]] = [None for _ in range(8)]
        for bot in my_bots:
            int_pos = 8 * bot.row + bot.col
            hp = bot.hp
            int_chess_id = _chess_to_int[self.my_side, _tencent_id[bot.type_id]]
            pos_to_chess[int_pos] = int_chess_id
            chess_details[int_chess_id] = (int_pos, hp)
            my_hp_sum += bot.hp
        for bot in enemy_bots:
            int_pos = 8 * bot.row + bot.col
            hp = bot.hp
            int_chess_id = _chess_to_int[enemy_side, _tencent_id[bot.type_id]]
            pos_to_chess[int_pos] = int_chess_id
            chess_details[int_chess_id] = (int_pos, hp)
            enemy_hp_sum += bot.hp
        self.layout: Layout = Layout(pos_to_chess, chess_details)

        self.point: dict[str, tuple[int, int]] = {
            self.my_side: (context.me.get_bots(name=100)[0].hp, my_hp_sum),
            enemy_side: (context.enemy.get_bots(name=100)[0].hp, enemy_hp_sum)
        }
        self.chess_profile: dict[ChessType, tuple[int, int]] = {ChessType.COMMANDER: (0, 1600),
                                                                ChessType.WARRIOR: (200, 1000),
                                                                ChessType.ARCHER: (250, 700),
                                                                ChessType.PROTECTOR: (150, 1400)}
        self.regain: tuple[int, int] = (25, 25)
        self.my_storage: dict = storage
        self.total_turn: int = 100
        self.action_history: list[Optional[Action]] = action_history


def api_decorator(func):
    def wrapper(context):
        global _action_history
        global _all_players_storage
        my_id = context.me.id
        if my_id not in _all_players_storage:
            _all_players_storage[my_id] = {}
        if context.round > 1:
            enemy_actions_list = api.get.enemy_last_round_ops()
            if enemy_actions_list:
                enemy_action = enemy_actions_list[0]
                enemy_id = _tencent_id[enemy_action.bot.type_id]
                if enemy_action.attack:
                    enemy_atk_r = enemy_action.attack[0]
                    enemy_atk_c = enemy_action.attack[1]
                else:
                    enemy_atk_r, enemy_atk_c = 0, 0
                if enemy_action.move:
                    enemy_move_r = enemy_action.move[0]
                    enemy_move_c = enemy_action.move[1]
                else:
                    enemy_move_r, enemy_move_c = 0, 0
                if enemy_atk_r == enemy_atk_c == enemy_move_r == enemy_move_c == 0:
                    last_action = None
                else:
                    last_action = Action(enemy_id, enemy_move_r, enemy_move_c, enemy_atk_r, enemy_atk_c)
            else:
                last_action = None
            _action_history.append(last_action)
        board = Board(context, _all_players_storage[my_id], _action_history.copy())
        original_layout = board.layout.copy()
        original_my_side_mask = _chess_to_int[board.my_side, ChessType.COMMANDER] >= 4
        # 运行玩家函数
        result: Optional[Action] = func(board)
        if result is not None and not isinstance(result, Action):
            raise ValueError("Wrong Action Format")
        # 执行回合动作
        _all_players_storage[my_id] = board.my_storage

        if result:
            profile = get_chess_profile(result.chess_id)
            if result.chess_id not in [ChessType.WARRIOR, ChessType.ARCHER, ChessType.PROTECTOR]:
                raise ValueError("Not a Controllable Object")
            if not (isinstance(result.mdr, int) and isinstance(result.mdc, int)
                    and isinstance(result.adr, int) and isinstance(result.adc, int)):
                raise ValueError("Wrong Action Format")
            if abs(result.mdr) + abs(result.mdc) > profile['move_range']:
                raise ValueError("Move Out of Range")
            if result.adr and result.adc and (result.adr, result.adc) not in profile['atk_pos']:
                raise ValueError("Attack Out of Range")
            bot_list = context.me.get_bots(name=_game_id[result.chess_id])
            if not bot_list:
                raise ValueError("Chess not alive")
            bot = bot_list[0]
            row, col = bot.row, bot.col
            new_r, new_c = row + result.mdr, col + result.mdc
            if not (0 <= new_r < 8 and 0 <= new_c < 8):
                raise ValueError("Move Out of Game Map")
            if (result.mdr or result.mdc) and original_layout.pos_to_chess.get(8 * new_r + new_c) is not None:
                raise ValueError("Move Blocked")

            bot.move_to((row + result.mdr, col + result.mdc))

            if result.adr or result.adc:
                atk_r = row + result.mdr + result.adr
                atk_c = col + result.mdc + result.adc
                if not (0 <= atk_r < 8 and 0 <= atk_c < 8):
                    raise ValueError("Bot Attack Out of Game Map")
                enemy_chess = original_layout.pos_to_chess.get(8 * atk_r + atk_c)
                if enemy_chess is None or (enemy_chess >= 4) == original_my_side_mask:
                    raise ValueError("Attack Wrong Target")

                bot.attack((atk_r, atk_c))

        _action_history.append(result)

    return wrapper


def valid_action(layout: Layout, side: str, action: Optional[Action]) -> bool:
    # 基于棋盘布局和指定对战方，判断行动是否有效 返回一个bool变量
    if action is None:
        return True
    if action.chess_id not in [ChessType.WARRIOR, ChessType.ARCHER, ChessType.PROTECTOR]:
        return False
    data = get_chess_profile(action.chess_id)
    if (action.adr and action.adc and (action.adr, action.adc) not in data['atk_pos']) or (
            abs(action.mdr) + abs(action.mdc) > data['move_range']):
        return False
    int_chess_id = _chess_to_int[side, action.chess_id]
    chess = layout.chess_details[int_chess_id]
    if chess is None:
        return False
    int_pos = chess[0]
    new_r, new_c = int_pos // 8 + action.mdr, int_pos % 8 + action.mdc
    if (new_r, new_c) not in _hidden_get_valid_move(layout, int_chess_id):
        return False
    if action.adr == action.adc == 0:
        return True
    atk_r, atk_c = new_r + action.adr, new_c + action.adc
    if not (0 <= atk_r < 8 and 0 <= atk_c < 8):
        return False
    target = layout.pos_to_chess.get(8 * atk_r + atk_c)
    if target is not None and (int_chess_id >= 4) != (target >= 4):
        return True
    else:
        return False


def get_chess_details(layout: Layout, side: str, chess_id: ChessType) -> Optional[LayoutDetails]:
    int_chess_id = _chess_to_int[side, chess_id]
    chess = layout.chess_details[int_chess_id]
    if chess is None:
        return None
    int_pos, hp = chess
    return {'side': side, 'chess_id': chess_id, 'hp': hp, 'pos': (int_pos // 8, int_pos % 8)}


def get_valid_chess_id(layout: Layout, side: str, *, include_commander: bool = True) -> list[ChessType]:
    id_range = [ChessType.COMMANDER, ChessType.ARCHER, ChessType.PROTECTOR,
                ChessType.WARRIOR] if include_commander else [ChessType.ARCHER, ChessType.PROTECTOR, ChessType.WARRIOR]
    ret = []
    for chess_id in id_range:
        if layout.chess_details[_chess_to_int[side, chess_id]] is not None:
            ret.append(chess_id)
    return ret


class ChessProfile(TypedDict):  # 仅用于标注
    atk: int
    atk_pos: list[tuple[int, int]]
    init_hp: int
    move_range: int


_commander_data = {'atk': 0, 'atk_pos': [], 'init_hp': 1600, 'move_range': 0}
_archer_data = {'atk': 250, 'atk_pos': [(-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -2), (0, -1), (0, 1), (0, 2), (1, -1),
                                        (1, 0), (1, 1), (2, 0)], 'init_hp': 700, 'move_range': 1}
_warrior_data = {'atk': 200, 'atk_pos': [(0, 1), (0, -1), (1, 0), (-1, 0)], 'init_hp': 1000, 'move_range': 2}
_protector_data = {'atk': 150, 'atk_pos': [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)],
                   'init_hp': 1400, 'move_range': 1}


def get_chess_profile(chess_id: ChessType) -> ChessProfile:
    if chess_id == ChessType.COMMANDER:
        return _commander_data
    elif chess_id == ChessType.ARCHER:
        return _archer_data
    elif chess_id == ChessType.WARRIOR:
        return _warrior_data
    elif chess_id == ChessType.PROTECTOR:
        return _protector_data


def _hidden_get_chess_profile(int_chess_id: int) -> ChessProfile:
    if (int_chess_id - ChessType.COMMANDER.value) % 4 == 0:
        return _commander_data
    elif (int_chess_id - ChessType.ARCHER.value) % 4 == 0:
        return _archer_data
    elif (int_chess_id - ChessType.WARRIOR.value) % 4 == 0:
        return _warrior_data
    elif (int_chess_id - ChessType.PROTECTOR.value) % 4 == 0:
        return _protector_data


def _hidden_get_valid_move(layout: Layout, int_chess_id: int) -> set[tuple[int, int]]:
    # 返回一个列表,每个元素是可移动位置(row,col)的二元组
    int_pos, _ = layout.chess_details[int_chess_id]
    pos_r, pos_c = int_pos // 8, int_pos % 8

    position_set: set[tuple[int, int]] = set()
    for delta_r, delta_c in [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]:
        new_r, new_c = pos_r + delta_r, pos_c + delta_c
        if delta_r == delta_c == 0:
            position_set.add((new_r, new_c))
        elif (0 <= new_r < 8 and 0 <= new_c < 8) and layout.pos_to_chess.get(8 * new_r + new_c) is None:
            position_set.add((new_r, new_c))

    if _hidden_get_chess_profile(int_chess_id)["move_range"] == 2:
        for delta_r, delta_c in [(-2, 0), (-1, -1), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 1), (2, 0)]:
            new_r, new_c = pos_r + delta_r, pos_c + delta_c
            if (0 <= new_r < 8 and 0 <= new_c < 8) and layout.pos_to_chess.get(8 * new_r + new_c) is None:
                if delta_r and delta_c:
                    # 针对1,1型路
                    if (pos_r + delta_r, pos_c) in position_set or (pos_r, pos_c + delta_c) in position_set:
                        position_set.add((new_r, new_c))
                else:
                    # 针对0,2型路
                    if (pos_r + delta_r // 2, pos_c + delta_c // 2) in position_set:
                        position_set.add((new_r, new_c))

    return position_set


def get_valid_move(layout: Layout, side: str, chess_id: ChessType) -> set[tuple[int, int]]:
    return _hidden_get_valid_move(layout, _chess_to_int[side, chess_id])


def get_valid_attack(layout: Layout, side: str, chess_id: ChessType) -> dict[ChessType, tuple[int, int]]:
    int_chess_id = _chess_to_int[side, chess_id]
    chess = layout.chess_details[int_chess_id]
    if chess is None:
        raise ValueError('Chess not alive!')
    int_pos = chess[0]
    old_r, old_c = int_pos // 8, int_pos % 8
    mask = int_chess_id >= 4
    atk_pos = _hidden_get_chess_profile(int_chess_id)['atk_pos']
    ret = {}
    for adr, adc in atk_pos:
        new_r, new_c = old_r + adr, old_c + adc
        if 0 <= new_r < 8 and 0 <= new_c < 8:
            target = layout.pos_to_chess.get(8 * new_r + new_c)
            if target is not None and mask != (target >= 4):
                ret[_int_to_chess[target][1]] = (new_r, new_c)
    return ret


def get_valid_actions(layout: Layout, side: str, *, chess_id: ChessType = None) -> \
        list[Optional[Action]]:
    # 基于棋局和指定行动方，返回列表,元素是某个棋子所有可能的行动Action
    if chess_id is None:
        list_actions = [None]
        for chess_id in [ChessType.WARRIOR, ChessType.ARCHER, ChessType.PROTECTOR]:
            list_actions.extend(
                _hidden_get_valid_actions(layout, _chess_to_int[side, chess_id], chess_id=chess_id)[1:])
        return list_actions
    else:
        return _hidden_get_valid_actions(layout, _chess_to_int[side, chess_id], chess_id=chess_id)


def _hidden_get_valid_actions(layout: Layout, int_chess_id: int, *, chess_id: ChessType) -> \
        list[Optional[Action]]:
    chess = layout.chess_details[int_chess_id]
    if chess is None:
        return [None]
    int_pos = chess[0]
    origin_r, origin_c = int_pos // 8, int_pos % 8
    mask: bool = int_chess_id >= 4

    result = [None]
    atk_pos = _hidden_get_chess_profile(int_chess_id)['atk_pos']
    for virtual_r, virtual_c in _hidden_get_valid_move(layout, int_chess_id):
        mdr, mdc = virtual_r - origin_r, virtual_c - origin_c
        if mdr or mdc:
            result.append(Action(chess_id, mdr, mdc, 0, 0))
        for atk_dr, atk_dc in atk_pos:
            t_r, t_c = virtual_r + atk_dr, virtual_c + atk_dc
            if 0 <= t_r < 8 and 0 <= t_c < 8:
                target_chess_id = layout.pos_to_chess.get(8 * t_r + t_c)
                if target_chess_id is not None and mask != (target_chess_id >= 4):
                    result.append(Action(chess_id, mdr, mdc, atk_dr, atk_dc))
    return result


def make_turn(layout: Layout, side: str, action: Optional[Action], *, turn_number: int = 0,
              calculate_points: str = 'soft') -> tuple[Layout, Optional[dict[str, tuple[int, int]]], dict[str, Final]]:
    # 基于棋盘布局和指定对战方，进行一个虚拟的轮次，返回结果布局，分数变化，胜利情况。默认提供的是有效行动
    assert calculate_points in ['none', 'soft', 'hard']
    original_points = calculate_scores(layout) if calculate_points == 'hard' else None
    virtual_layout = layout.copy()

    def blood_regen():
        # 回血
        nonlocal virtual_layout
        for pos_ in [27, 28, 35, 36]:
            current_chess_id = virtual_layout.pos_to_chess.get(pos_)
            if current_chess_id is not None:
                hp_limit = _hidden_get_chess_profile(current_chess_id)['init_hp']
                virtual_layout.set_hp(current_chess_id,
                                      hp=min(hp_limit, virtual_layout.chess_details[current_chess_id][1] + 25))
                if current_chess_id >= 4:
                    virtual_layout.set_hp(4, hp=25, hp_addition=True)
                else:
                    virtual_layout.set_hp(0, hp=25, hp_addition=True)

    if action:
        int_chess_id = _chess_to_int[side, action.chess_id]
        chess = virtual_layout.chess_details[int_chess_id]
        if chess is None:
            raise ValueError('Illegal action chess_id')
        # 移动
        pos = chess[0]
        new_pos = pos + 8 * action.mdr + action.mdc
        virtual_layout.set_chess_new_pos(int_chess_id, new_pos)
        # 回血
        blood_regen()
        # 攻击
        atk_delta = 8 * action.adr + action.adc
        if atk_delta:
            enemy_chess_id = virtual_layout.pos_to_chess.get(new_pos + atk_delta)
            atk = _hidden_get_chess_profile(int_chess_id)['atk']
            if virtual_layout.chess_details[enemy_chess_id][1] <= atk:
                virtual_layout.set_chess_new_pos(enemy_chess_id, None)
            else:
                virtual_layout.set_hp(enemy_chess_id, hp=-atk, hp_addition=True)
    else:
        # 只回血
        blood_regen()

    west_home = virtual_layout.pos_to_chess.get(56)
    east_home = virtual_layout.pos_to_chess.get(7)

    new_points = calculate_scores(virtual_layout) if calculate_points == 'hard' else None

    win_w = Final.NONE
    win_e = Final.NONE
    if west_home is None:
        win_w = Final.COMMANDER_DEAD
        win_e = Final.WIN
    elif east_home is None:
        win_e = Final.COMMANDER_DEAD
        win_w = Final.WIN
    elif turn_number == 99:
        if calculate_points == 'none':
            win_w = Final.OTHER
            win_e = Final.OTHER
        else:
            if calculate_points == 'soft':
                new_points = calculate_scores(virtual_layout)
            if new_points["W"][0] < new_points["E"][0]:
                win_e = Final.WIN
                win_w = Final.LESS_POINT
            elif new_points["E"][0] < new_points["W"][0]:
                win_w = Final.WIN
                win_e = Final.LESS_POINT
            elif new_points["W"][1] > new_points["E"][1]:
                win_w = Final.WIN
                win_e = Final.LESS_POINT
            else:
                win_e = Final.WIN
                win_w = Final.LESS_POINT

    ret_points = None
    if calculate_points == 'hard':
        ret_points = {"W": (new_points["W"][0] - original_points["W"][0], new_points["W"][1] - original_points["W"][1]),
                      "E": (new_points["E"][0] - original_points["E"][0], new_points["E"][1] - original_points["E"][1])}

    return virtual_layout, ret_points, {"W": win_w, "E": win_e}


def is_terminal(layout: Layout) -> Optional[str]:
    # 基于棋盘布局判断游戏是否终止。终止返回胜方W或E，不终止返回None
    west_home = layout.pos_to_chess.get(56)
    east_home = layout.pos_to_chess.get(7)
    if west_home is None:
        return 'E'
    elif east_home is None:
        return 'W'
    else:
        return None


def calculate_scores(layout: Layout) -> dict[str, tuple[int, int]]:
    # 基于棋盘返回计算分数
    west_home_score, east_home_score = 0, 0
    west_total_score, east_total_score = 0, 0
    w_side_id = _chess_to_int['W', ChessType.COMMANDER] // 4
    for int_chess_id, chess in enumerate(layout.chess_details):
        if chess is not None and chess[1] > 0:
            if int_chess_id % 4 == 0:
                if int_chess_id // 4 == w_side_id:
                    west_home_score = chess[1]
                else:
                    east_home_score = chess[1]
            else:
                if int_chess_id // 4 == w_side_id:
                    west_total_score += chess[1]
                else:
                    east_total_score += chess[1]
    return {'W': (west_home_score, west_total_score), 'E': (east_home_score, east_total_score)}


def who_win(layout: Layout) -> str:
    # 基于棋盘计算分数来判断谁获胜
    r = is_terminal(layout)
    if r:
        return r
    else:
        dct = calculate_scores(layout)
        west_home_score, west_total_score = dct['W']
        east_home_score, east_total_score = dct['E']
        if west_home_score > east_home_score:
            return 'W'
        elif west_home_score < east_home_score:
            return 'E'
        elif west_total_score > east_total_score:
            return 'W'
        else:
            return 'E'
