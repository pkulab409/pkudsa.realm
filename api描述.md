# API描述
## 比赛术语
- 回合制对战（turn-based game）：针对同一个局面，双方轮流采取行动，分胜负的对战；
- 棋盘（board）：包括8*8格子，以及各格子的功能设定；
- 棋局（layout）：在对战过程中呈现出来的士兵分布信息；
- 对战双方（player）：分为左下角的West方（蓝色），右上角的East方（红色）；
- 先手（initiate）：一局中第一轮次的行动者，设定为West方；
- 盘（set）：两个玩家的一盘对战，由轮流先手的多局构成，20局11胜（win），如果10:10则为战平（tie）；
- 局（game）：一局回合制对战，双方具有先手后手区别，最终分胜方负方，没有平局；
- 轮次（turn）：对战平台调用某方的play，在限定时间内得到返回的行动，在棋盘上实施行动，改变棋局，计算得分，如果无法判断胜负，则进入下一轮次；
- 行动（action）：描述对棋盘上每个士兵发出的指令。

## 玩家算法
```python
def play(board):  # 根据当前棋局，经过决策，返回动作
    ...
    return list_action  # 返回动作列表，下标0/1/2对应骑兵 弓兵 步兵
```

## 棋盘类Board
```python
class Board:
    def __init__(self):
        self.layout = [[0]*8 for _ in range(8)]  # 棋盘8*8嵌套列表
        self.my_side = "W"  # W方，或者"E"为E方
        self.my_storage = dict()  # 跨turn存储，字典
        self.total_turn = 60  # 总轮数
        self.turn_number = 0  # 当前轮次序号，首轮为0
        self.action_history = []  # 行动历史，下标为轮次，值为list_action
```

## 动作类Action
- op是指令，分为move/attack
- dx,dy表示指令目标的坐标偏移值（+-）
- 已死亡棋子或本轮次不移动的棋子使用None返回，不使用该Action类
```python
from collections import namedtuple
Action = namedtuple("Action", "op dx dy")
list_action = [Action(op="move", dx=0, dy=0), 
               None,
               Action(op="attack", dx=1, dy=1)]
```