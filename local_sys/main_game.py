# -*- coding: utf-8 -*-
"""
Version 0.1
Created on Sat Apr 20 13:29:19 2024
Author:Yunbo Sun
最初版本的主程序,内置了手操和什么也不做的机器人

Version 0.2
Created on Sat May 11 1:04:19 2024
Author:Yunbo Sun
第二个版本的主程序,目前和我们api的格式基本兼容,但可能在storage上不太一样
"""

from core_changed import *
"""
注意 请不要在这个程序内重复定义ChessType之类的类
"""
def action_less_bot(board):
    return None
def hand_bot(board):
    """
    这是一个标准的玩家ai模板，此时玩家1的操作是手操
    """
    opt=[]
    print(board.action_history)
   
    s=list(map(int,input().split()))
    
    #如果你要更新你的storage,那么你就返回一个[Action,new_storage]的列表
    #否则,你就只需要返回一个Action
    return [Action(ChessType.ARCHER,s[0],s[1],s[2],s[3]),board.turn_number]

if __name__=="__main__":
    g1=Game()
    g1.load_ai(hand_bot,action_less_bot)
    g1.setup()
    g1.game_process()

