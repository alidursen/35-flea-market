import itertools
import functools
from typing import Callable
from pprint import pprint

MAP_reduction = 20 # percent, on multiple attacks
initial_chance = 54 # percent, at level 0
chance_increase = 2 # percent, hit chance versus level increase
multiple_attack_frequency = 5 # how many levels grant +1 attack
max_chance = 80 # percent
level_diff_soft_limit = 5 # !! if changed, change level_diff() accordingly !!
level_diff_hard_limit = 9

def level_diff(n:int) -> int:
    """shows the effect of dfd-atk level difference to hit chances"""
    if n > level_diff_hard_limit: return -1000 # or some other "impossibility"
    if n > level_diff_soft_limit: return level_diff(level_diff_soft_limit)
    if n== level_diff_soft_limit: return -30
    if n== 3: return -20
    if n>= 0: return -5*n
    if n < 0: return -level_diff(-n)
    return 0 # to please the linter gods!

def multiplier(hit_chances: list[float]) -> list[float]:
    """given a vector of success probabilities [p1, p2 ... pn]
    where pi is the chance of succeeding on i'th attempt,
    returns a vector of probabilities [q0, q1 ... qn]
    where qi is the chance of obtaining i overall successes.
     
    note that sum(qi)=1 but no such condition exists for pi
    because they are independent events."""

    le = len(hit_chances)
    thc = [0.] * (le+1)
    for i in itertools.product((1,0), repeat=le):
        thc[sum(i)] += functools.reduce(
            lambda a, t: a * (t[1] if t[0]==1 else (1-t[1])),
            zip(i, hit_chances),
            1
        )
    return thc

def hit_chances(n: int, attacks:int) -> list[float]: 
    """n is the hit chance (in percentage decimals due to rounding issues)
    
    given initial chance n, lists [n, n-MAP, n-2MAP ...] until exhaustion"""
    t = []
    while n>0 and attacks>0:
        t.append(min(100,n)/100)
        n -= MAP_reduction
        attacks -= 1
    return t

multiplied_hit_chances: Callable[[int, int, int], list[float]] = lambda atk, dfd, extra_attacks: multiplier(
    hit_chances(
        min(max_chance, initial_chance+chance_increase*atk) + level_diff(dfd-atk),
        extra_attacks+1
    )
)

# returns the expected number of successes for a given overall success probability vector
strike_counter: Callable[[list[float]], float] = lambda li: functools.reduce(lambda s, i: s+(i[0]*i[1]), zip(li, [0,1,2,3,4,5]), 0)


if __name__=="__main__":
    onslaught = [
        [list(map(lambda x: round(x, 8), multiplied_hit_chances(atk_level, def_level, atk_level//multiple_attack_frequency))) for def_level in range(1,21)]
        for atk_level in range(1,21)
    ]

    singles = [
        [round(1-multiplied_hit_chances(atk_level, def_level, 0)[0], 8) for def_level in range(1,21)]
        for atk_level in range(1,21)
    ]

    strikes = [[round(strike_counter(j), 6) for j in i] for i in onslaught]
