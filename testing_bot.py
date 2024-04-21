"""
下面的函数是用于测试的函数
在for_bot的所有对象中，只允许调用下面给定的对象（可删不可增）

测试中时间上限均为float('inf')
"""
from for_bot import ChessType, Chess, Action
from for_bot import get_chess_datas, calculate_real_atk, is_terminal, who_win, calculate_hp_sum, \
    generate_legal_successors, do_in_turn_action, do_after_turn, generate_all_possible_successors, do_list_actions, \
    generate_all_possible_successors_and_layouts
from for_bot import chess_number, chess_name_tuple, board_size, max_turn_number, max_spend_time, safe_area, \
    safe_area_add_for_chess, safe_area_add_for_home, home_initial_hp


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


def your_bot(board):
    """
        YOUR CODE HERE
    """
    list_action = [None, None, None]
    return list_action


# 任取两个智能体
west_play = action_less_bot
east_play = gambler_bot
