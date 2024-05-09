# API描述
## 目录
- [比赛术语](#比赛术语)
- [玩家算法代码源文件](#玩家算法代码源文件)
- [realm.py的类定义](#realmpy的类定义)
- [实用函数](#实用函数)

## 比赛术语
- 回合制对战（turn-based game）：针对同一个局面，双方轮流采取行动，分胜负的对战；
- 棋盘（board）：包括8*8格子，以及各格子的功能设定；
- 棋局（layout）：在对战过程中呈现出来的士兵分布信息；
- 对战双方（player）：分为左下角的West方（红色），右上角的East方（蓝色）；
- 先手（initiate）：一局中第一轮次的行动者，设定为West方；
- 局（game）：一局回合制对战，双方具有先手后手区别，最终分胜方负方，没有平局；
- 轮次（turn）：对战平台调用某方的update，在限定时间内得到返回的行动，在棋盘上实施行动，改变棋局，计算得分，如果无法判断胜负，则进入下一轮次；
- 行动（action）：描述对棋盘上的士兵发出的指令，包括士兵id、水平移动距离，竖直移动距离，攻击目标的水平偏移值，攻击目标的竖直偏移值

## 玩家算法代码源文件
- 其中api_decorator是一个装饰器，用于转换算法函数为引擎可读的函数
```python
import realm  # 定义了所有玩家可以用的类和实用函数

@realm.api_decorator
def update(board):  # 根据当前棋局，经过决策，返回动作
    pass          # 在此处编写代码
    return action  # 返回动作
```
平台将在对局开始前生成双方的AI实例, 每回合按照先后手轮流调用AI实例的update方法.<br>
在每一轮次(turn)结束后，平台将结算玩家得分并更新盘面(board)

## realm.py的类定义
### 棋子表示类ChessType
```python
from enum import Enum
class ChessType(Enum):
    COMMANDER = 0
    WARRIOR = 1
    ARCHER = 3
    PROTECTOR = 2
```

### 棋子类Chess
- chess_id：为士兵种类标识，如ChessType.ARCHER
- hp：棋子当前剩余血量
- side：棋子所属的对战方, 如："W"
- pos：棋子当前位置(row, col), 如(0,0)对应于左上角位置

```python
from collections import namedtuple
Chess = namedtuple("Chess", "side chess_id hp pos")
```

### 棋局类Layout
- Layout类是list的子类，本身是一个8*8的嵌套列表，用于呈现当前棋盘局面；<br>
    - 规定 layout[i][j] 返回第i行第j列的元素，例如 layout[0][0] 对应于棋盘的左上角;
    - 若棋盘在该位置上存在棋子，对应的元素类型为棋子类Chess，否则为None
- 该类拥有属性chess_list，保存有所有棋子。操作或生成Layout对象后需要调用initialize方法才能使chess_list标准化；initialize方法直接返回标准化后的chess_list
- uninitialized_copy方法返回一个（未标准化chess_list的）拷贝

```python
class Layout(list):
    def __init__(self, layout):
        super().__init__(layout)
        self.chess_list: list[Chess] = []

    def initialize(self) -> list[Chess]:
        self.chess_list: list[Chess] = []
        for i in range(8):
            for j in range(8):
                chess = self[i][j]
                if chess:
                    self.chess_list.append(chess)
        return self.chess_list

    def uninitialized_copy(self) -> 'Layout':
        new_layout = Layout([[self[i][j] for j in range(8)] for i in range(8)])
        return new_layout
```

### 棋盘类Board
- my_storage为字典，允许玩家修改，可用于跨轮次保存数据
- 其他可调用的属性可参考下方示例：

```python
class Board:
    def __init__(self):
        self.layout = Layout([[None]*8 for _ in range(8)])  # 棋盘为Layout类型
        self.my_side = "W"  # 己方所处的对战方。左下角的West方，或者"E"为右上角的East方
        self.my_storage = dict()  # 跨turn存储的字典
        self.total_turn = 100  # 总轮数
        self.turn_number = 0  # 当前轮次序号，首轮为0
        # 士兵的攻击力和生命值（上限/初始值）
        self.chess_profile = {ChessType.COMMANDER:(0, 1600), ChessType.WARRIOR:(200, 1000),
                              ChessType.ARCHER:(250, 700), ChessType.PROTECTOR:(150, 1400)}
        self.regain = (50, 50)  # 回血设置，（自己回血量，司令回血量）
        self.point = {"W":(1600, 3100), "E":(1600, 3100)}  # 当前得分，由（司令生命值，士兵总生命值）构成
        self.action_history = []  # 行动历史，下标为轮次，值为action
```

### 胜负原因类Final
```python
from enum import Enum
class Final(Enum):
    WIN = 0  # 胜利
    COMMANDER_DEAD = 1  # 司令死亡判负
    LESS_POINT = 2  # 总生命值低判负
    NONE = 3  # 暂不存在胜利方
    OTHER = 4  # 其它情形
```
胜负原因类Final主要用于make_turn函数，具体用法见下文

### 动作类Action
Action对象的属性：
- chess_id：为士兵种类标识，如ChessType.ARCHER
- mdr, mdc分别表示移动目的地相对于当前位置的水平坐标偏移值(move delta row) 和垂直坐标偏移值(move delta column)
    - 规定向右/向下为正，向左/向上为负（+-）
    - 例如: mdr=1, mdc=-2 表示向右移动1格，向上移动2格
- adr, adc表示攻击目的地相对于当前位置的坐标偏移值（+-），用法同行，**注意**：此偏移值相对于移动后的新位置
    - adr, adc均设置为0时表示不攻击

```python
from collections import namedtuple
Action = namedtuple("Action", "chess_id mdr mdc adr adc")
```
示例action:
```python
action = Action(chess_id=ChessType.ARCHER, mdr=0, mdc=0, adr=1, adc=0)
```

## 实用函数
#### 修饰器说明：
```python
api_decorator(func)
# 标准的装饰器，用于转换算法函数为引擎可读的标准函数
```

- 示例用法：
```python
@realm.api_decorator
def update(board): 
    pass # 编写对战算法
    return action
```


#### 函数功能和用法：
1. 判断传入action的合法性 <br>
```python
valid_action(layout, side, action) -> bool 
```
2. 获取指定id士兵的Chess对象<br>
```python
get_chess(layout, side, chess_id) -> Chess | None
```
3. 获取指定方的有效士兵 <br>
```python
get_valid_chess(layout, side) -> List[Chess]
```
- 返回Chess对象列表

4. 获取包含指定id士兵的基础属性<br>
```python
get_chess_profile(chess_id) -> dict
```
- 返回字典，key依次为'atk', 'atk_pos', 'init_hp', 'move_range'，对应的value分别为士兵的攻击力、由可攻击位置的偏移值数值构成的列表、初始生命值、移动范围（曼哈顿距离）

5. 获取可一次移动到达的合法位置（被挡路情况已排除） <br>
```python
get_valid_move(layout, side, chess_id) -> List[Tuple[int,int]]
```
- 返回一个列表，每个元素是合法位置(row,col)的二元组；
- 若不存在可移动位置，返回空列表

6. 获取可以直接攻击的合法位置和目标（无效位置已排除）<br>
```python
get_valid_attack(layout, side, chess_id) -> dict[Chess, tuple[int, int]]
```
- 返回一个字典，键是目标攻击士兵的Chess对象，值是目标攻击士兵的位置
- 若不存在可攻击的对象，返回空字典

7. 获取指定士兵所有可能的合法动作或全部合法动作
```python
get_valid_actions(layout, side, *, chess_id = None) -> List[Action|None]
```
- 返回一个列表，（除了首位的）元素是该棋子所有可能的Action对象；首位元素为None，表示不移动
- **死亡棋子返回的列表只含None**
- 若不指定chess_id, 则返回包含所有棋子的全部合法动作，返回值为列表。列表中元素顺序依次是None、WARRIOR所有行动、ARCHER所有行动、PROTECTOR所有行动

8. 基于棋盘布局和指定对战方，进行一个虚拟的轮次，返回结果 <br>
```python
make_turn(layout, side, action, *, turn_number=0) -> Tuple[Layout,dict,dict]
```
- 返回: 结果棋局new_layout、两方分数变化值构成的字典 {"W":delta_w,"E":delta_e}，以及可能的胜负{"W":win_w,"E":win_e}；
    - delta_w为W方的分数变化值
    - win_w表示胜负原因，根据实际情况，可能的取值为Final.WIN, Final.COMMANDER_DEAD, Final.LESS_POINT, Final.NONE
    - E方对应变量同理
- turn_number默认为0。可将其设置为当前turn number，为99（最终turn）时会进行强制结算分数判断胜负

9. 基于棋盘布局判断游戏是否终止<br>
```python 
    is_terminal(layout) -> str | None
```
- 若终止，返回胜方，即'W'或'E'；若不终止，返回None

10. 计算分数
```python
calculate_scores(layout) -> dict
```
- 返回计算分数{'W': (司令生命值, 士兵总生命值), 'E': (司令生命值, 士兵总生命值)}

11. 100轮次结束后，判断获胜方
```python
who_win(layout) -> str
```
- 如果游戏终止，返回获胜方（即is_terminal函数的结果）
- 如果100轮次时，游戏仍没有触发终止条件，则按胜负判定规则，比较司令生命值和其他士兵生命值，返回获胜方，即'W'/'E'

