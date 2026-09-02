import itertools
from functools import total_ordering, reduce
from typing import Callable

baseline_fighter: dict[str, list[float]] = {
    "attack_bonus":      [0,    4,    5,    6,    8,    9,    11,    11,    13,    14,    17,    18,    20,    22,    24,    25,    26,    27,    28,    29,    30],
    "strike_chance":     [0,   57,   59,   61,   63,   65,    67,    69,    71,    73,    75,    77,    79,    81,    83,    85,    85,    85,    85,    85,    85],
    "damage_per_strike": [0,  6.5,  6.5,  8.5, 11.5, 11.5,  12.5,    17,    17,    17,    19,    21,    24,  28.5,  29.5,  31.5,  31.5,  31.5,  31.5,  31.5,  33.5],
    "overall_damage":    [0, 3.71, 3.84, 5.19, 7.25, 7.48, 13.63, 19.21, 19.89, 20.57, 23.75, 32.76, 38.88, 47.88, 51.33, 56.70, 59.85, 59.85, 59.85, 59.85, 63.65]
}

unarmed_upgrades = [(1,6), (1,8), (1,10), (2,6), (2,8), (3,6), (2,10), (3,8), (4,6), (4,8)]
#                    3.5    4.5    5.5     7      9      10.5   11      13.5   14     18
#                          +1     +1      +1.5   +2     +1.5   +.5     +2.5   +.5    +4

@total_ordering
class Mystic_Warrior:
    def __init__(self,level:int,dex:int,wis:int,upg:int,amulet:int,focus:bool):
        self.level = min(level, 20)
        self.dex = dex
        self.wis = wis
        self.upgrades = min(upg, 9)
        self.amulet = amulet
        self.focus = focus

        self.atk = self.level+self.dex+self.amulet+(1 if self.focus else 0)
        self.dmg = unarmed_upgrades[self.upgrades][0]*(unarmed_upgrades[self.upgrades][1]+1)/2.+self.wis+self.amulet

        _base = baseline_fighter["strike_chance"][self.level]+5*(self.atk-baseline_fighter["attack_bonus"][self.level])
        self.chances = [_base-10, _base-10]
        if self.level >= 6:
            self.chances.append(_base-35)
        if self.level >= 11:
            self.chances.append(_base-35)
            self.chances.append(_base-60)
        if self.level >= 16:
            self.chances.append(max(_base-85, 5))

        self.total_dmg = self.dmg*sum(self.chances)/100 # ... linearity of expectation
        self.compared = abs(self.total_dmg - baseline_fighter["overall_damage"][self.level])
    
    def __lt__(self, other:'Mystic_Warrior'):
        return self.compared > other.compared
    
    def __str__(self) -> str:
        return 'level:{0},\ndex:{1}, wis:{2},\nunarmed:{3}d{4}, amulet:+{5},\nweapon focus: {6}'.format(
            self.level, self.dex, self.wis, unarmed_upgrades[self.upgrades][0], unarmed_upgrades[self.upgrades][1], self.amulet, self.focus)
    
    def __key(self):
        return self.level, self.dex, self.wis, self.upgrades, self.amulet, self.focus
    
    def __hash__(self) -> int:
        return hash(self.__key())
    
    def increment(self) -> list['Mystic_Warrior']:
        l = [self.level+1]

        if self.level in {3,4,5,8,9,19}:
            dw = [(self.dex+1,self.wis), (self.dex,self.wis+1)] # either ability increases (4,20) or items (5,6,9,10)
        elif self.level == 11:
            dw = [(self.dex+2,self.wis+1), (self.dex+1,self.wis+2)] # both ability increase and items @12
        else:
            dw = [(self.dex,self.wis)]

        upg = [self.upgrades]
        if self.upgrades<9: upg.append(self.upgrades+1)
        if self.upgrades<8: upg.append(self.upgrades+2)

        a = [self.amulet]
        if self.amulet<5: a.append(self.amulet+1)
        
        f = [self.focus]
        if not self.focus: f.append(True)
        
        return sorted(
            [Mystic_Warrior(i[0], i[1][0], i[1][1], i[2], i[3], i[4]) for i in itertools.product(l, dw, upg, a, f)],
            reverse=True
        )
    
    def diff(self, successor:'Mystic_Warrior'):
        r = dict()
        if successor.level-self.level != 0:
            r["level"] = successor.level-self.level
        if successor.upgrades-self.upgrades != 0:
            r["upgrades"] = successor.upgrades-self.upgrades
        if successor.dex-self.dex != 0:
            r["dex"] = successor.dex-self.dex
        if successor.wis-self.wis != 0:
            r["wis"] = successor.wis-self.wis
        if successor.amulet-self.amulet != 0:
            r["amulet"] = successor.amulet-self.amulet
        if successor.focus and not self.focus:
            r["focus"] = True
        return r

def proc1(metric: Callable[[Mystic_Warrior], float]):
    """
    Returns a binary tree and an index.
    
    On tree, each node represents a character level and feature set
    and being child of a node corresponds to an improvement of
    features. When a level-feature set has more than two possible
    improvements, those who score highest w.r.t. class' inner sorting
    (that is, comparison against baseline fighter's overall damage at that level)
    are prioritized.

    The returned index is the location of optimal solution according to a given
    metric. To find parents and follow the tree up to the root, simply divide
    the index by 2 at each step.
    """
    warriors: dict[int, list[tuple[Mystic_Warrior, float]|None]] = dict()
    init = Mystic_Warrior(1,2,2,0,0,False)
    warriors[1] = [(init, metric(init))]
    for i in range(2, 21):
        # print("working on:", i)
        warriors[i] = []
        for j in warriors[i-1]:
            if j is None:
                warriors[i].extend([None, None])
            else:
                candidates = j[0].increment()
                warriors[i].append((candidates[0], j[1]+metric(candidates[0])))
                if len(candidates)>1:
                    warriors[i].append((candidates[1], j[1]+metric(candidates[1])))
                else:
                    warriors[i].append(None)
    # we end up with around 1million elements, with half million (2^19=524,288) on the final layer

    # print("working on: finding minimum")
    min_sum = [0, float('inf')]
    for i in range(2**19):
        a = warriors[20][i] 
        if a is None:
            continue
        if a[1]<min_sum[1]:
            min_sum = [i, a[1]]

    # for i in range(19):
    #     c: tuple[Mystic_Warrior, float] = warriors[i+1][min_sum[0]//(2**(19-i))]
    #     n = warriors[i+2][min_sum[0]//(2**(18-i))]
    #     if len(c[0].diff(n[0])) > 1:
    #         print(c[0].diff(n[0]))
    #     print("error squared sum:", n[1])
    #     print('----|----')
    return warriors, min_sum[0]

def proc2(p:list[Mystic_Warrior]):
    print(reduce(lambda t, s: t+s.compared**2, p, 0))
    print(sum(map(lambda i:i.total_dmg - baseline_fighter["overall_damage"][i.level], p)))
    print('--------')
    for i in p:
        print(i.total_dmg - baseline_fighter["overall_damage"][i.level])

if __name__=="__main__":
    # warriors, min_index = proc1(lambda x: (x.compared)**2)

    # through procedure1 one gets the optimal solution of:
    # {'level': 4, 'wis': 1, 'amulet': 1}
    # {'level': 5, 'dex': 1}
    # {'level': 6, 'dex': 1, 'amulet': 1}
    # {'level': 7, 'amulet': 1}
    # {'level': 8, 'upgrades': 1}
    # {'level': 9, 'dex': 1}
    # {'level':10, 'upgrades': 1, 'dex': 1}
    # . 
    # {'level':12, 'dex': 2, 'wis': 1}
    # {'level':13, 'upgrades': 2}
    # {'level':14, 'upgrades': 1}
    # {'level':15, 'focus': True}
    # {'level':16, 'upgrades': 1}
    # ... 
    # {'level':20, 'wis': 1}
    # 
    # error-squared sum: 8.442125, error sum: 5.985
    #  
    # to end up at Mystic_Warrior(20, dex:8, wis:5, unarmed: 2d10, amulet: +3, Weapon Focus: True)
    # while we can accept the end result, progress has issues:
    # 1. wis is +2 from ASI, +2 from item while dex is +1 ASI, +4 item
    # 2. amulets are too clumped: 4,6,7
    # 3. damage upgrades are too clumped: 8,10,13,14,16
    # 
    # instead try 

    proc2([
        Mystic_Warrior(1, 2, 2, 0, 0, False),
        Mystic_Warrior(2, 2, 2, 0, 0, False),
        Mystic_Warrior(3, 2, 2, 0, 0, False),
        Mystic_Warrior(4, 3, 2, 1, 1, False),
        Mystic_Warrior(5, 3, 3, 1, 1, False),
        Mystic_Warrior(6, 4, 3, 1, 1, False),
        Mystic_Warrior(7, 4, 3, 2, 2, False),
        Mystic_Warrior(8, 4, 3, 2, 2, False),
        Mystic_Warrior(9, 5, 3, 2, 2, False),
        Mystic_Warrior(10,5, 4, 2, 3, False),
        Mystic_Warrior(11,5, 4, 2, 3, False),
        Mystic_Warrior(12,7, 5, 2, 3, False),
        Mystic_Warrior(13,7, 5, 3, 4, False),
        Mystic_Warrior(14,7, 5, 3, 4, True ),
        Mystic_Warrior(15,7, 5, 4, 4, True ),
        Mystic_Warrior(16,7, 5, 4, 4, True ),
        Mystic_Warrior(17,7, 5, 4, 4, True ),
        Mystic_Warrior(18,7, 5, 4, 4, True ),
        Mystic_Warrior(19,7, 5, 4, 4, True ),
        Mystic_Warrior(20,7, 6, 4, 4, True ),
    ])

    # to end up with Mystic_Warrior(20, dex:7, wis:6, unarmed: 2d8, amulet: +4, Weapon Focus: True) with
    # error-squared sum: 17.458475, error sum: 4.755
    # 
    # some benefits of this progression scheme:
    # 1. doesn't limit amulets to +5
    # 2. individual strikes are more "balanced" towards flat bonus (2d8+10 vs 2d10+8)
    # 
    # one potential issue is how unarmed damage of 2d6 is only available for 2 levels (13 and 14) 
