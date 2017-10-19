# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A random mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#

import random
from functools import partial

from ecosystem.agents import Agent
from ecosystem.network import Network, MotorNetwork

from toolz.curried import do
from toolz.functoolz import compose
from gzutils.gzutils import Logging, unpack

from sea import Sea, Song, Squid
from random_mom_and_calf_config import mom_start_pos, calf_start_pos, OPTIONS


# Setup logging
# =============

DEBUG_MODE = True
l = Logging('random_mom_and_calf2', DEBUG_MODE)

# Mom that moves by random until squid is found. Move forward when there is
# squid and sing. When there is no squid, move forward, upward or dive
# randomly.
#
# The network consists of one `SENSOR` for `Squid` and three `RAND` (random) nodes
# each with a probability of 0.3 of being True. The eight states the three
# RAND nodes generate are mapped to the motors: `forward`, `dive_and_forward`,
# `up_and_forward`. The `SENSOR` is mapped to the `motor sing_eat_and_forward`.
# Mapping states to motors is done using a `dict` here.
#
# Pseudocode:
#```
#                         r1, r2, r3 <= RAND, RAND, RAND
# eat_sing_and_forward <= s1         <= SENSOR(Squid)
# forward              <= n2         <= NOT(s1, n3, n4)
# dive_and_forward     <= n3         <= AND(NOT(s1), OR(AND(r1, NOT(r2, r3)), AND(r3, NOT(r1, r2))))
#                                       AND(NOT(s1), OR(ONE(r1, [r2, r3], ONE(r3, [r1, r2]))))
# up_and_forward       <= n4         <= AND(NOT(s1), NOT(r1, r2, r3))
#
#```

# NOTE: This setup is dependent on the order the nodes are added to the network below!
state_to_motor = {frozenset([1, 2, 3]): frozenset([1]),
                  frozenset([1, 2]): frozenset([1]),
                  frozenset([1, 3]): frozenset([1]),
                  frozenset([2, 3]): frozenset([1]),
                  frozenset([2]): frozenset([1]),
                  frozenset([3]): frozenset([3]),
                  frozenset([1]): frozenset([3]),
                  frozenset([]): frozenset([2])}

motors = ['sing_eat_and_forward', 'forward', 'dive_and_forward',
          'up_and_forward', 'eat_and_forward']
motors_to_action = {frozenset([0]): 'sing_eat_and_forward',
                    frozenset([1]): 'forward',
                    frozenset([2]): 'dive_and_forward',
                    frozenset([3]): 'up_and_forward',
                    frozenset([4]): 'eat_and_forward',
                    '*': '-'}

class Mom(Agent):

    def __init__(self):
        # pylint: disable=line-too-long

        super().__init__(None, 'mom')
        self.network = Network()
        self.s1 = self.network.add_SENSOR_node(Squid)
        self.r1 = self.network.add_RAND_node(0.3)
        self.r2 = self.network.add_RAND_node(0.3)
        self.r3 = self.network.add_RAND_node(0.3)

        self.mnetwork = MotorNetwork(motors, motors_to_action)

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Mom mnetwork.update'))
                               , self.mnetwork.update
                               , do(partial(l.debug, 'Mom state_to_motor'))
                               , lambda s: frozenset([0]) if 0 in s else state_to_motor.get(s)
                               , lambda x: do(partial(l.info, '--- MOM FOUND SQUID, SINGING AND EATING! ---'))(x) if 0 in x else x
                               , self.network.update
                               , do(partial(l.debug, 'Mom unpacked percept'))
                               , unpack(0)
                               , do(partial(l.debug, 'Mom percept'))
                              )

    def __repr__(self):
        return '<{} ({})>'.format(self.__name__, self.__class__.__name__)


# Calf that will by random until hearing song. Dive when hearing song.
# The world will not permit diving below the bottom surface, so it will
# just move forward.
class Calf(Agent):
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        # pylint: disable=line-too-long

        super().__init__(None, 'calf')
        self.network = Network()
        self.s1 = self.network.add_SENSOR_node(Squid)

        self.r1 = self.network.add_RAND_node(0.3)
        self.r2 = self.network.add_RAND_node(0.3)
        self.r3 = self.network.add_RAND_node(0.3)

        self.s2 = self.network.add_SENSOR_node(Song)

        self.mnetwork = MotorNetwork(motors, motors_to_action)

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Calf mnetwork.update'))
                               , self.mnetwork.update
                               , do(partial(l.debug, 'Calf state_to_motor'))
                               , lambda s: frozenset([4]) if 0 in s else (frozenset([2]) if 4 in s else state_to_motor.get(s))
                               , lambda x: do(partial(l.info, '--- CALF HEARD SONG, DIVING! ---'))(x) if 4 in x else x
                               , lambda x: do(partial(l.info, '--- CALF FOUND SQUID, EATING! ---'))(x) if 0 in x else x
                               , do(partial(l.debug, 'Calf network.update'))
                               , self.network.update
                               , do(partial(l.debug, 'Calf unpacked percept'))
                               , unpack(0)
                               , do(partial(l.debug, 'Calf percept'))
                              )

    def __repr__(self):
        return '<{} ({})>'.format(self.__name__, self.__class__.__name__)


# Main
# =====

def run(wss=None, steps=None, seed=None):
    steps = int(steps) if steps else 10
    l.debug('Running random_mom_and_calf in', str(steps), 'steps with seed', seed)

    random.seed(seed)

    options = OPTIONS
    options.wss = wss
    sea = Sea(options)

    mom = Mom()
    calf = Calf()

    sea.add_thing(mom, mom_start_pos)
    sea.add_thing(calf, calf_start_pos)

    sea.run(steps)

if __name__ == "__main__":
    run()
