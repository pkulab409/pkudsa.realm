"""
内核
"""
import time
from for_bot import ChessType, Board, Chess, Action, get_chess_datas, calculate_real_atk


class GameException(Exception):
    # 不合法行为捕获的错误
    def __init__(self, *, turn: int, side: str, message: str, origin_exception: BaseException = None):
        super().__init__()
        self.turn = turn
        self.side = side
        self.message = message
        self.origin_exception = origin_exception


def _reverse_side(s: str) -> str:
    # E和W互换的函数
    if s == 'W':
        return 'E'
    else:
        return 'W'


def _generate_from_chess_data() -> list:
    # 将_ChessData类中数据转化为CoreChess类可读数据
    lst = get_chess_datas()
    results = []
    for chess in lst:
        results.append({'name': chess.name, 'hp': chess.hp_limit, 'atk': chess.atk, 'moving_set': chess.moving_set,
                        'atk_set': chess.atk_set})
    return results


class CoreChess:
    """
    内核layout中数据的类型，可视为Chess类的高级版本
    """

    def __init__(self, *, name: ChessType, side: str, hp: int, atk: int = 0, moving_set: frozenset = frozenset(),
                 atk_set: frozenset = frozenset(), position: tuple):
        self.side: str = side  # W或E
        self.name: ChessType = name  # 类型
        self.hp: int = hp  # 生命
        self.hp_limit: float = hp if name != ChessType.Home else float('inf')  # 生命上限
        self.atk: int = atk  # 攻击力
        self.moving_set: frozenset[tuple] = moving_set  # 相对移动范围
        self.atk_set: frozenset[tuple] = atk_set  # 相对攻击范围，不含(0,0)
        self.position: tuple[int, int] = position  # 位置
        self.alive: bool = True  # 是否存活

    def do_attack(self, other):
        # 进行攻击
        other.hp -= calculate_real_atk(self.name, other.name)


chess_number: int = 3  # 暂时不许更改

board_size: int = 8
max_turn_number: int = 60
max_spend_time: float = 0.1  # 最多耗时0.1秒

safe_area = frozenset({(4, 4), (3, 3), (3, 4), (4, 3)})
safe_area_add_for_chess: int = 50
safe_area_add_for_home: int = 20

home_initial_hp: int = 2000  # 初始基地生命值


class Core:
    # 用于运行的类
    def __init__(self, *, west_play, east_play):
        datas = _generate_from_chess_data()
        west_cavalry = CoreChess(side='W', position=(0, 1), **datas[0])
        west_bowman = CoreChess(side='W', position=(1, 0), **datas[1])
        west_infantry = CoreChess(side='W', position=(1, 1), **datas[2])
        self.west = [west_cavalry, west_bowman, west_infantry]
        self.west_home = CoreChess(side='W', position=(0, 0), name=ChessType.Home, hp=home_initial_hp)

        east_cavalry = CoreChess(side='E', position=(board_size - 1, board_size - 2), **datas[0])
        east_bowman = CoreChess(side='E', position=(board_size - 2, board_size - 1), **datas[1])
        east_infantry = CoreChess(side='E', position=(board_size - 2, board_size - 2), **datas[2])
        self.east = [east_cavalry, east_bowman, east_infantry]
        self.east_home = CoreChess(side='E', position=(board_size - 1, board_size - 1), name=ChessType.Home,
                                   hp=home_initial_hp)

        self.turn_number = 0

        self.layout: list[list[None | CoreChess]] = [[None for _ in range(board_size)] for _ in
                                                     range(board_size)]  # 这里的layout是按直角坐标系建立的，不同于普通表格
        for chess in self.west + self.east + [self.west_home, self.east_home]:
            i, j = chess.position
            self.layout[i][j] = chess

        self.west_storage = {}
        self.east_storage = {}

        self.west_play = west_play
        self.east_play = east_play

        self.west_spend_time: list[int] = []
        self.east_spend_time: list[int] = []

        self.action_history: list[list[Action | None]] = []  # 防止攻击篡改同时记录多个history
        self.west_action_history: list[list[Action | None]] = []
        self.east_action_history: list[list[Action | None]] = []

    def generate_for_bot_layout(self) -> list[list[any]]:
        # 返回bot使用的layout
        result: list[list[any]] = [[None for _ in range(board_size)] for _ in range(board_size)]
        for i in range(board_size):
            for j in range(board_size):
                chess = self.layout[i][j]
                if chess is not None:
                    result[i][j] = Chess(name=chess.name, hp=chess.hp, side=chess.side)
        return result

    def verify_after_turn(self) -> bool:
        # 一轮结束后确认人员是否死亡并给在安全区的加分，True表示游戏结束
        for i in range(board_size):
            for j in range(board_size):
                if i == j == 0 or i == j == board_size - 1:
                    continue
                chess = self.layout[i][j]
                if chess is not None:
                    if (i, j) in safe_area:
                        # 自身加血
                        chess.hp += safe_area_add_for_chess
                        chess.hp = min(chess.hp, chess.hp_limit)
                        # 基地加血
                        if chess.side == 'W':
                            self.west_home.hp += safe_area_add_for_home
                        else:
                            self.east_home.hp += safe_area_add_for_home
                    if chess.hp <= 0:
                        chess.hp = 0
                        chess.alive = False
                        self.layout[i][j] = None
        if self.west_home.hp <= 0 or self.east_home.hp <= 0:
            return True
        else:
            return False

    def calculate_scores(self) -> dict:
        # 计算最后分数
        if self.west_home.hp <= 0:
            west_score = 0
        else:
            west_score = self.west_home.hp + sum(chess.hp for chess in self.west)
        if self.east_home.hp <= 0:
            east_score = 0
        else:
            east_score = self.east_home.hp + sum(chess.hp for chess in self.east)
        return {'W': west_score, 'E': east_score}

    def calculate_spend_time(self) -> dict:
        # 计算双方各耗时
        w_time, e_time = sum(self.west_spend_time), sum(self.east_spend_time)
        return {'W': w_time, 'E': e_time}

    def run(self):
        # 运行点函数
        while self.turn_number < max_turn_number:
            # 初始化策略函数
            side = 'W' if self.turn_number % 2 == 0 else 'E'
            board = Board(turn_number=self.turn_number, layout=self.generate_for_bot_layout(), side=side,
                          total_turn=max_turn_number, spend_time=self.calculate_spend_time())
            if side == 'W':
                board.action_history = self.west_action_history
                board.my_storage = self.west_storage
                play_func = self.west_play
            else:
                board.action_history = self.east_action_history
                board.my_storage = self.east_storage
                play_func = self.east_play
            # 运行策略函数
            try:
                t0 = time.time_ns()
                list_action = play_func(board)  # 运行
                delta_t = time.time_ns() - t0
                if side == 'W':
                    self.west_spend_time.append(delta_t)
                    self.west_storage = board.my_storage
                else:
                    self.east_spend_time.append(delta_t)
                    self.east_storage = board.my_storage
            except BaseException as e:
                raise GameException(turn=self.turn_number, side=side, message="运行时报错", origin_exception=e)
            if delta_t > max_spend_time * (10 ** 9):
                raise GameException(turn=self.turn_number, side=side, message=f"运行超时，总耗时{delta_t / (10 ** 9)}秒")
            # 进行动作
            try:
                assert isinstance(list_action, list) and len(list_action) == chess_number
                for i in range(chess_number):
                    action = list_action[i]
                    if action is None:
                        continue
                    assert isinstance(action, Action)
                    chess = self.west[i] if side == 'W' else self.east[i]
                    assert chess.alive
                    assert isinstance(action.dx, int) and isinstance(action.dy, int)
                    if action.op == 'move':
                        assert (action.dx, action.dy) in chess.moving_set
                        if action.dx == action.dy == 0:
                            continue
                        x, y = chess.position
                        new_x, new_y = action.dx + x, action.dy + y
                        assert 0 <= new_x < board_size and 0 <= new_y < board_size
                        assert self.layout[new_x][new_y] is None
                        chess.position = (new_x, new_y)
                        self.layout[x][y], self.layout[new_x][new_y] = None, chess
                    elif action.op == 'attack':
                        assert (action.dx, action.dy) in chess.atk_set
                        x, y = chess.position
                        atk_x, atk_y = action.dx + x, action.dy + y
                        assert 0 <= atk_x < board_size and 0 <= atk_y < board_size
                        enemy = self.layout[atk_x][atk_y]
                        assert enemy is not None and enemy.side == _reverse_side(side)
                        chess.do_attack(enemy)
                    else:
                        raise AssertionError
            except AssertionError:
                raise GameException(turn=self.turn_number, side=side, message=f"action list illegal: {list_action}")
            # 结束处理
            self.action_history.extend(list_action.copy())  # 三个history都要增加历史
            self.west_action_history.extend(list_action.copy())
            self.east_action_history.extend(list_action.copy())
            if self.verify_after_turn():
                break
            self.print_layout()
            self.turn_number += 1
        # 结束计算分数
        print(f'Turn: {self.turn_number}')
        c = self.calculate_scores()
        w_score, e_score = c['W'], c['E']
        print(f'West score: {w_score}  East score: {e_score}')
        time_dict = self.calculate_spend_time()
        print(f'West spends {time_dict["W"] / (10 ** 9)} seconds  East spends {time_dict["E"] / (10 ** 9)} seconds')
        if w_score > e_score:
            print('West win!')
        elif w_score < e_score:
            print('East win!')
        else:
            if time_dict['W'] < time_dict['E']:
                print('West win!')
            else:
                print('East win!')

    def print_layout(self):
        output_layout: list[list[None | str]] = [[None for _ in range(board_size)] for _ in range(board_size)]
        for i in range(board_size):
            for j in range(board_size):
                chess = self.layout[i][j]
                if chess is None:
                    if (i, j) in safe_area:
                        s = 'area'
                    else:
                        s = ''
                else:
                    s = chess.name.name + chess.side
                s += ' ' * (9 - len(s))
                output_layout[board_size - 1 - j][i] = s
        for row in output_layout:
            print(' | '.join(row))
        print('================================================================================================')
        print('================================================================================================')
