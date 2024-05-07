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
import copy
from typing import Optional


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


class Chess:
    def __init__(self, side: str, chess_id: ChessType, hp: int, pos: tuple[int, int]):
        self.chess_id: ChessType = chess_id  # 棋子ID, 如：ChessType.COMMANDER
        self.hp: int = hp  # 棋子当前剩余血量
        self.side: str = side  # 如："W"
        self.pos: tuple[int, int] = pos  # 棋子当前位置(row, col)


class Layout(list):
    def __init__(self, layout):
        super().__init__(layout)
        self.chess_list: list[Chess] = []

    def initialize(self):
        self.chess_list: list[Chess] = []
        for i in range(8):
            for j in range(8):
                chess = self[i][j]
                if chess:
                    self.chess_list.append(chess)


class Board:
    def __init__(self, context, storage: dict, action_history: list[Optional['Action']]):

        self.turn_number: int = context.round - 1
        if self.turn_number % 2 == 0:
            self.my_side: str = "W"
            enemy_side = "E"
        else:
            self.my_side: str = "E"
            enemy_side = "W"

        # 生成layout和血量
        self.layout: Layout = Layout([[None] * 8 for _ in range(8)])
        my_hp_sum, enemy_hp_sum = 0, 0
        my_bots, enemy_bots = context.me.get_bots(), context.enemy.get_bots()

        for bot in my_bots:
            pos = (bot.row, bot.col)
            id_ = _tencent_id[bot.type_id]
            self.layout[bot.row][bot.col] = Chess(self.my_side, id_, bot.hp, pos)
            my_hp_sum += bot.hp
        for bot in enemy_bots:
            pos = (bot.row, bot.col)
            id_ = _tencent_id[bot.type_id]
            self.layout[bot.row][bot.col] = Chess(enemy_side, id_, bot.hp, pos)
            enemy_hp_sum += bot.hp
        self.layout.initialize()

        self.point: dict[str, tuple[float, float]] = {
            self.my_side: (context.me.get_bots(name=100)[0].hp, my_hp_sum),
            enemy_side: (context.enemy.get_bots(name=100)[0].hp, enemy_hp_sum)
        }

        self.chess_profile: dict[ChessType, tuple] = {ChessType.COMMANDER: (0, 1600), ChessType.WARRIOR: (200, 1000),
                                                      ChessType.ARCHER: (250, 700), ChessType.PROTECTOR: (150, 1400)}

        self.my_storage: dict = storage
        self.total_turn: int = 100
        self.action_history: list = action_history


Action = namedtuple("Action", "chess_id mdr mdc adr adc")


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
                last_action = Action(enemy_id, enemy_move_r, enemy_move_c, enemy_atk_r, enemy_atk_c)
            else:
                last_action = None
            _action_history.append(last_action)
        board = Board(context, _all_players_storage[my_id], copy.deepcopy(_action_history))
        original_layout = copy.deepcopy(board.layout)
        original_my_side = board.my_side
        # 运行玩家函数
        result: Optional[Action] = func(board)
        if result and not isinstance(result, Action):
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
            bot = context.me.get_bots(name=_game_id[result.chess_id])[0]
            row, col = bot.row, bot.col
            new_r, new_c = row + result.mdr, col + result.mdc
            if not (0 <= new_r < 8 and 0 <= new_c < 8):
                raise ValueError("Move Out of Game Map")
            if (result.mdr or result.mdc) and original_layout[new_r][new_c]:
                raise ValueError("Move Blocked")

            bot.move_to((row + result.mdr, col + result.mdc))

            if result.adr != 0 or result.adc != 0:
                atk_r = row + result.mdr + result.adr
                atk_c = col + result.mdc + result.adc
                if not (0 <= atk_r < 8 and 0 <= atk_c < 8):
                    raise ValueError("Bot Attack Out of Game Map")
                enemy_chess = original_layout[atk_r][atk_c]
                if not (enemy_chess and enemy_chess.side != original_my_side):
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
    for i in range(8):
        for j in range(8):
            chess = layout[i][j]
            if chess and chess.side == side and chess.chess_id == action.chess_id:
                new_r, new_c = i + action.mdr, j + action.mdc
                if (new_r, new_c) not in get_valid_move(layout, side, chess.chess_id):
                    return False
                if action.adr == 0 and action.adc == 0:
                    return True
                atk_r, atk_c = new_r + action.adr, new_c + action.adc
                if not (0 <= atk_r < 8 and 0 <= atk_c < 8):
                    return False
                enemy_chess = layout[atk_r][atk_c]
                if enemy_chess and enemy_chess.side != chess.side:
                    return True
                else:
                    return False
    return False


def get_chess(layout: Layout, side: str, chess_id: ChessType) -> Optional[Chess]:
    for i in range(8):
        for j in range(8):
            chess = layout[i][j]
            if chess and chess.side == side and chess.chess_id == chess_id:
                return chess
    return None


def get_valid_chess(layout: Layout, side: str) -> list[Chess]:
    chess_list = []
    for i in range(8):
        for j in range(8):
            chess = layout[i][j]
            if chess and chess.side == side:
                chess_list.append(chess)
    chess_list.sort(key=lambda x: _game_id[x.chess_id])
    return chess_list


def get_chess_profile(chess_id: ChessType) -> dict:
    my_bot = api.meta.BOT_ATTRIBUTES[_game_id[chess_id]]
    return {'atk': my_bot.attack_strength, 'atk_pos': my_bot.attack_delta_pos.copy(), 'init_hp': my_bot.init_hp,
            'move_range': my_bot.move_range}


def get_valid_move(layout: Layout, side: str, chess_id: ChessType) -> list[tuple[int, int]]:
    # 返回一个列表,每个元素是可移动位置(row,col)的二元组
    chess = get_chess(layout, side, chess_id)
    pos = chess.pos
    move_range = get_chess_profile(chess_id)["move_range"]
    position_list = []
    for delta_r in range(-move_range, move_range + 1, 1):
        for delta_c in range(-move_range, move_range + 1, 1):
            new_r = pos[0] + delta_r
            new_c = pos[1] + delta_c
            if not (delta_r or delta_c):
                position_list.append((new_r, new_c))
                continue
            path_length = abs(delta_r) + abs(delta_c)
            if path_length <= move_range:
                if (0 <= new_r < 8 and 0 <= new_c < 8) and layout[new_r][new_c] is None:
                    # 判断目标位置在不在,因为距离最大是2,可以手动枚举
                    if path_length == 2:
                        if delta_r and delta_c:
                            # 针对1,1型路
                            if not (layout[pos[0] + delta_r][pos[1]] and layout[pos[0]][pos[1] + delta_c]):
                                position_list.append((new_r, new_c))
                        else:
                            # 针对0,2型路
                            if not layout[pos[0] + delta_r // 2][pos[1] + delta_c // 2]:
                                position_list.append((new_r, new_c))
                    else:
                        position_list.append((new_r, new_c))
    return position_list


def get_valid_attack(layout: Layout, side: str, chess_id: ChessType) -> list[tuple[tuple[int, int], Chess]]:
    # 返回一个列表,列表的每个元素是一个(位置,兵)的二元组
    chess = get_chess(layout, side, chess_id)
    atk_pos_list = get_chess_profile(chess_id)["atk_pos"]
    atk_list = []
    for i in range(8):
        for j in range(8):
            delta = (i - chess.pos[0], j - chess.pos[1])
            if delta in atk_pos_list:
                if layout[i][j] and layout[i][j].side != side:
                    atk_list.append(((i, j), layout[i][j]))
    return atk_list


def get_valid_actions(layout: Layout, side: str, *, chess_id: Optional[ChessType] = None) -> list[Optional[Action]]:
    # 基于棋局和指定行动方，返回列表,元素是某个棋子所有可能的行动Action
    if chess_id is None:
        list_actions = [None]
        for id_ in [ChessType.WARRIOR, ChessType.ARCHER, ChessType.PROTECTOR]:
            list_actions.extend(get_valid_actions(layout, side, chess_id=id_)[1:])
        return list_actions

    result = [None]
    chess = get_chess(layout, side, chess_id)
    if not chess:
        return [None]

    profile = get_chess_profile(chess_id)
    atk_pos = profile['atk_pos']
    possible_moves = get_valid_move(layout, side, chess_id)
    for virtual_pos in possible_moves:
        mdr, mdc = virtual_pos[0] - chess.pos[0], virtual_pos[1] - chess.pos[1]
        if mdr or mdc:
            result.append(Action(chess_id, mdr, mdc, 0, 0))
        for delta in atk_pos:
            t_r, t_c = virtual_pos[0] + delta[0], virtual_pos[1] + delta[1]
            if 0 <= t_r < 8 and 0 <= t_c < 8:
                if layout[t_r][t_c] is not None and layout[t_r][t_c].side != side:
                    result.append(Action(chess_id, mdr, mdc, delta[0], delta[1]))
    return result


def make_turn(layout: Layout, side: str, action: Optional[Action], *, turn_number: int = 0) -> \
        tuple[Layout, dict[str, tuple[int, int]], dict[str, Final]]:
    # 基于棋盘布局和指定对战方，进行一个虚拟的轮次，返回结果布局，分数变化，胜利情况。默认提供的是有效行动
    original_score = calculate_scores(layout)
    virtual_layout = copy.deepcopy(layout)
    if action:
        find = False
        for i in range(8):
            for j in range(8):
                chess = virtual_layout[i][j]
                if chess and chess.side == side and chess.chess_id == action.chess_id:
                    find = True
                    break
            if find:
                break
        else:
            raise IndexError
        # 移动
        new_r, new_c = i + action.mdr, j + action.mdc
        virtual_layout[i][j], virtual_layout[new_r][new_c] = None, chess

        # 记得改士兵的信息!
        virtual_layout[new_r][new_c].pos = (new_r, new_c)
        # 回血
        for i, j in {(3, 3), (3, 4), (4, 3), (4, 4)}:
            current_chess = virtual_layout[i][j]
            if current_chess:
                hp_limit = get_chess_profile(current_chess.chess_id)['init_hp']
                current_chess.hp = min(hp_limit, current_chess.hp + 25)
                if current_chess.side == 'W':
                    virtual_layout[7][0].hp += 25
                else:
                    virtual_layout[0][7].hp += 25
        # 攻击
        if action.adr or action.adc:
            enemy_chess = virtual_layout[new_r + action.adr][new_c + action.adc]
            atk = get_chess_profile(chess.chess_id)['atk']
            if enemy_chess.hp <= atk:
                virtual_layout[new_r + action.adr][new_c + action.adc] = None
            else:
                enemy_chess.hp -= atk
    else:
        # 只回血
        for i, j in {(3, 3), (3, 4), (4, 3), (4, 4)}:
            current_chess = virtual_layout[i][j]
            if current_chess:
                hp_limit = get_chess_profile(current_chess.chess_id)['init_hp']
                current_chess.hp = min(hp_limit, current_chess.hp + 25)
                if side == 'W':
                    virtual_layout[7][0].hp += 25
                else:
                    virtual_layout[0][7].hp += 25
    virtual_layout.initialize()
    new_score = calculate_scores(virtual_layout)
    deltaW = (new_score["W"][0] - original_score["W"][0], new_score["W"][1] - original_score["W"][1])
    deltaE = (new_score["E"][0] - original_score["E"][0], new_score["E"][1] - original_score["E"][1])

    west_home = virtual_layout[7][0]
    east_home = virtual_layout[0][7]

    winW = Final.NONE
    winE = Final.NONE
    if west_home is None or west_home.hp <= 0:
        winW = Final.COMMANDER_DEAD
        winE = Final.WIN
    elif east_home is None or east_home.hp <= 0:
        winE = Final.COMMANDER_DEAD
        winW = Final.WIN
    elif turn_number == 99:
        if new_score["W"][0] < new_score["E"][0]:
            winE = Final.WIN
            winW = Final.LESS_POINT
        elif new_score["E"][0] < new_score["W"][0]:
            winW = Final.WIN
            winE = Final.LESS_POINT
        elif new_score["W"][1] > new_score["E"][1]:
            winE = Final.LESS_POINT
            winW = Final.WIN
        else:
            winE = Final.WIN
            winW = Final.LESS_POINT

    return virtual_layout, {"W": deltaW, "E": deltaE}, {"W": winW, "E": winE}


def is_terminal(layout: Layout) -> Optional[str]:
    # 基于棋盘布局判断游戏是否终止。终止返回胜方W或E，不终止返回None
    west_home = layout[7][0]
    east_home = layout[0][7]
    if west_home is None or west_home.hp <= 0:
        return 'E'
    elif east_home is None or east_home.hp <= 0:
        return 'W'
    else:
        return None


def calculate_scores(layout: Layout) -> dict[str, tuple[int, int]]:
    # 基于棋盘返回计算分数
    west_home = layout[7][0]
    east_home = layout[0][7]
    west_home_score = 0 if (west_home is None or west_home.hp <= 0) else west_home.hp
    east_home_score = 0 if (east_home is None or east_home.hp <= 0) else east_home.hp
    west_total_score, east_total_score = 0, 0
    for i in range(8):
        for j in range(8):
            if (i == 0 and j == 7) or (i == 7 and j == 0):
                continue
            chess = layout[i][j]
            if chess:
                if chess.side == 'W':
                    west_total_score += chess.hp
                else:
                    east_total_score += chess.hp
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
