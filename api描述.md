# API描述
## 比赛术语
- 回合制对战（turn-based game）：针对同一个局面，双方轮流采取行动，分胜负的对战；
- 棋盘（board）：包括8*8格子，以及各格子的功能设定；
- 棋局（layout）：在对战过程中呈现出来的士兵分布信息；
- 对战双方（player）：分为左下角的West方（蓝色），右上角的East方（红色）；
- 先手（initiate）：一局中第一轮次的行动者，设定为West方；
- 局（game）：一局回合制对战，双方具有先手后手区别，最终分胜方负方，没有平局；
- 轮次（turn）：对战平台调用某方的play，在限定时间内得到返回的行动，在棋盘上实施行动，改变棋局，计算得分，如果无法判断胜负，则进入下一轮次；
- 行动（action）：描述对棋盘上的士兵发出的指令，包括士兵id、move dx，move dy，attack dx，attack dy。

## 玩家算法
```python
def play(board):  # 根据当前棋局，经过决策，返回动作
    ...
    return action  # 返回动作
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
        self.point = {"W":(2000, 3000), "E":(2000, 3000)}  # 当前得分，由司令生命值和士兵总生命值构成
        self.action_history = []  # 行动历史，下标为轮次，值为action
        
    def action_valid(self, layout, side, action):  # 基于棋盘布局和指定对战方，判断行动是否有效
        ...
        return True
    
    def make_turn(self, layout, side, action):  # 基于棋盘布局和指定对战方，进行一个轮次的对战，返回结果布局和分数变化
        ...
        return result_layout, delta_point
```

## 动作类Action
- id是士兵标识，分为"R"（骑兵）"A"（弓兵）"F"（步兵）
- mdx, mdy表示移动目的地的坐标偏移值（+-）
- adx, ady表示攻击目的地的坐标偏移值（+-），**注意**：此偏移值相对于移动后的新位置
```python
from collections import namedtuple
Action = namedtuple("Action", "id mdx mdy adx ady")
action = Action(id="R", mdx=0, mdy=0, adx=1, ady=0)
```