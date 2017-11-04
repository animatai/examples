# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A learning mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#
# A cachelot example where mom and calf learns. The only behaiour that isn't
# learnt is that the mother signs when she eats.
#

import random

from functools import partial
from toolz.curried import do
from toolz.functoolz import compose
from gzutils.gzutils import Logging, unpack

from animatai.agents import Agent
from animatai.network import Network, MotorNetwork
from animatai.network_rl import MotorModel, NetworkModel, NetworkDP, NetworkQLearningAgent

from sea import Sea, Song, Squid
from random_mom_and_calf_config import mom_start_pos, calf_start_pos, OPTIONS


# Setup logging
# =============

DEBUG_MODE = True
l = Logging('mom_and_calf', DEBUG_MODE)


# Mom and Calf
# ===========

class Mom(Agent):

    def __init__(self, objectives):
        # pylint: disable=line-too-long, too-many-locals

        # program=None
        super().__init__(None, 'mom')

        # Motors and actions
        motors = ['sing_eat_and_forward', 'forward', 'dive_and_forward',
                  'up_and_forward']

        sing_eat_and_forward, forward = frozenset([0]), frozenset([1])
        dive_and_forward, up_and_forward = frozenset([2]), frozenset([3])

        motors_to_action = {sing_eat_and_forward: 'sing_eat_and_forward',
                            forward: 'forward',
                            dive_and_forward: 'dive_and_forward',
                            up_and_forward: 'up_and_forward',
                            '*': '-'}

        motor_model = MotorModel(motors_to_action)


        N = Network(None, objectives)
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[]}
        s1 = N.add_SENSOR_node(Squid)
        network_model = NetworkModel({s1: 'Squid'})

        M = MotorNetwork(motors, motors_to_action)

        # NOTE: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        self.ndp = NetworkDP(mom_start_pos, self.status, motor_model, .9, network_model)
        self.q_agent = NetworkQLearningAgent(self.ndp, Ne=0, Rplus=2,
                                             alpha=lambda n: 60./(59+n),
                                             epsilon=0.2,
                                             delta=0.5)

        l.info('Mom q_agent:', self.q_agent)
        l.info('mom_motors_to_action:', motors_to_action)

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Mom mnetwork.update'))
                               , do(partial(l.debug, M))
                               , M.update
                               , do(partial(l.debug, 'Mom q_agent'))
                               , self.q_agent
                               , do(partial(l.debug, N))
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

    def __init__(self, objectives):
        # pylint: disable=line-too-long

        super().__init__(None, 'calf')

        motors = ['eat_and_forward', 'forward', 'dive_and_forward',
                  'up_and_forward']

        eat_and_forward, forward = frozenset([0]), frozenset([1])
        dive_and_forward, up_and_forward  = frozenset([2]), frozenset([3])

        motors_to_action = {eat_and_forward: 'eat_and_forward',
                            forward: 'forward',
                            dive_and_forward: 'dive_and_forward',
                            up_and_forward: 'up_and_forward',
                            '*': '-'}

        motor_model = MotorModel(motors_to_action)


        N = Network(None, objectives)
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[]}
        s1 = N.add_SENSOR_node(Squid)
        s2 = N.add_SENSOR_node(Song)
        network_model = NetworkModel({s1: 'Squid', s2: 'Song'})

        M = MotorNetwork(motors, motors_to_action)

        # NOTE: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        self.ndp = NetworkDP(calf_start_pos, self.status, motor_model, .9, network_model)
        self.q_agent = NetworkQLearningAgent(self.ndp, Ne=0, Rplus=2,
                                             alpha=lambda n: 60./(59+n),
                                             epsilon=0.2,
                                             delta=0.5)

        l.info('Calf q_agent:', self.q_agent)
        l.info('motors_to_action:', motors_to_action)

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Calf mnetwork.update'))
                               , do(partial(l.debug, M))
                               , M.update
                               , do(partial(l.debug, 'Calf q_agent'))
                               , self.q_agent
                               , do(partial(l.debug, N))
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
    l.debug('Running mom_and_calf in', str(steps), 'steps with seed', seed)

    random.seed(seed)

    options = OPTIONS
    options.wss = wss
    sea = Sea(options)

    mom = Mom(options.objectives)
    calf = Calf(options.objectives)

    sea.add_thing(mom, mom_start_pos)
    sea.add_thing(calf, calf_start_pos)

    sea.run(steps)

if __name__ == "__main__":
    run()
