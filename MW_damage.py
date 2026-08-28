import itertools
from functools import total_ordering

baseline_fighter: dict[str, list[float]] = {
    "attack_bonus":      [0,    4,    5,    6,    8,    9,    11,    11,    13,    14,    17,    18,    20,    22,    24,    25,    26,    27,    28,    28,    30],
    "strike_chance":     [0,   57,   59,   61,   63,   65,    67,    69,    71,    73,    75,    77,    79,    81,    83,    85,    85,    85,    85,    85,    85],
    "damage_per_strike": [0,  6.5,  6.5,  8.5, 11.5, 11.5,  12.5,    17,    17,    17,    19,    21,    24,  28.5,  29.5,  31.5,  31.5,  31.5,  31.5,  32.5,  33.5],
    "overall_damage":    [0, 3.71, 3.84, 5.19, 7.25, 7.48, 13.63, 19.21, 19.89, 20.57, 23.75, 32.76, 38.88, 47.88, 51.33, 56.70, 59.85, 59.85, 59.85, 61.75, 63.65]
}

unarmed_upgrades = [(1,6), (1,8), (2,6), (2,8), (3,6), (3,8), (4,6), (4,8)]
#                    3.5    4.5    7      9      10.5   13.5   14     18
#                          +1     +2.5   +2     +1.5   +3     +.5    +4

@total_ordering
class Mystic_Warrior:
    def __init__(self,level:int,dex:int,wis:int,upg:int,amulet:int,focus:bool):
        self.level = min(level, 20)
        self.dex = dex
        self.wis = wis
        self.upgrades = min(upg, 7)
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
    
    def increment(self) -> list['Mystic_Warrior']:
        l = [self.level+1]
        if self.level in {3,4,5,8,9,19}:
            dw = [(self.dex+1,self.wis), (self.dex,self.wis+1)] # either ability increases (4,20) or items (5,6,9,10)
        elif self.level == 11:
            dw = [(self.dex+2,self.wis+1), (self.dex+1,self.wis+2)] # both ability increase and items @12
        else:
            dw = [(self.dex,self.wis)]

        upg = [self.upgrades]
        if self.upgrades<7: upg.append(self.upgrades+1)
        if self.upgrades<6: upg.append(self.upgrades+2)

        a = [self.amulet]
        if self.amulet<5: a.append(self.amulet+1)
        
        f = [self.focus]
        if not self.focus: f.append(True)
        
        conditions = itertools.product(l, dw, upg, a, f)
        return sorted([Mystic_Warrior(i[0], i[1][0], i[1][1], i[2], i[3], i[4]) for i in conditions], reverse=True)

if __name__=="__main__":
    warriors = [Mystic_Warrior(1,2,2,0,0,False)]
    while True:
        last = warriors[-1]
        if last.level >= 20:
            break
        candidates = last.increment()[0:2]
        warriors.append(candidates[0] if candidates[0].increment()[0] >= candidates[1].increment()[0] else candidates[0])
        # not happy that we're calculating candidates[i].increment() twice (both in this pass, and on the first step of next pass)
        # may look for a better solution down the line
