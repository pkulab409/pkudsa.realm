# API描述
## 比赛术语
- 回合制对战（turn-based game）：针对同一个局面，双方轮流采取行动，分胜负的对战；
- 棋盘（board）：包括8*8格子，以及各格子的功能设定；
- 棋局（layout）：在对战过程中呈现出来的士兵分布信息；
- 对战双方（player）：分为左下角的West方（红色），右上角的East方（蓝色）；
- 先手（initiate）：一局中第一轮次的行动者，设定为West方；
- 局（game）：一局回合制对战，双方具有先手后手区别，最终分胜方负方，没有平局；
- 轮次（turn）：对战平台调用某方的play，在限定时间内得到返回的行动，在棋盘上实施行动，改变棋局，计算得分，如果无法判断胜负，则进入下一轮次；
- 行动（action）：描述对棋盘上的士兵发出的指令，包括士兵id、move dr，move dc，attack dr，attack dc。

## 玩家算法代码源文件
```python
import realm  # 定义了所有玩家可以用的类和实用函数

def play(board):  # 根据当前棋局，经过决策，返回动作
    ...
    return action  # 返回动作
```

## realm.py的类定义
### 棋子类Chess
```python
from enum import Enum
class ChessType(Enum):
    COMMANDER = 0
    WARRIOR = 1
    ARCHER = 2
    PROTECTOR = 3
    
class Chess:
    def __init__(self, side, id, hp, pos):
        self.id = id  # 棋子ID, 如：ChessType.COMMANDER
        self.hp = hp  # 棋子当前剩余血量
        self.side = side  # 如："W"
        self.pos = pos  # 棋子当前位置(row, col)
```

### 棋盘类Board
- layout是当前棋盘局面，其中数据是棋子类Chess或None
- my_storage允许修改，可用于保存数据
```python
class Board:
    def __init__(self):
        self.layout = [[None]*8 for _ in range(8)]  # 棋盘8*8嵌套列表layout[row][col]，列表元素类型是Chess
        self.my_side = "W"  # W方，或者"E"为E方
        self.my_storage = dict()  # 跨turn存储，字典
        self.total_turn = 100  # 总轮数
        self.turn_number = 0  # 当前轮次序号，首轮为0
        self.chess_profile = {ChessType.COMMANDER:()}
        self.point = {"W":(2000, 3000), "E":(2000, 3000)}  # 当前得分，由（司令生命值，士兵总生命值）构成
        self.action_history = []  # 行动历史，下标为轮次，值为action
```

### 胜负原因类Final
```python
from enum import Enum
class Final(Enum):
    WIN = 0
    INVALID_ACTION = 1
    TIMEOUT = 2
    COMMANDER_DEAD = 3
    LESS_POINT = 4
```

### 动作类Action
- id是士兵标识，ChessType
- mdr, mdc表示移动目的地的坐标偏移值（+-）
- adr, adc表示攻击目的地的坐标偏移值（+-），**注意**：此偏移值相对于移动后的新位置
- adr, adc均设置为0时表示不攻击
```python
from collections import namedtuple
Action = namedtuple("Action", "id mdr mdc adr adc")
# 例如：action = Action(id=ChessType.ARCHER, mdr=0, mdc=0, adr=1, adc=0)
```

### 实用函数
```python
def valid_action(layout, side, action):  # 返回action的有效性True/False
    ...

def make_turn(layout, side, action):  
    # 在棋盘上进行一个轮次的行动，返回结果layout和分数的delta值(deltaW,DeltaE)，以及可能的胜负(sideW,sideE)
    ...

def get_chess(layout, side, id):  # 获取指定id士兵的Chess对象
    ...

def get_valid_chess(layout, side):  # 获取指定方的有效士兵，返回Chess对象列表
    ...

def get_valid_move(layout, side, id):  # 获取可以一次移动到达的合法位置，排除被挡路的位置
    ...

def get_valid_attack(layout, side, id):  # 获取可以直接攻击的合法位置和目标，排除无效位置
    ...

def get_valid_action(layout, side, id):  # 获取指定士兵所有可能的合法动作
    ...

```