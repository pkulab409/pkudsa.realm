"""
Version 0.5
Created on Sat Apr 20 13:29:19 2024
Author:Yunbo Sun
正式版本的内核,按照调整后的规则重写了一下,并预留出不少的拓展接口.
加入了Return_Board类作为返回给玩家的信息和一些内置的简单函数
加入了地图中央的安全区
改变了初始的英雄和属性

Version 1.0
Created on Sat May 11 1:04:19 2024
Author:Yunbo Sun
第二个版本的内核,目前和我们api的格式基本兼容,但可能在storage上略微不太一样
(详见main_game.py的说明)
再次调整了英雄的属性
删除了一些无关紧要的旧函数
调整了执行命令的格式和action一致

注意 一些违法操作在内核里面的反应结果是什么也不做,而不是报错
另外,内核没有禁止跨过棋子而移动2格,这部分的判定请以valid_action为准
你可以在最下方粘贴realm.py的valid_action和它后面的所有函数.以共方便

这个版本的本地内核可能会有Bug，请谨慎使用

可视化采用了PrettyTable输出字符,不乐意你自己改,谢谢.
"""
from prettytable import PrettyTable
from collections import namedtuple
import time
from enum import Enum
class ChessType(Enum):
        COMMANDER = 0
        WARRIOR = 1
        ARCHER = 3
        PROTECTOR = 2
Action = namedtuple("Action", "id mdr mdc adr adc")
hero_num_list={ChessType.COMMANDER:-1,ChessType.ARCHER:0,ChessType.PROTECTOR:1,ChessType.WARRIOR:2}
_ChessType_id: dict[str, ChessType] = {"Base": ChessType.COMMANDER, "Archer": ChessType.ARCHER, "Protector": ChessType.PROTECTOR,
                                     "Warrior": ChessType.WARRIOR}
_inGame_id: dict[ChessType , str] ={ChessType.COMMANDER:"Base", ChessType.ARCHER:"Archer", ChessType.PROTECTOR:"Protector",
                                     ChessType.WARRIOR:"Warrior"}
class Profile:
    #不同种类英雄的档案 可扩展
    """
    这里是不同类型英雄的档案,在这修改数值
    """
    def __init__(self,name):
        self.defense=0
        if name=="Saber":
            # saber是我一开始的版本写的，就扔这吧（
            # 其实最初版本内核是master&saber&archer&lancer,我看Fate太多导致的
            self.character="Saber"
            self.max_health=200 #最大生命值
            self.health=self.max_health
            self.attack=100 #攻击力
            self.defense=40 #防御力 目前版本不设置
            self.atk_pos=[]#目前版本用来描述可攻击格子和自己坐标差的列表
            self.atk_range=1 #攻击范围 目前版本被上面替代
            self.move_range=1 #移动范围
            self.rebirth_time=3 #初始复活回合数 在目前版本中已经被删除了
            
        elif name=="Protector":
            #盾兵
            self.character="Protector"
            self.max_health=1400
            self.health=self.max_health
            self.attack=150
            #self.defense=60
            self.atk_range=1
            self.atk_pos=[(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
            self.move_range=1
            self.rebirth_time=3 #具体复活时间有没有死亡次数惩罚?
        elif name=="Archer":
            #弓兵
            self.character="Archer"
            self.max_health=700
            self.health=self.max_health
            self.attack=250
            #self.defense=20
            self.atk_pos=[(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1),(2,0),(-2,0),(0,2),(0,-2)]
            self.atk_range=2
            self.move_range=1
            self.rebirth_time=4 
        elif name=="Warrior":
            #骑兵
            self.character="Warrior"
            self.max_health=1000
            self.health=self.max_health
            self.attack=200
            self.atk_pos=[(0,1),(1,0),(0,-1),(-1,0)]
            #self.defense=0
            self.atk_range=1
            self.move_range=2
            self.rebirth_time=5
def mDist(p1,p2):
    
    #计算两个点的曼哈顿距离
    #p1 p2是(int,int)元组
    try:
        return abs(p1[0]-p2[0])+abs(p1[1]-p2[1])
    except:
        return -1
def rebirth_time(death_count):
    """
    计算第death_count(int)次死亡后,复活需要等待的回合数,数值设置可以参考一些moba游戏
    """
    return 2*death_count**2

"""
actions列表存储两个玩家各自的策略函数,它不能塞到Game里面,否则会被对方所读取
"""
actions=[]
"""
在下面定义一些全局变量
"""
tomb_position=(10,10)
greatest_size=100
class Entity:
    #父类 地图上的东西 包括英雄 水晶 和塔
    def __init__(self,owner=0,pos=(0,0),name=""):
        """
        owner(int) 该实体的拥有者 0为中立 1和2分别为2个玩家
        pos((int,int)) 该实体的初始位置
        name(string) 该实体的名称,在一局游戏内用这个独一无二的名称进行索引
        """
        #该实体能否移动
        self.moveable=False
        #该实体的名称,这是它在游戏内的唯一标识!
        self.name=name
        #该实体可以移动的范围(曼哈顿距离)
        self.moverange=0
        #该实体的位置
        self.position=pos
        #该实体的类型
        self.type="Mob"
        self.character="Mob"
        #该实体的拥有者 0为中立 1和2分别为玩家
        self.owner=owner
        #该实体的血量
        self.max_health=1
        self.health=1 
        #该实体的防御
        self.defense=0
        #该实体是否允许被穿过
        self.passable=True
        
    def recover(self,value):
        self.health=min(self.max_health,self.health+value)
    def hit(self,source_entity):
        #受到实体source的一次攻击,攻击力默认为source的攻击力
        effective_atk=source_entity.attack
        if source_entity.character=="Archer" and self.character=="Lancer":
            effective_atk*=2
        elif source_entity.character=="Lancer" and self.character=="Base":
            effective_atk*=3
        self.health-=max(0,effective_atk-self.defense)
    def move(self,delta):
        #实体移动某段距离
        try:
            position=(self.position[0]+delta[0],self.position[1]+delta[1])
            return self.moveto(position)
        except:
            print("Wrong Input")
            return "Wrong Input"
    def moveto(self,position):
        #实体移动到某个位置,进行距离是否合法的判断
        if mDist(self.position,position)<=self.move_range:
            self.position=position
            return True
        else:
            print("Out of Range")
        """
        if self.moveable:
            try:
                if mDist(self.position,position)<=self.move_range:
                    self.position=position
                    return True
                else:
                    return False
            except:
                return False
        else:
            return False
        """
class Hero(Entity):
    #玩家可操作的英雄
    def __init__(self,owner,pos,name,profile):
        super().__init__(owner,pos,name)
        #英雄在没死时可移动
        
        self.moveable=True
        #英雄是Hero
        self.type="Hero"
        self.max_health=profile.max_health
        self.health=self.max_health
        self.attack=profile.attack
        self.defense=profile.defense
        self.atk_range=profile.atk_range
        self.move_range=profile.move_range
        self.character=profile.character
        self.rebirth_time=profile.rebirth_time
        self.atk_pos=profile.atk_pos
        #复活时的位置
        self.base_position=pos
        self.tomb_position=tomb_position
    
        
        #英雄默认不能被穿过
        self.passable=False
        
        #复活还需要等待的时间
        self.rebirth=0
        #死亡次数
        self.death_count=0
        #击杀数
        self.kill_count=0
        #连续击杀数
        self.continue_kill_count=0
        pass
    
        
    def hit(self,source_entity):
        super().hit(source_entity)
        """
        英雄被杀死后会在坟墓的位置等待复活
        """
        if self.health<=0:
            self.death_count+=1
            #self.rebirth=rebirth_time(self.death_count)
            self.rebirth=self.rebirth_time #目前版本复活cd没有死亡数惩罚
            #self.health=self.max_health
            self.health=0
            self.position=self.tomb_position
            self.moveable=False
            self.continue_kill_count=0
            source_entity.kill_count+=1
            source_entity.continue_kill_count+=1

class Base(Entity):
    #玩家大本营(水晶)
    def __init__(self,owner,pos,name):
        super().__init__(owner,pos,name)
        self.type="Base"
        self.character="Base"
        self.owner=owner
        self.health=1600
        self.max_health=float("inf")
        #水晶不能被穿过
        self.passable=False
        self.rebirth=0
        pass
class Tower(Entity):
    #中间的可占领的塔
    """
    我自己最初写代码时设计的塔,拥有一定的生命值,可以被攻击.
    当它被杀死时,它会立刻回满血量,同时所有权转移到击杀者的所属方.
    塔的拥有者会持续获得分数
    """
    def __init__(self,owner,pos,name,score=1):
        super().__init__(owner,pos,name)
        self.type="Tower"
        self.character="Tower"
        #中间塔初始为中立
        self.owner=0
        #这座塔的拥有者每回合会加多少分数
        self.score=score
        self.health=200
        self.max_health=200
        #塔能被穿过
        self.passable=True
        pass
    def hit(self,source_entity):
        super().hit(source_entity)
        if self.health<=0:
            self.health=self.max_health
            self.owner=source_entity.owner

class Game:
    #描述整个游戏进程
    def __init__(self):
        self.size=8
        #游戏地图的每一项是这个格子的实体名称
        self.game_map=[[[] for _ in range(greatest_size)] for __ in range(greatest_size)]
        #安全区位置清单,存储这些格子的坐标
        self.safe_area=[(3,3),(3,4),(4,3),(4,4)]
        self.safe_heal_hero=25
        self.safe_heal_base=25
        self.turns=0
        #实体用字典存储,键是实体在游戏内独一无二的名称
        self.entities={}
        self.scores=[0,0,0]
        self.winner=0
        #目前的算法是把没复活的所有英雄都移到地图外的一个地方等待复活.但因为目前没有复活机制所以就暂时别管
        
        self.return_board=None

        self.total_turn=60 #总回合
        self.history=[] #历史操作存储
        self.storage=[{},{},{}]
        self.turn_time=0 #本回合所用时间
        self.total_time=[0,0,0] #玩家时间存储
    def add_entity(self,entity):
        self.entities[entity.name]=entity
        """
        if entity.type=="Hero":
            self.entities[entity.name].base_position=((entity.owner-1)*(self.size-1),(entity.owner-1)*(self.size-1))
        """
    def load_ai(self,bot1,bot2):
        self.bot=[bot1,bot2]
        return True
    def setup(self):
        """
        创建一局新游戏,添加水晶,塔和双方英雄
        """
        self.safe_area=[(3,3),(3,4),(4,3),(3,4)]
        
        size=self.size
        self.add_entity(Base(1,(size-1,0),"Base_p1"))
        self.add_entity(Base(2,(0,size-1),"Base_p2"))
        
        #在目前版本的游戏,加分塔被取消了
        #self.add_entity(Tower(0,((size-1)//2,(size-1)//2),"Tower_mid"))
        #self.add_entity(Tower(0,(0,size-1),"Tower_down"))
        #self.add_entity(Tower(0,(size-1,0),"Tower_up"))
        self.add_entity(Hero(1,(size-1,1),"Hero_p1_0",Profile("Archer")))
        self.add_entity(Hero(1,(size-2,1),"Hero_p1_1",Profile("Protector")))
        self.add_entity(Hero(1,(size-2,0),"Hero_p1_2",Profile("Warrior")))
        #目前版本的游戏,Saber换成了Rider(悲) 草现在改名为Warrior了
        self.add_entity(Hero(2,(0,size-2),"Hero_p2_0",Profile("Archer")))
        self.add_entity(Hero(2,(1,size-2),"Hero_p2_1",Profile("Protector")))
        self.add_entity(Hero(2,(1,size-1),"Hero_p2_2",Profile("Warrior")))
        
    def update_map(self):
        """
        刷新目前的地图,把地图格子放上实体
        """
        self.game_map=[[[] for _ in range(greatest_size)] for __ in range(greatest_size)]
        for entity_name in self.entities:
            entity=self.entities[entity_name]
            x=entity.position[0]
            y=entity.position[1]
            self.game_map[x][y].append(entity.name)
    def show_map(self):
        """
        显示地图,只在作者用文字版调试时有用
        """
        t=PrettyTable()
        t.field_names = ["行列"]+[i for i in range(self.size)]
        for i in range(self.size):
            t.add_row([i]+[self.show_process(i,x) for x in range(self.size) ])
        print(t)
    def show_process(self,i,j):
        """
        文字显示地图时的临时处理函数,只在作者文字调试时有用
        """
        block=self.game_map[i][j]
        opt=""
        for entity_name in block:
            opt=opt+self.entities[entity_name].character+str(self.entities[entity_name].owner)+"\n"
            opt=opt+str(self.entities[entity_name].health)+"/"+str(self.entities[entity_name].max_health)+"\n"
        return opt
    def get_base(self,player):
        name="Base_p"+str(player)
        return self.entities[name]
    def get_hero(self,player,num):
        #从玩家和编号得到英雄
        """
        player(int) 1或2 玩家号
        num(int) 0或1或2 英雄编号
        """
        name="Hero_p"+str(player)+"_"+str(num)
        #print(name)
        return self.entities[name]

    def get_hero_name(self,player,num):
        try:
            name="Hero_p"+str(player)+"_"+str(num)
            return name
        except:
            return False
    def position_legal(self,position):
        """
        判断一个位置的移动是否合法
        首先看在不在地图内,再考虑有没有不能通过的实体
        """
        try:
            if position[0]>=0 and position[0]<self.size and position[1]>=0 and position[1]<self.size:
                for entity_name in self.game_map[position[0]][position[1]]:
                    if not self.entities[entity_name].passable:
                        print("Blocked by",self.entities[entity_name].name)
                        return False
                return True
            else:
                print("Out of map")
                return False
        except:
            print("Other Errors")
            return False

    def entity_move_to(self,entity_name,target_position):
        """
        把名字为entity_name(string)的实体移动到target_position((int,int))的位置
        """
        if self.position_legal(target_position):
            if self.entities[entity_name].moveto(target_position):
                return True
        else:
            print("Wrong Move")
        return False
    def entity_move(self,entity_name,delta):
        """
        移动这样的距离
        """
        pos0=self.entities[entity_name].position
        target=(pos0[0]+delta[0],pos0[1]+delta[1])
        return self.entity_move_to(entity_name,target)
    def entity_attack(self,source,target):
        """
        名字为source(string)的实体向名字为target(string)的实体发动攻击
        如果超过射程默认输出False攻击失败
        """
        sp=self.entities[source].position
        tp=self.entities[target].position
        delta=(tp[0]-sp[0],tp[1]-sp[1])
        if self.entities[source].type=="Hero" and self.entities[source].moveable==True:
            if delta in self.entities[source].atk_pos:
                #攻击成功时,目标进行受击的伤害判定
                self.entities[target].hit(self.entities[source])
            else:
                return False
        else:
            return False
    def entity_attack_position(self,source,position):
        for names in self.game_map[position[0]][position[1]]:
            self.entity_attack(source,names)
            #默认攻击这个块内的所有实体
    def execute_order(self,player,orders):
        #这个函数目前暂时没有用了
        """
        在游戏内执行player(int)玩家的命令action[(),(),()]
        order格式:(动作类型,动作参数,目前参数是(dx,dy))
        也可以直接判断命令的格式 如果不符合就直接pass掉
        
        
        """

        for i in range(3):
                
            hero=self.get_hero(player,i)
            single_order=orders[i]
            order_name=single_order[0]
            if order_name=="wait":
                continue      
            order_parameter=single_order[1]
            if order_name=="move":
                delta=order_parameter
                self.entity_move(hero.name,delta)
            elif order_name=="attack":
                delta=order_parameter
                position=(hero.position[0]+delta[0],hero.position[1]+delta[1])
                self.entity_attack_position(hero.name,position)
            self.update_map()

    def act_turn(self,player):
        """
        执行player的一个回合
        """
        
        self.return_board=Return_Board(player,self)
        t0=time.time_ns()
        opt=self.bot[player-1](self.return_board)
        t1=time.time_ns()
        self.turn_time=t1-t0
        self.total_time[player]+=self.turn_time
        
        if isinstance(opt,list):
            action=opt[0]
            
            storage=opt[1]
            self.storage[player-1]=storage
        else:
            action=opt
           
        """
        在此处理移动
        """
        if action:
            
            hero_num=hero_num_list[action.id]
            hero=self.get_hero(player,hero_num)
            if action.mdr or action.mdc:
                delta=(action.mdr,action.mdc)
                self.entity_move(hero.name,delta)
            self.update_map()
        
        """
        在此处理回血
        """
        
        for entity_name in self.entities:
            if self.entities[entity_name].type=="Hero":
                
                if self.entities[entity_name].position in self.safe_area:
                    self.entities[entity_name].recover(self.safe_heal_hero)
                    base_name="Base_p"+str(self.entities[entity_name].owner)
                    self.entities[base_name].recover(self.safe_heal_base)
                #处理复活的模块,暂时不启用
                """ 
                if self.entities[entity_name].rebirth>0:
                    #print(self.entities[entity_name].name,self.entities[entity_name].rebirth)
                    self.entities[entity_name].rebirth-=1
                    
                    #如果存在重生功能那么应该如此实现,即把实体放到一个地图外的地方并让它无法移动
                    if self.entities[entity_name].rebirth==0:
                        base_position=self.entities[entity_name].base_position
    
                        if len(self.game_map[base_position[0]][base_position[1]])==0: #如果复活后的位置没有任何实体占用
                            self.entities[entity_name].position=base_position     
                            self.entities[entity_name].moveable=True
                        else:
                            self.entities[entity_name].rebirth+=1 #等着
                            
                            continue
                """
            """
            这部分是因为在原始版本,我们需要占领能加分的防御塔,但现在我们不再需要这个功能了
            elif self.entities[entity_name].type=="Tower":
                #每座塔的拥有者进行加分
                self.scores[self.entities[entity_name].owner]+=self.entities[entity_name].score
                
            """

        """
        bot负责容纳不同玩家的AI，AI输入当前游戏的状态(打算给玩家的信息)
        并根据玩家自己的算法,返回命令格式的操作.
        """

        
        if action:
            hero_num=hero_num_list[action.id]
            hero=self.get_hero(player,hero_num)
            if action.adr or action.adc:
                atk_position=(hero.position[0]+action.adr,hero.position[1]+action.adc)
                self.entity_attack_position(hero.name,atk_position)
            self.update_map()
            
        
        #self.execute_order(player,order)
        #print(player,order)
        self.history.append(action)
        #执行玩家的命令
        
        
        
        self.show_map()
        #self.turns+=1
        
    def endgame(self):
        """
        结束游戏的条件判定
        """

        if self.entities["Base_p1"].health<=0:
            self.winner=2
            return True
        if self.entities["Base_p2"].health<=0:
            self.winner=1
            return True
        if self.turns>=self.total_turn:
            #计分胜利被暂时停用
            """
            if self.scores[1]>self.scores[2]:
                self.winner=1
            else:
                self.winner=2
            """
            total_hp=[0,0,0]
            for entity_name in self.entities:
                total_hp[self.entities[entity_name].owner]+=max(self.entities[entity_name].health,0)
            if total_hp[1]>total_hp[2]:
                self.winner=1
            elif total_hp[1]<total_hp[2]:
                self.winner=2
            else:
                #如果剩余hp相等那就看时间
                if self.total_time[1]<self.total_time[2]:
                    self.winner=1
                else:
                    self.winner=2
            return True
        return False
    def game_process(self):
        self.turns=0
        self.update_map()
        self.show_map()
        while not self.endgame():
            self.act_turn(self.turns%2+1)
            self.turns+=1
        print("Winner is player",str(self.winner))
    def get_map(self):
        return self.game_map
    

"""
=======================================================================================
这上面的是内核，下面的是它适应到API格式的接口.
=======================================================================================

"""





class Chess:
    def __init__(self, side: str, id: ChessType, hp: int, pos: tuple[int, int]):
        self.id: ChessType = id  # 棋子ID, 如：ChessType.COMMANDER
        self.hp: int = hp  # 棋子当前剩余血量
        self.side: str = side  # 如："W"
        self.pos: tuple[int, int] = pos  # 棋子当前位置(row, col)
class Return_Board:
    """
    返回给玩家的游戏信息
    并包含了一些实用函数
    """
    def __init__(self,player,Game_Core):
        
        
        self.board_size=Game_Core.size #棋盘大小
        self.player=player #自己是几号玩家 1和2数字编号
        self.opposite=1+player%2 #对方是几号玩家 1和2数字编号
        self.my_side=["G","W","E"][player] #自己阵营的名字 是api里面的玩家阵营格式
        self.enemy_side=["G","W","E"][self.opposite]
        
        self.layout: list[list[Optional[Chess]]] = [[None] * 8 for _ in range(8)]
        my_hp_sum, enemy_hp_sum = 0, 0
        """
        这部分的代码是我把游戏内核的信息打包成api要求的chess类
        然后扔进这个layout里面
        """
        
        #self.board=Game_Core.game_map #棋盘,存储每个格子上面东西的名字 现在被转换成我们Pkudsa的layout
        for i in range(3):
            hero=Game_Core.get_hero(self.player,i)
            if not hero.moveable:
                continue
            my_chess=Chess(self.my_side,_ChessType_id[hero.character],hero.health,hero.position)
            self.layout[hero.position[0]][hero.position[1]]=my_chess
            my_hp_sum+=hero.health
        base=Game_Core.get_base(self.player)
        my_base_chess=Chess(self.my_side,_ChessType_id[base.character],base.health,base.position)
        self.layout[base.position[0]][base.position[1]]=my_base_chess
        for i in range(3):
            hero=Game_Core.get_hero(self.opposite,i)
            if not hero.moveable:
                continue
            my_chess=Chess(self.enemy_side,_ChessType_id[hero.character],hero.health,hero.position)
            self.layout[hero.position[0]][hero.position[1]]=my_chess
            enemy_hp_sum+=hero.health
        base=Game_Core.get_base(self.opposite)
        enemy_base_chess=Chess(self.enemy_side,_ChessType_id[base.character],base.health,base.position)
        self.layout[base.position[0]][base.position[1]]=enemy_base_chess
        #self.my_hero=[{"health":Game_Core.get_hero(player,i).health,"position":Game_Core.get_hero(player,i).position,"character":Game_Core.get_hero(self.player,i).character} for i in range(3)]
        #己方英雄 包含血量位置和职业名字 的信息
        #self.enemy_hero=[{"health":Game_Core.get_hero(self.opposite,i).health,"position":Game_Core.get_hero(self.opposite,i).position,"character":Game_Core.get_hero(self.opposite,i).character} for i in range(3)]
        #敌方英雄 同上
        self.point: dict[str, tuple[float, float]] = {
            self.my_side: (my_base_chess.hp, my_hp_sum),
            self.enemy_side: (enemy_base_chess.hp, enemy_hp_sum)
        }
        self.chess_profile: dict[ChessType, tuple] = {ChessType.COMMANDER: (0, 1600), ChessType.WARRIOR: (200, 1000),
                                                      ChessType.ARCHER: (250, 700), ChessType.PROTECTOR: (150, 1400)}
        
        self.turn_number=Game_Core.turns #当前回合数
        self.total_turn=Game_Core.total_turn #回合数上限
        self.scores=Game_Core.scores #分数
        self.action_history=Game_Core.history #历史动作
        self.storage=Game_Core.storage[player-1] #存储到的内容

    

def get_chess_profile(id: ChessType) -> dict:
    """
    因为本地端无法调用腾讯api的信息,所以这个函数需要修改
    """

    chess_name=_inGame_id[id]
    my_profile = Profile(chess_name) 
    return {'atk': my_profile.attack, 'atk_pos': my_profile.atk_pos.copy(), 'init_hp': my_profile.max_health,
            'move_range': my_profile.move_range}

"""
原则上说,在这后面完全可以支持我们realm里面valid_action以及其以后的所有辅助函数
因为这些函数都是在layout基础上实现的,内核是腾讯的还是我的都没有区别
"""


