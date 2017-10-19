# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A random Mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#

import random

from ecosystem.agents import Agent
from gzutils.gzutils import Logging

from sea import Sea, Song, Squid
from random_mom_and_calf_config import mom_start_pos, calf_start_pos, OPTIONS


# Setup logging
# =============

DEBUG_MODE = True
l = Logging('random_mom_and_calf', DEBUG_MODE)

# Mom that moves by random until squid is found. Move forward when there is
# squid and sing.
def mom_program(percept):
    # pylint: disable=redefined-argument-from-local

    # unpack the percepts tuple: ([Thing|NonSpatial], rewards)
    percepts, _ = percept

    action = None
    for percept in percepts:
        # _2=radius
        object_, _2 = percept
        if isinstance(object_, Squid):
            l.info('--- MOM FOUND SQUID, SINGING AND EATING! ---')
            action = 'sing_eat_and_forward'

    if not action:
        action = 'forward'
        rand = random.random()
        if rand < 1/3:
            action = 'dive_and_forward'
        elif rand < 2/3:
            action = 'up_and_forward'


    return action


# Calf that will by random until hearing song. Dive when hearing song.
# The world will not permit diving below the bottom surface, so it will
# just move forward.
def calf_program(percept):
    # pylint: disable=redefined-argument-from-local

    # unpack the percepts tuple: ([Thing|NonSpatial], rewards)
    percepts, _ = percept

    action = None

    for percept in percepts:
        # _2=radius
        object_, _2 = percept
        if isinstance(object_, Squid):
            l.info('--- CALF FOUND SQUID, EATING! ---')
            action = 'eat_and_forward'

        if not action and isinstance(object_, Song):
            l.info('--- CALF HEARD SONG, DIVING! ---')
            action = 'dive_and_forward'


    if not action:
        action = 'forward'
        rand = random.random()
        if  rand < 1/3:
            action = 'dive_and_forward'
        elif rand < 2/3:
            action = 'up_and_forward'

    return action


# Main
# =====

def run(wss=None, steps=None, seed=None):
    l.debug('Running random_mom_and_calf in', str(steps), 'steps with seed', seed)
    steps = int(steps) if steps else 10

    random.seed(seed)

    options = OPTIONS
    options.wss = wss
    sea = Sea(options)

    mom = Agent(mom_program, 'mom')
    calf = Agent(calf_program, 'calf')

    sea.add_thing(mom, mom_start_pos)
    sea.add_thing(calf, calf_start_pos)

    sea.run(steps)

if __name__ == "__main__":
    run()
