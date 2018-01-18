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
from numpy import corrcoef
from statistics import mean, stdev

from functools import partial
from toolz.curried import do
from toolz.functoolz import compose
from gzutils.gzutils import DefaultDict, Logging, unpack, get_output_dir

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


        self.network = N = Network(None, objectives)
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[]}
        s1 = N.add_SENSOR_node(Squid)
        self.network_model = NetworkModel({frozenset(): 'no_sensors',
                                           frozenset([s1]): 'squid'})

        self.motor_network = M = MotorNetwork(motors, motors_to_action)

        # NOTE: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        self.ndp = NetworkDP(mom_start_pos, self.status, motor_model, gamma=.9,
                             network_model=self.network_model)
        self.q_agent = NetworkQLearningAgent(self.ndp, Ne=0, Rplus=2,
                                             alpha=lambda n: 60./(59+n),
                                             epsilon=0.2,
                                             delta=0.5)

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
        return '<{} ({}) iterations:{}>'.format(self.__name__,
                                     self.__class__.__name__,
                                     self.q_agent.iterations)


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
        dive_and_forward, up_and_forward = frozenset([2]), frozenset([3])

        motors_to_action = {eat_and_forward: 'eat_and_forward',
                            forward: 'forward',
                            dive_and_forward: 'dive_and_forward',
                            up_and_forward: 'up_and_forward',
                            '*': '-'}

        motor_model = MotorModel(motors_to_action)


        self.network = N = Network(None, objectives)
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[]}
        s1 = N.add_SENSOR_node(Squid)
        s2 = N.add_SENSOR_node(Song)
        self.network_model = NetworkModel({frozenset([]): 'no_sensors',
                                      frozenset([s1]): 'squid',
                                      frozenset([s2]): 'song',
                                      frozenset([s1,s2]): 'squid_and_song'})

        self.motor_network = M = MotorNetwork(motors, motors_to_action)

        # NOTE: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        self.ndp = NetworkDP(calf_start_pos, self.status, motor_model, gamma=.9,
                             network_model=self.network_model)
        self.q_agent = NetworkQLearningAgent(self.ndp, Ne=0, Rplus=2,
                                             alpha=lambda n: 60./(59+n),
                                             epsilon=0.2,
                                             delta=0.5)

        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'Calf mnetwork.update'))
                               , do(partial(l.debug, M))
                               , lambda a: do(partial(l.debug, '*** CALF EATING! ***'))(a) if a == 'eat_and_forward' else a
                               , M.update
                               , do(partial(l.debug, 'Calf q_agent'))
                               , self.q_agent
                               , do(partial(l.debug, N))
                               , lambda p: do(partial(l.debug, '*** CALF HEARD SONG! ***'))(p) if s2 in p[0] else p
                               , lambda p: do(partial(l.debug, '*** CALF FOUND SQUID! ***'))(p) if s1 in p[0] else p
                               , do(partial(l.debug, 'Calf network.update'))
                               , N.update
                               , do(partial(l.debug, 'Calf percept'))
                              )

    def __repr__(self):
        return '<{} ({}) iterations:{}>'.format(self.__name__,
                                     self.__class__.__name__,
                                     self.q_agent.iterations)


# Main
# =====

def run_trial(wss=None, steps=None, seed=None):
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

    for status in ['energy']:
        l.debug('----- ' + status + '------')

        U, pi = mom.q_agent.Q_to_U_and_pi()[status]
        l.debug('mom - pi:', pi, ', U:', U)

        U, pi = calf.q_agent.Q_to_U_and_pi()[status]
        l.debug('calf - pi:', pi, ', U:', U)

    return ({'name': mom.__name__, 'iterations': mom.q_agent.iterations, 'U_and_pi': mom.q_agent.Q_to_U_and_pi()},
            {'name': calf.__name__, 'iterations': calf.q_agent.iterations, 'U_and_pi': calf.q_agent.Q_to_U_and_pi()})


def summarize_U_and_pi(U_and_pi):
    U_res = DefaultDict(0)
    pi_res = DefaultDict(0)
    for j in range(0, len(U_and_pi)):
        for objective, (U, pi) in U_and_pi[j].items():
            for sensors, action in pi.items():
                pi_res[objective + ':' + sensors + ':' + action] += 1
            for sensors, utility in U.items():
                U_res[objective + ':' + sensors] += utility
    U_res = sorted(list(U_res.items()), key=lambda x: x[1], reverse=True)
    pi_res = sorted(list(pi_res.items()), key=lambda x: x[1], reverse=True)
    return U_res, pi_res

def run(wss=None, steps=None, seed=None, trials=10):
    steps = int(steps) if steps else 500
    random.seed(seed)

    ages = ([], [])
    U_and_pi = ([], [])
    for i in range(0, trials):
        if i != 0:
            OPTIONS.output_path = get_output_dir(file=__file__) # get a new timestamp in each trial

        mom, calf = run_trial(wss, steps, seed)
        ages[0].append(mom['iterations'])
        ages[1].append(calf['iterations'])

        U_and_pi[0].append(mom['U_and_pi'])
        U_and_pi[1].append(calf['U_and_pi'])



    l.info('-------- STATS --------')
    l.info('MEAN - mom:', mean(ages[0]), ', calf:', mean(ages[1]))
    if len(ages[0]) > 1:
        l.info('CORRELATIONS:\n', corrcoef(ages[0], ages[1]) )
        l.info('STDEV - mom:', stdev(ages[0]), ', calf:', stdev(ages[1]))
    l.info('AGES - mom:', ages[0])
    l.info('AGES - calf:', ages[1])

    l.info('SUMMARY - U (state:sum of U over the trials) & PI  (state:number of times the policy selected action) ')
    l.info('mom', summarize_U_and_pi(U_and_pi[0]))
    l.info('calf', summarize_U_and_pi(U_and_pi[1]))



if __name__ == "__main__":
    run()
