"""


Version 0.5
Created on Sat Apr 20 13:29:19 2024
Author:Yunbo Sun
正式版本的内核,按照调整后的规则重写了一下,并预留出不少的拓展接口.
加入了Return_Board类作为返回给玩家的信息和一些内置的简单函数
加入了地图中央的安全区
改变了初始的英雄和属性
"""
from prettytable import PrettyTable
from collections import namedtuple
import time

class Profile:
    #不同种类英雄的档案 可扩展
    """
    这里是不同类型英雄的档案,在这修改数值
    """
    def __init__(self,name):
        self.defense=0
        if name=="Saber":
            # saber是我一开始的版本写的，就扔这吧（
            self.character="Saber"
            self.max_health=200 #最大生命值
            self.health=self.max_health
            self.attack=100 #攻击力
            self.defense=40 #防御力 目前版本不设置
            self.atk_range=1 #攻击范围
            self.move_range=1 #移动范围
            self.rebirth_time=3 #初始复活回合数
            
        elif name=="Lancer":
            #步兵
            self.character="Lancer"
            self.max_health=1800
            self.health=self.max_health
            self.attack=200
            #self.defense=60
            self.atk_range=1
            self.move_range=1
            self.rebirth_time=3 #具体复活时间有没有死亡次数惩罚?
        elif name=="Archer":
            #弓兵
            self.character="Archer"
            self.max_health=300
            self.health=self.max_health
            self.attack=500
            #self.defense=20
            self.atk_range=1
            self.move_range=1
            self.rebirth_time=4 
        elif name=="Rider":
            #骑兵
            self.character="Rider"
            self.max_health=800
            self.health=self.max_health
            self.attack=400
            #self.defense=0
            self.atk_range=2
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
        self.health=1000
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
class Flag(Entity):
    #懒得写了,我之后补上
    def __init__(self,owner,pos,name,score=1):
        super().__init__(owner,pos,name)
        self.type="Flag"
        self.character="Flag"
        self.owner=0
        self.score=score
class Game:
    #描述整个游戏进程
    def __init__(self):
        self.size=7
        #游戏地图的每一项是这个格子的实体名称
        self.game_map=[[[] for _ in range(greatest_size)] for __ in range(greatest_size)]
        #安全区位置清单,存储这些格子的坐标
        self.safe_area=[]
        self.safe_heal_hero=50
        self.safe_heal_base=20
        self.turns=0
        #实体用字典存储,键是实体在游戏内独一无二的名称
        self.entities={}
        self.scores=[0,0,0]
        self.winner=0
        #目前的算法是把没复活的所有英雄都移到地图外的一个地方等待复活.
        
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
        self.add_entity(Base(1,(0,0),"Base_p1"))
        self.add_entity(Base(2,(size-1,size-1),"Base_p2"))
        
        #在目前版本的游戏,加分塔被取消了
        #self.add_entity(Tower(0,((size-1)//2,(size-1)//2),"Tower_mid"))
        #self.add_entity(Tower(0,(0,size-1),"Tower_down"))
        #self.add_entity(Tower(0,(size-1,0),"Tower_up"))
        self.add_entity(Hero(1,(0,1),"Hero_p1_0",Profile("Rider")))
        self.add_entity(Hero(1,(1,0),"Hero_p1_1",Profile("Archer")))
        self.add_entity(Hero(1,(1,1),"Hero_p1_2",Profile("Lancer")))
        #目前版本的游戏,Saber换成了Rider(悲)
        self.add_entity(Hero(2,(size-1,size-2),"Hero_p2_0",Profile("Rider")))
        self.add_entity(Hero(2,(size-2,size-1),"Hero_p2_1",Profile("Archer")))
        self.add_entity(Hero(2,(size-2,size-2),"Hero_p2_2",Profile("Lancer")))
        
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
            t.add_row([i]+[self.show_process(x,i) for x in range(self.size) ])
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
        if self.entities[source].type=="Hero" and self.entities[source].moveable==True:
            if self.entities[source].atk_range>=mDist(self.entities[source].position,self.entities[target].position):
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
        """
        在游戏内执行player(int)玩家的命令Action[(),(),()]
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
                #print("Moved")
            elif order_name=="attack":
                delta=order_parameter
                position=(hero.position[0]+delta[0],hero.position[1]+delta[1])
                self.entity_attack_position(hero.name,position)
            self.update_map()

    def act_turn(self,player):
        """
        执行player的一个回合,复活时间和塔的加分进行一次结算,然后玩家进行一次操作
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
                
            elif self.entities[entity_name].type=="Tower":
                #每座塔的拥有者进行加分
                self.scores[self.entities[entity_name].owner]+=self.entities[entity_name].score

        """
        bot负责容纳不同玩家的AI，AI输入当前游戏的状态(打算给玩家的信息)
        并根据玩家自己的算法,返回命令格式的操作.
        """
        self.return_board=Return_Board(player,self)
        t0=time.time_ns()
        opt=self.bot[player-1](self.return_board)
        t1=time.time_ns()
        self.turn_time=t1-t0
        self.total_time[player]+=self.turn_time
        order=opt[0]
        storage=opt[1]
        self.storage[player-1]=storage
        
        """
        给玩家传入的是Game类的一个复制品,这样他们偷偷改参数也无法作用到Game本体
        

        """
        
        self.execute_order(player,order)
        #print(player,order)
        self.history.append(order)
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
            
class Return_Board:
    """
    返回给玩家的游戏信息
    并包含了一些实用函数
    """
    def __init__(self,player,Game_Core):
        
        
        self.board_size=Game_Core.size #棋盘大小
        self.player=player #自己是几号玩家
        self.opposite=1+player%2 #对方是几号玩家
        self.my_side=["G","W","E"][player] #自己阵营的名字
        self.board=Game_Core.game_map #棋盘,存储每个格子上面东西的名字
        self.my_hero=[{"health":Game_Core.get_hero(player,i).health,"position":Game_Core.get_hero(player,i).position,"character":Game_Core.get_hero(self.player,i).character} for i in range(3)]
        #己方英雄 包含血量位置和职业名字 的信息
        self.enemy_hero=[{"health":Game_Core.get_hero(self.opposite,i).health,"position":Game_Core.get_hero(self.opposite,i).position,"character":Game_Core.get_hero(self.opposite,i).character} for i in range(3)]
        #敌方英雄 同上
        self.turn_number=Game_Core.turns #当前回合数
        self.total_turn=Game_Core.total_turn #回合数上限
        self.scores=Game_Core.scores #分数
        self.action_history=Game_Core.history #历史动作
        self.storage=Game_Core.storage[player-1] #存储到的内容
    def get_profile(hero_number):
        #获得i号英雄的档案,用于查阅英雄的基本数据
        name_list=["Rider","Archer","Lancer"]
        profile=Profile(name_list[hero_number])
        return profile
    def get_block_info(self,x,y):
        #获得某个地图块上的单位的所属方和类型(用编号012表示)
        opt={"player":None,"type":None}
        if self.check_inmap((x,y)):
            block=self.board[x][y]
            if len(block)==0:
                return opt
            else:
                name=block[0].split("_")
                if name[0]=="Hero":
                    opt["player"]=int(name[1][1])
                    opt["type"]=int(name[2])
                    return opt
                elif name[0]=="Base":
                    opt["player"]=int(name[1][1])
                    opt["type"]="Base"
                    return opt
                    
        else:
            return False
    def check_inmap(self,position):
        #检测position位置是否在地图内
        try:
            x=position[0]
            y=position[1]
            if x>=0 and x<self.board_size and y>=0 and y<self.board_size:
                return True
            return False
        except:
            return False
    def check_moveable(self,hero_number,position):
        #检测hero_number能否移动到position位置 包含位置和移动和距离的合法性
        #默认是自己的英雄

        pos0=self.my_hero[hero_number]["position"]

        pos1=position
        move_range=self.get_profile(hero_number).move_range
        if self.check_inmap(pos1):
            if mDist(pos0,pos1)<=move_range:
                if mDist(pos0,pos1)==0 or (mDist(pos0,pos1)>0 and len(self.board[pos1[0]][pos1[1]])==0):
                    return True
        return False
    def check_attackable(self,hero_number,position):
        #检测自己的英雄攻击position位置的合法性
        pos0=self.my_hero[hero_number]["position"]
        pos1=position
        atk_range=self.get_profile(hero_number).atk_range
        if self.check_inmap(pos1):
            if mDist(pos0,pos1)<=atk_range:
                if self.board[pos1[0]][pos1[1]]!=None:
                    #如果那个位置没有的话
                    return True
        return False
def actionp1(board):
    """
    玩家1的操作是手操
    """
    opt=[]
    print(board.get_block_info(0,0))
    for i in range(3):
        inp=list(input().split())
        target=(int(inp[1]),int(inp[2]))
        opt.append((inp[0],target))
    
    return [opt,0]
def actionp2(board):
    """
    玩家2目前是什么也不做的愚蠢ai
    """
    #gamedata.turns+=1
    #因为gamedata传入的是复制品 所以它什么也做不了
    return [[("move",(-1,0)),("wait",(0,0)),("wait",(0,0))],0]


