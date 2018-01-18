# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#
# A `GridAgent` living in a `Grid` environment where each square has a `Landmark`
# object with a unique id. The `GridAgent` has two `NEEDs`: `Energy` and `Water`.
# `Energy` is placed in square 'd' and `Water` in square 'g'. The agent has `SENSORs`
# for `Landmark` objects and `Energy` and `Water`.
#
# +------+------+------+------+
# |   a  |   b  |   c  |   d  |
# +------+------+------+------+
# |   e  |      |   f  |   g  |
# +------+------+------+------+
# |   h  |   i  |   j  |   k  |
# +------+------+------+------+



# Imports
# ======

import random

from functools import partial
from toolz.curried import do
from toolz.functoolz import compose
from gzutils.gzutils import DotDict, Logging, get_output_dir

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
                    '    s \n' +
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
                                     ('s', Energy), ('W', Water)]
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
motors_to_action = {north: '^', south: 'v', east: '>', west: '<', '*': '-'}
motor_model = MotorModel(motors_to_action)

class GridAgent(Agent):

    def __init__(self, objectives, landmarks):
        # pylint: disable=line-too-long, too-many-locals

        super().__init__(None, 'grid_agent')

        N = Network(None, objectives)
        SENSOR = N.add_SENSOR_node
        self.status = N.get_NEEDs()
        self.status_history = {'energy':[], 'water': []}

        # Create sensors
        SENSOR(Water)
        SENSOR(Energy)
        # create one SENSOR for each square
        sensor_dict = {}
        for lm in landmarks:
            sensor_dict[frozenset([SENSOR(Landmark, lm)])] = lm
        network_model = NetworkModel(sensor_dict)

        M = MotorNetwork(motors, motors_to_action)

        # NOTE: init=agent_start_pos, using a location here (only for debugging),
        #            is a state when MDP:s are used
        self.ndp = NetworkDP(agent_start_pos, self.status, motor_model, .9, network_model)
        self.q_agent = NetworkQLearningAgent(self.ndp, Ne=0, Rplus=2,
                                             alpha=lambda n: 60./(59+n),
                                             epsilon=0.2,
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
                               , do(self.printU)
                              )

    def __repr__(self):
        return '<{} ({})>'.format(self.__name__, self.__class__.__name__)


    def printU(self, _):
        for status in ['energy', 'water']:
            l.info('----- ' + status + '------')
            U, pi = self.q_agent.Q_to_U_and_pi()[status]

            l.info('Utilities:')
            U = {k: '{0:.3f}'.format(v) for k, v in U.items()}
            print_grid(U)
            l.info('Policy:')
            print_grid(pi)

# Main
# =====

def print_grid(U):
    res = ''
    for k in ['7', '8', '9', '10']:
        res += (str(U[k]) if k in U else '-') + '\t'
    l.info(res)
    res = ''
    for k in ['13', 'X', '15', '16']:
        res += (str(U[k]) if k in U else '-') + '\t'
    l.info(res)
    res = ''
    for k in ['19', '20', '21', '22']:
        res += (str(U[k]) if k in U else '-') + '\t'
    l.info(res)

    res = ''
    for k in U:
        if k not in ['7', '8', '9', '10', '13', 'X', '15', '16', '19', '20', '21', '22']:
            res += str(k) + ':' + str(U[k]) + '\t'
    l.info(res)


def run(wss=None, steps=None, seed=None):
    steps = int(steps) if steps else 1000
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
    l.info('The SENSORS will have these numbers:')
    l.info('      2, 3, 4,{1,5}')
    l.info('      6,    7,{0,8}')
    l.info('      9,10,11,12')


    l.info('q_agent:', grid_agent.q_agent)

if __name__ == "__main__":
    run()
