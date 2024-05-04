import realm
import random

def gambler_score(layout,side,id,action,enemy_side): 
    target_pos = realm.get_chess(layout,enemy_side,realm.ChessType.COMMANDER).pos
    current_pos = realm.get_chess(layout,side,id).pos
    if (current_pos[0] + action.adr,current_pos[1] + action.adc) == target_pos: # 如果攻击到司令
        return 8 # 赋予该Action较高的分数
    else: 
        profile = realm.get_chess_profile(id)
        atk_pos_list = profile['atk_pos']
        distance_min = 8
        for delta in atk_pos_list:
            t_r,t_c=current_pos[0]+delta[0],current_pos[1]+delta[1]
            distance = abs(t_r-target_pos[0])+abs(t_c-target_pos[1]) # 与敌方司令之间的曼哈顿距离
            distance_min = min(distance_min,distance) 
        return -distance_min

def gambler(layout,my_side):
    if realm.is_terminal(layout):
        return None # 结束局面无需选择
    enemy_side = 'E' if my_side == 'W' else 'W'
    my_best_score = -float('inf')
    best_action = None
    for id_ in [realm.ChessType.WARRIOR, realm.ChessType.ARCHER, realm.ChessType.PROTECTOR]:
        actions = realm.get_valid_actions(layout, my_side, id_)
        # 在所有的action中选择最好的
        for action in actions:
            if action:
                new_board_layout, scores, wins = realm.make_turn(layout, my_side, action)
                # 如果能够直接胜利就采取胜利的措施
                if wins[my_side] == realm.Final.WIN:
                    return action
                # 如果导致对面胜利, 不采取：
                if wins[enemy_side] == realm.Final.WIN:
                    continue
                # 否则取更有利于攻击到敌方司令的Action
                score = gambler_score(new_board_layout, my_side, id_, action, enemy_side)
                if score > my_best_score:
                    best_action = action
                    my_best_score = score
    return best_action

@realm.api_decorator
def update(board):
    my_side = board.my_side
    action = gambler(board.layout,my_side)