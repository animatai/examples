# pylint: disable=missing-docstring, global-statement, invalid-name
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#


# Imports
# ======

import random
import unittest

from functools import partial
from toolz.curried import do
from toolz.functoolz import compose
from gzutils.gzutils import DotDict, Logging, get_output_dir, save_csv_file

from animatai.mdp import MDP
from animatai.utils import vector_add
from animatai.agents import Agent, Obstacle, Thing, XYEnvironment
from animatai.network import MotorNetwork, Network
from animatai.network_rl import MotorModel, NetworkModel, NetworkDP, NetworkQLearningAgent


# Setup logging
# =============

random.seed(1)

OUTPUT_DIR = get_output_dir()
DEBUG_MODE = True
l = Logging('grid', DEBUG_MODE)


# Environment
# ===========

class Energy(Thing):
    pass

class Water(Thing):
    pass

class Landmark(Thing):
    pass

# +------+------+------+------+
# |   a  |   b  |   c  |   d  |
# +------+------+------+------+
# |   e  |      |   f  |   g  |
# +------+------+------+------+
# |   h  |   i  |   j  |   k  |
# +------+------+------+------+

terrain = ('GGGGGG\n' +
           'GGGGGG\n' +
           'GGGGGG\n' +
           'GGGGGG\n' +
           'GGGGGG')

things = ('XXXXXX\n' +
          'XllllX\n' +
          'XlXllX\n' +
          'XllllX\n' +
          'XXXXXX')

exogenous_things = ('      \n' +
                    '    S \n' +
                    '    W \n' +
                    '      \n' +
                    '      ')

agent_start_pos = (1, 3)

# rewards: {action: {percept: {objective: reward}}}
OPTIONS = DotDict({
    'output_path': get_output_dir(file=__file__),
    'terrain': terrain.split('\n'),
    'things': things.split('\n'),
    'exogenous_things': exogenous_things.split('\n'),
    'exogenous_things_prob': 0.1,
    'objectives': {'energy': 1.0, 'water': 1.0},
    'rewards':{
        None: {
            Energy: {
                'energy': 1.0,
                'water': -0.001
            },
            Water: {
                'energy': -0.001,
                'water': 1.0
            },
            None: {
                'energy': -0.001,
                'water': -0.001
            }
        }
    },
    'wss_cfg': {
        'numTilesPerSquare': (1, 1),
        'drawGrid': True,
        'randomTerrain': 0,
        'agents': {
            'grid_agent': {
                'name': 'G',
                'pos': agent_start_pos,
                'hidden': False
            }
        }
    }
})

class Grid(XYEnvironment):

    def __init__(self, options):
        self.options = options
        self.options.ENV_ENCODING = [('l', Landmark), ('X', Obstacle),
                                     ('S', Energy), ('W', Water)]
        self.options.save_history_for = [Energy, Water]
        super().__init__(self.options)

    def execute_action(self, agent, action, time):
        self.show_message((agent.__name__ + ' performing ' + str(action) + ' at location ' +
                           str(agent.location) + ' and time ' + str(time)))

        directions = {'^': (0, -1), 'v': (0, 1), '>': (1, 0), '<': (-1, 0)}
        if not action in directions:
            l.error('execute_action:unknow action', action, 'for agent', agent, 'at time', time)
            return

        if agent.location == (4, 1):
            l.info('*** MIGHT HAVE FOUND ENERGY ***')
            agent.location = agent_start_pos

        if agent.location == (4, 2):
            l.info('*** MIGHT HAVE FOUND WATER ***')
            agent.location = agent_start_pos

        agent.bump = self.move_to(agent,
                                  vector_add(directions[action],
                                             agent.location))


# Agent
# ======

# Motors and actions
motors = ['^', 'v', '<', '>']
north, south, east, west = frozenset([0]), frozenset([1]), frozenset([2]), frozenset([3])
motors_to_action = {north: '^', south: 'v', east: '>', west: '<'} #, '*': '-'}
motor_model = MotorModel(motors_to_action)

class GridAgent(Agent):

    def __init__(self, objectives, landmarks):
        # pylint: disable=line-too-long, too-many-locals

        super().__init__(None, 'GridAgent')

        N = Network(None, objectives)
        SENSOR = N.add_SENSOR_node
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[], 'water': []}

        water, energy = SENSOR(Water), SENSOR(Energy)

        # create one SENSOR for each square
        sensor_dict = {}
        for lm in landmarks:
            sensor_dict[frozenset([SENSOR(Landmark, lm)])] = lm
        network_model = NetworkModel(sensor_dict)

        M = MotorNetwork(motors, motors_to_action)

        # TODO: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        #       sensor_model=None (used with MDPs but not in proper environments)
        self.ndp = NetworkDP(agent_start_pos, self.status, motor_model, .9, network_model)
        self.q_agent = NetworkQLearningAgent(self.ndp, Ne=5, Rplus=2,
                                        alpha=lambda n: 60./(59+n),
                                        delta=0.5)


        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'mnetwork.update'))
                               , M.update
                               , do(partial(l.debug, 'q_agent'))
                               , self.q_agent
                               , do(partial(l.debug, N))
                               , do(partial(l.debug, 'network.update'))
                               , N.update
                               , do(partial(l.debug, 'percept'))
                               , lambda x: do(partial(l.debug, '*** ENERY FOUND ***'))(x) if 'energy' in x[1] and x[1]['energy'] > 0.0 else x
                               , lambda x: do(partial(l.debug, '*** WATER FOUND ***'))(x) if 'water' in x[1] and x[1]['water'] > 0.0 else x
                              )

    def __repr__(self):
        return '<{} ({})>'.format(self.__name__, self.__class__.__name__)


# Main
# =====

def print_grid(U):
    l.info(U[0:4])
    l.info(U[4:7])
    l.info(U[7:11])

def run(wss=None, steps=None, seed=None):
    steps = int(steps) if steps else 20
    l.debug('Running grid in', str(steps), 'steps with seed', seed)

    random.seed(seed)
    options = OPTIONS
    options.wss = wss

    grid = Grid(options)
    landmarks = [lm.__name__ for lm in grid.list_things(Landmark)]
    grid_agent = GridAgent(options.objectives, landmarks)
    grid.add_thing(grid_agent, agent_start_pos)
    grid.run(steps)

    l.info('\n')
    l.info('The Landmarks will have these numbers:')
    l.info('   0, 1, 2, 3, 4, 5')
    l.info('0: X, X, X, X, X, X')
    l.info('1: X, 7, 8, 9,10, X')
    l.info('2: X,13, X,15,16, X')
    l.info('3: X,19,20,21,22, X')
    l.info('4: X, X, X, X, X, X')

    for status in ['energy', 'water']:
        l.info('----- ' + status + '------')
        U, pi = grid_agent.q_agent.Q_to_U_and_pi()[status]

        l.info(U)
        l.info(pi)

        # print the utilities and the policy also
        U1 = sorted(U.items(), key=lambda x: int(x[0] if type(x[0]) is str else 99))
        pi1 = sorted(pi.items(), key=lambda x: int(x[0] if type(x[0]) is str else 99))
        print_grid(U1)
        print_grid(pi1)


    l.info('q_agent:', grid_agent.q_agent)

if __name__ == "__main__":
    run()
