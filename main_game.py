# -*- coding: utf-8 -*-
"""
Version 0.1
Created on Sat Apr 20 13:29:19 2024
Author:Yunbo Sun
最初版本的主程序,内置了手操和什么也不做的机器人
"""
from core import *
def action_less_bot(board):
    return [[("wait"), ("wait"), ("wait")],0]
def hand_bot(board):
    """
    玩家1的操作是手操
    """
    opt=[]
    print(board.storage)
    print(board.get_block_info(0,0))
    for i in range(3):
        inp=list(input().split())
        target=(int(inp[1]),int(inp[2]))
        opt.append((inp[0],target))
    
    return [opt,opt]

if __name__=="__main__":
    g1=Game()
    g1.load_ai(hand_bot,action_less_bot)
    g1.setup()
    g1.game_process()

