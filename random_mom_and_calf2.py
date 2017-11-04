# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A random mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#
# This is an extention of the `random_mom_and_calf` example where the mom and
# calf are implemented using classes that are inheriting the `Agent`
# class. The behaviour is now implemented using the `Network` and `MotorNetwork`
# classes. The `Mom` and `Calf` classes shows two slightly different ways
# the classes can be used.
#

import random
from functools import partial

from animatai.agents import Agent
from animatai.network import Network, MotorNetwork

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
#          rewrite using ONE            AND(NOT(s1), OR(ONE(r1, [r2, r3], ONE(r3, [r1, r2]))))
# up_and_forward       <= n4         <= AND(NOT(s1), NOT(r1, r2, r3))
#
#```

motors = ['sing_eat_and_forward', 'forward', 'dive_and_forward',
          'up_and_forward', 'eat_and_forward']

# motors
sing_eat_and_forward, forward, dive_and_forward = frozenset([0]), frozenset([1]), frozenset([2])
up_and_forward, eat_and_forward = frozenset([3]), frozenset([4])

motors_to_action = {sing_eat_and_forward: 'sing_eat_and_forward',
                    forward: 'forward',
                    dive_and_forward: 'dive_and_forward',
                    up_and_forward: 'up_and_forward',
                    eat_and_forward: 'eat_and_forward',
                    '*': '-'}

class Mom(Agent):

    def __init__(self):
        # pylint: disable=line-too-long, too-many-locals

        super().__init__(None, 'mom')

        N = Network(None, {'energy': 1.0})
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[]}

        M = MotorNetwork(motors, motors_to_action)
        SENSOR, RAND, AND = N.add_SENSOR_node, N.add_RAND_node, N.add_AND_node
        NOT, OR = N.add_NOT_node, N.add_OR_node

        s1, r1, r2, r3 = SENSOR(Squid), RAND(0.3), RAND(0.3), RAND(0.3)
        n3 = AND([NOT([s1]), OR([AND([r1, NOT([r2, r3])]), AND([r3, NOT([r1, r2])])])])
        n4 = AND([NOT([s1]), NOT([r1, r2, r3])])
        n2 = NOT([s1, n3, n4])

        state_to_motor = {frozenset([s1]): sing_eat_and_forward,
                          frozenset([n2]): forward,
                          frozenset([n3]): dive_and_forward,
                          frozenset([n4]): up_and_forward}

        l.info('state_to_motor:', state_to_motor)
        l.info('motors_to_action:', motors_to_action)

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Mom mnetwork.update'))
                               , M.update
                               , do(partial(l.debug, 'Mom state_to_motor'))
                               , lambda p: state_to_motor.get(p[0])
                               , do(partial(l.debug, N))
                               , do(partial(l.debug, 'Mom filter interesting states'))
                               , lambda p: (p[0] & {s1, n2, n3, n4}, p[1])
                               , do(partial(l.debug, 'Mom network.update'))
                               , N.update
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

        N = Network(None, {'energy': 1.0})
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[]}

        s1 = N.add_SENSOR_node(Squid)
        r1 = N.add_RAND_node(0.3)
        r2 = N.add_RAND_node(0.3)
        r3 = N.add_RAND_node(0.3)
        s2 = N.add_SENSOR_node(Song)

        M = MotorNetwork(motors, motors_to_action)

        state_to_motor = {frozenset([r1, r2, r3]): forward,
                          frozenset([r1, r2]): forward,
                          frozenset([r1, r3]): forward,
                          frozenset([r2, r3]): forward,
                          frozenset([r2]): forward,
                          frozenset([r3]): up_and_forward,
                          frozenset([r1]): up_and_forward,
                          frozenset([]): dive_and_forward}

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Calf mnetwork.update'))
                               , M.update
                               , do(partial(l.debug, 'Calf state_to_motor'))
                               , lambda p: eat_and_forward if s1 in p[0] else (dive_and_forward if s2 in p[0] else up_and_forward)
                               #, lambda s: eat_and_forward if s1 in s else (dive_and_forward if s2 in s else state_to_motor.get(s))
                               , lambda p: do(partial(l.info, '--- CALF HEARD SONG, DIVING! ---'))(p) if s2 in p[0] else p
                               , lambda p: do(partial(l.info, '--- CALF FOUND SQUID, EATING! ---'))(p) if s1 in p[0] else p
                               , do(partial(l.debug, 'Calf network.update'))
                               , N.update
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
