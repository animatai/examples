# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A random mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#
# Configuration that is common for the different cachelot examples.
#

from gzutils.gzutils import DotDict, get_output_dir

from sea import Squid

terrain = ('WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW\n' +
           'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW\n' +
           'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW\n' +
           'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW\n' +
           'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW\n' +
           'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW\n' +
           'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW')

# the mother and calf have separate and identical lanes
things = ('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n' +
          '                                                  \n' +
          '  ssss              ssss                  ssss    \n' +
          'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n' +
          '                                                  \n' +
          '  ssss              ssss                  ssss    \n' +
          'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

# the mother and calf have separate and identical lanes
exogenous_things = ('                                                  \n' +
                    '                                                  \n' +
                    '  ssss              ssss                  ssss    \n' +
                    '                                                  \n' +
                    '                                                  \n' +
                    '  ssss              ssss                  ssss    \n' +
                    '                                                  ')


mom_start_pos = (0, 1)
calf_start_pos = (0, 4)

# `motors` can perform several `actions`. The Sea Environment has four available
# `actions`: `eat`, `down`, `up`, `forward`. There is also one `nsaction` which is `sing`
# `sensors` are boolean variables indicating percepts (`Things` of different kinds)
# that are perceived. Active `sensors` are sent as input to the `program`
OPTIONS = DotDict({
    'output_path': get_output_dir(file=__file__),
    'terrain': terrain.split('\n'),
    'things': things.split('\n'),
    'exogenous_things': exogenous_things.split('\n'),
    'exogenous_things_prob': 0.05,
    'objectives': {'energy': 1.0},
    'rewards':{
        'sing_eat_and_forward': {
            Squid: {
                'energy': 0.5
            },
            None: {
                'energy': -0.02
            }
        },
        'eat_and_forward': {
            Squid: {
                'energy': 0.5
            },
            None: {
                'energy': -0.02
            }
        },
        'dive_and_forward': {
            None: {
                'energy': -0.02
            }
        },
        'up_and_forward': {
            None: {
                'energy': -0.01
            }
        },
        'forward': {
            None: {
                'energy': -0.01
            }
        },
        None: {
            None: {
                'energy': 0.0
            }
        },
    },
    'wss_cfg': {
        'numTilesPerSquare': (1, 1),
        'drawGrid': True,
        'randomTerrain': 0,
        'agents': {
            'mom': {
                'name': 'M',
                'pos': mom_start_pos,
                'hidden': False
            },
            'calf': {
                'name': 'c',
                'pos': calf_start_pos,
                'hidden': False
            }
        }
    }
})
