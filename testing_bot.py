"""
下面的函数是用于测试的函数
在for_bot的所有对象中，只允许调用下面给定的对象（可删不可增）
"""
from for_bot import ChessType, Chess, Action
from for_bot import get_chess_datas, calculate_real_atk, is_terminal, who_win, calculate_hp_sum, \
    generate_legal_successors, do_in_turn_action, do_after_turn, generate_all_possible_successors, do_list_actions, \
    generate_all_possible_successors_and_layouts
from for_bot import chess_number, chess_name_tuple, board_size, max_turn_number, max_spend_time, safe_area, \
    safe_area_add_for_chess, safe_area_add_for_home, home_initial_hp
import random
import time


def action_less_bot(board):
    # 静止不动的bot
    return [None, None, None]


def gambler_bot(board):
    # 赌徒bot（能攻击就攻击，不能攻击就往敌方基地走）
    side = board.my_side
    layout = board.layout
    results = []
    for i in range(chess_number):
        action_list = generate_legal_successors(layout, side)[i]
        if len(action_list) == 1:
            current_action = None
        else:
            current_action = Action(op='move', dx=0, dy=0)
            for action in action_list[1:]:
                if current_action.op == 'move' and action.op == 'attack':
                    current_action = action
                    break
                elif current_action.op == action.op == 'move':
                    if side == 'W' and action.dx + action.dy > current_action.dx + current_action.dy:
                        current_action = action
                    elif side == 'E' and action.dx + action.dy < current_action.dx + current_action.dy:
                        current_action = action
        results.append(current_action)
        layout = do_in_turn_action(layout, side, name=chess_name_tuple[i], action=current_action)
    return results


def direct_eval_bot(board):
    # 选择估值最大的动作
    side = board.my_side
    reverse_side = lambda x: 'W' if x == 'E' else 'E'

    def evaluate(layout) -> float:
        winner = who_win(layout)
        if winner is None:
            dic = calculate_hp_sum(layout)
            return dic[side] - dic[reverse_side(side)]
        elif winner == side:
            return float('inf')
        else:
            return float('-inf')

    value, action = float('-inf'), [None, None, None]
    for action_list, new_layout in generate_all_possible_successors_and_layouts(board.layout, side):
        new_value = evaluate(new_layout)
        if new_value > value or (new_value == value and random.random() < 0.3):
            value, action = new_value, action_list
    return action


def minimax_under_time_limit_bot(board):
    # 简单minmax树搜索算法（又慢又傻）
    max_depth = 2
    side = board.my_side
    reverse_side = lambda x: 'W' if x == 'E' else 'E'
    t0 = time.time()

    def evaluate(layout) -> float:
        winner = who_win(layout)
        if winner is None:
            dic = calculate_hp_sum(layout)
            return dic[side] - dic[reverse_side(side)]
        elif winner == side:
            return float('inf')
        else:
            return float('-inf')

    def helper(layout, current_side, depth):
        if is_terminal(layout) or depth == max_depth:
            return evaluate(layout), []

        if current_side == side:
            value, big_actions = float('-inf'), []
            for action_list, new_layout in generate_all_possible_successors_and_layouts(layout, side):
                new_value, old_list = helper(new_layout, reverse_side(current_side), depth + 1)
                if new_value > value or (new_value == value and random.random() < 0.3):
                    value, big_actions = new_value, old_list + [action_list]
                if time.time() - t0 > max_spend_time / 2:
                    break
            return value, big_actions
        else:
            value, big_actions = float('inf'), []
            for action_list, new_layout in generate_all_possible_successors_and_layouts(layout, side):
                new_value, old_list = helper(new_layout, reverse_side(current_side), depth + 1)
                if new_value < value or (new_value == value and random.random() < 0.3):
                    value, big_actions = new_value, old_list + [action_list]
                if time.time() - t0 > max_spend_time / 2:
                    break
            return value, big_actions

    _, list_action = helper(board.layout, side, 0)
    if list_action:
        return list_action.pop()
    else:
        raise


def alpha_beta_under_time_limit_bot(board):
    # 简单alpha-beta剪枝算法（也很慢很傻）
    max_depth = 2
    side = board.my_side
    reverse_side = lambda x: 'W' if x == 'E' else 'E'
    t0 = time.time()

    def evaluate(layout) -> float:
        winner = who_win(layout)
        if winner is None:
            dic = calculate_hp_sum(layout)
            return dic[side] - dic[reverse_side(side)]
        elif winner == side:
            return float('inf')
        else:
            return float('-inf')

    def helper(layout, current_side, depth, *, alpha, beta):
        if is_terminal(layout) or depth == max_depth:
            return evaluate(layout), []
        next_side = reverse_side(current_side)
        if current_side == side:
            value, big_actions = float('-inf'), []
            for action_list, new_layout in generate_all_possible_successors_and_layouts(layout, side):
                new_value, old_list = helper(new_layout, next_side, depth + 1, alpha=alpha, beta=beta)
                if new_value > value or (new_value == value and random.random() < 0.3):
                    value, big_actions = new_value, old_list + [action_list]
                if time.time() - t0 > max_spend_time / 2:
                    break
                if value >= beta:
                    return value, big_actions
                alpha = max(alpha, value)
            return value, big_actions
        else:
            value, big_actions = float('inf'), []
            for action_list, new_layout in generate_all_possible_successors_and_layouts(layout, side):
                new_value, old_list = helper(new_layout, next_side, depth + 1, alpha=alpha, beta=beta)
                if new_value < value or (new_value == value and random.random() < 0.3):
                    value, big_actions = new_value, old_list + [action_list]
                if time.time() - t0 > max_spend_time / 2:
                    break
                if value <= alpha:
                    return value, big_actions
                beta = min(beta, value)
            return value, big_actions

    _, list_action = helper(board.layout, side, 0, alpha=float('-inf'), beta=float('inf'))
    if list_action:
        return list_action.pop()
    else:
        raise


def improved_alpha_beta_bot(board):
    # 改进后的alpha-beta剪枝算法
    max_depth = 9
    side = board.my_side
    reverse_side = lambda x: 'W' if x == 'E' else 'E'
    get_side_by_depth = lambda d: side if (d // 3) % 2 == 0 else reverse_side(side)

    def evaluate(layout) -> float:
        dic = calculate_hp_sum(layout)
        return dic[side] - dic[reverse_side(side)]

    def helper(layout, depth, *, alpha, beta):
        if is_terminal(layout) or depth == max_depth:
            return evaluate(layout), []
        current_side = get_side_by_depth(depth)
        if current_side == side:
            value, big_actions = float('-inf'), []
            gen = generate_legal_successors(layout, current_side)[depth % 3]
            for action in gen:
                new_layout = do_in_turn_action(layout, current_side, name=chess_name_tuple[depth % 3], action=action,
                                               use_copy=True)
                if depth % 3 == 2:
                    new_layout = do_after_turn(new_layout)
                new_value, old_list = helper(new_layout, depth + 1, alpha=alpha, beta=beta)
                if new_value > value:
                    value, big_actions = new_value, old_list + [action]
                if value >= beta:
                    return value, big_actions
                alpha = max(alpha, value)
            return value, big_actions
        else:
            value, big_actions = float('inf'), []
            gen = generate_legal_successors(layout, current_side)[depth % 3]
            for action in gen:
                new_layout = do_in_turn_action(layout, current_side, name=chess_name_tuple[depth % 3], action=action,
                                               use_copy=True)
                if depth % 3 == 2:
                    new_layout = do_after_turn(new_layout)
                new_value, old_list = helper(new_layout, depth + 1, alpha=alpha, beta=beta)
                if new_value < value:
                    value, big_actions = new_value, old_list + [action]
                if value <= alpha:
                    return value, big_actions
                beta = min(beta, value)
            return value, big_actions

    _, list_action = helper(board.layout, 0, alpha=float('-inf'), beta=float('inf'))
    if len(list_action) >= 3:
        return [list_action.pop(), list_action.pop(), list_action.pop()]
    else:
        raise


# 任取两个智能体
west_play = improved_alpha_beta_bot
east_play = gambler_bot
