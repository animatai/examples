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
from animatai.network_rl import MotorModel, SensorModel, NetworkDP, NetworkQLearningAgent


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
                    '     S\n' +
                    '     W\n' +
                    '      \n' +
                    '      ')

agent_start_pos = (1, 3)

# rewards: {action: {percept: {objective: reward}}}
OPTIONS = DotDict({
    'output_path': get_output_dir(file=__file__),
    'terrain': terrain.split('\n'),
    'things': things.split('\n'),
    'exogenous_things': exogenous_things.split('\n'),
    'exogenous_things_prob': 0.005,
    'objectives': {'energy': 1.0, 'water': 1.0},
    'rewards':{
        None: {
            Energy: {
                'energy': 0.1,
                'water': 0.0
            },
            Water: {
                'energy': 0.0,
                'water': 0.1
            },
            None: {
                'energy': 0.0,
                'water': 0.0
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
        super().__init__(self.options)

    def execute_action(self, agent, action, time):
        self.show_message((agent.__name__ + ' performing ' + str(action) + ' at location ' +
                           str(agent.location) + ' and time ' + str(time)))

        directions = {'^': (0, -1), 'v': (0, 1), '>': (1, 0), '<': (-1, 0)}
        if not action in directions:
            l.error('execute_action:unknow action', action, 'for agent', agent, 'at time', time)
            return

        agent.bump = self.move_to(agent,
                                  vector_add(directions[action],
                                             agent.location))


# Agent
# ======

# Motors and actions
motors = ['^', 'v', '<', '>']
north, south, east, west = frozenset([0]), frozenset([1]), frozenset([2]), frozenset([3])
motors_to_action = {north: '^', south: 'v', east: '>', west: '<', '*': '-'}

'''
landmark_to_state = {frozenset([0]): 'a',
                     frozenset([1]): 'b',
                     frozenset([2]): 'c',
                     frozenset([3]): 'd',
                     frozenset([4]): 'e',
                     frozenset([5]): 'f',
                     frozenset([6]): 'g',
                     frozenset([7]): 'h',
                     frozenset([8]): 'i',
                     frozenset([9]): 'j',
                     frozenset([10]): 'k'}
sensor_model = landmark_to_state
'''

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
        landmark_sensor = []
        for lm in landmarks:
            landmark_sensor.append(SENSOR(Landmark, lm))

        M = MotorNetwork(motors, motors_to_action)

        # TODO: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        #       motor_model=None using M.motors_for_all_actions() instead
        #       sensor_model=None (used with MDP:s not proper environments)
        self.ndp = NetworkDP(agent_start_pos, self.status, None, .9, None, M.motors_for_all_actions())
        q_agent = NetworkQLearningAgent(self.ndp, Ne=5, Rplus=2,
                                        alpha=lambda n: 60./(59+n),
                                        delta=0.5,
                                        max_iterations=100)


        # compose applies the functions from right to left
        self.program = compose(do(partial(l.debug, 'mnetwork.update'))
                               , M.update
                               , do(partial(l.debug, 'q_agent'))
                               , q_agent
                               , do(partial(l.debug, N))
                               , do(partial(l.debug, 'network.update'))
                               , N.update
                               , do(partial(l.debug, 'percept'))
                              )

    def __repr__(self):
        return '<{} ({})>'.format(self.__name__, self.__class__.__name__)


# Main
# =====

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

if __name__ == "__main__":
    run()
