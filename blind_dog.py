# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A simple example showing how wsserver can be used
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#

import random

from gzutils.gzutils import DotDict, Logging
from animatai.agents import Agent, Thing, Direction, NonSpatial, XYEnvironment
from animatai.utils import vector_add


# Setup logging
# =============

DEBUG_MODE = True
l = Logging('blind_dog', DEBUG_MODE)

random.seed('blind-dog')

# Configuration of rendering
# =========================
#
# left: (-1,0), right: (1,0), up: (0,-1), down: (0,1)

MOVES = [(0, -1), (0, 1)]

fido_start_pos = (0, 0)
dido_start_pos = (0, 0)

OPTIONS = DotDict({
    'terrain': 'G\nG\nG\nG\nG\nG\nG\nG\nG\nG'.split('\n'),
    'wss_cfg': {
        'numTilesPerSquare': (1, 1),
        'drawGrid': True,
        'randomTerrain': 0,
        'agents': {
            'fido': {
                'name': 'F',
                'pos': fido_start_pos,
                'hidden': False
            },
            'dido': {
                'name': 'D',
                'pos': dido_start_pos,
                'hidden': False
            }
        }
    }
})



# Classes
# ========

class Food(Thing):
    pass

class Water(Thing):
    pass

class Dirt(Thing):
    pass

class Bark(NonSpatial):
    def __hash__(self):
        return hash(self.__name__)

class Park(XYEnvironment):
    def __init__(self, options):
        self.ENV_ENCODING = [('F', Food), ('W', Water), ('D', Dirt)]
        #options['width'] = len(options.terrain[0])
        #options['height'] = len(options.terrain)
        super().__init__(options)

    def calc_performance(self, _, _2):
        pass

    # changes the state of the environment based on what the agent does
    def execute_action(self, agent, action, time):
        super().execute_action(agent, action, time)

        if action == 'Forward':
            # the super class moves the agent for us, just print a status
            msg = '{} decided to {} at location {} and time {}'.format(str(agent)[1:-1],
                                                                       action,
                                                                       agent.location,
                                                                       time)
            self.show_message(msg)

        elif action == 'eat':
            items = self.list_things_at(agent.location, tclass=Food)
            if items:
                if agent.eat(items[0]): #Have the dog eat the first item
                    msg = '{} ate {} at location {} and time {}'.format(str(agent)[1:-1],
                                                                        str(items[0])[1:-1],
                                                                        agent.location,
                                                                        time)
                    self.show_message(msg)
                    self.delete_thing(items[0]) #Delete it from the Park after.

        elif action == 'drink':
            items = self.list_things_at(agent.location, tclass=Water)
            if items:
                if agent.drink(items[0]): #Have the dog drink the first item
                    msg = '{} drank {} at location {} and time {}'.format(str(agent)[1:-1],
                                                                          str(items[0])[1:-1],
                                                                          agent.location,
                                                                          time)
                    self.show_message(msg)
                    self.delete_thing(items[0]) #Delete it from the Park after.

        elif action == 'watch':
            items = self.list_things_at(agent.location, tclass=Thing)
            msg = '{} decided to {} {} at location {} and time {}'.format(str(agent)[1:-1],
                                                                          action,
                                                                          items,
                                                                          agent.location,
                                                                          time)
            self.show_message(msg)

        elif action == 'bark':
            msg = '{} decided to {} at location {} and time {}'.format(str(agent)[1:-1],
                                                                       action,
                                                                       agent.location,
                                                                       time)
            self.show_message(msg)
            agent.bark(time)
            self.add_non_spatial(Bark('vov'), time)


    # By default, we're done when we can't find a live agent,
    # but to prevent killing our cute dog, we will stop before itself -
    # when there is no more food or water
    def is_done(self):
        no_edibles = not any(isinstance(thing, (Food, Water)) for thing in self.things)
        dead_agents = not any(agent.is_alive() for agent in self.agents)
        return dead_agents or no_edibles

class BlindDog(Agent):

    def __repr__(self):
        return '<{} ({})>'.format(self.__name__, self.__class__.__name__)

    def movedown(self):
        self.location = vector_add(self.location, (0, 2))

    def eat(self, thing):
        if isinstance(thing, Food):
            l.info("{} ate food at {}.".format(self.__name__, self.location))
            return True

        return False

    def drink(self, thing):
        if isinstance(thing, Water):
            l.info("{} drank water at {}.".format(self.__name__, self.location))
            return True

        return False

    def bark(self, time):
        l.info("{} barked at time {}.".format(self.__name__, time))
        return True

    # thing
    def watch(self, _):
        return True

# Returns an action based on it's percepts
def program(percept):
    # pylint: disable=redefined-argument-from-local

    # unpack the percepts tuple: ([Thing|NonSpatial], rewards)
    percepts, _ = percept

    action = 'bark' if random.random() < 0.25 else 'Forward'

    for percept in percepts:
        object_, _2 = percept
        if isinstance(object_, Food):
            l.info('-- EATING ---')
            action = 'eat'
            break
        elif isinstance(object_, Water):
            l.info('-- DRINKING ---')
            action = 'drink'
            break
        elif random.random() < 0.5:
            action = 'watch'
            break
        elif isinstance(object_, Bark) and random.random() < 0.5:
            l.info('-- HEARD BARK ---')
            action = 'bark'
            break

    return action



# Main
# =====

# _=param
def run(wss=None, steps=None, seed=None):
    steps = int(steps) if steps else 50

    random.seed(seed)

    l.debug('Running blind_dog ', steps, ' steps')

    options = OPTIONS
    options.wss = wss

    park = Park(options)
    dog1 = BlindDog(program, 'fido')
    dog2 = BlindDog(program, 'dido')

    dog1.direction = Direction(Direction.D)
    dog2.direction = Direction(Direction.D)

    dogfood = Food('dogfood')
    water = Water('water')
    dirt = Dirt('dirt')

    park.add_thing(dog1, fido_start_pos)
    park.add_thing(dog2, dido_start_pos)

    l.debug(dog1.location, dog2.location)

    park.add_thing(dirt, (0, 2))
    park.add_thing(dogfood, (0, 5))
    park.add_thing(water, (0, 7))

    park.run(steps)

if __name__ == "__main__":
    run()
