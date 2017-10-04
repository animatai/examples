# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A random Mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#

from ecosystem.agents import Thing, Obstacle, Direction, NonSpatial, XYEnvironment
from gzutils.gzutils import DotDict, Logging, get_output_dir, save_csv_file


# Setup constants and logging
# ===========================

DEBUG_MODE = True
l = Logging('sea', DEBUG_MODE)


# Classes
# ========

class Squid(Thing):
    pass

# action 'sing' creates Song
class Song(NonSpatial):
    pass

# motors are executed instead of single actions. motors consists of several actions
# and setup in the options for the agent.
class Sea(XYEnvironment):

    # pylint: disable=arguments-differ

    def __init__(self, options):
        self.options = DotDict(options)
        self.options.ENV_ENCODING = [('s', Squid), ('X', Obstacle)]
        self.options.save_history_for = [Squid]
        super().__init__(self.options)

    # to be used after the __call__ function
    def any_measurement_decreased(self):
        any_obj = list(self.environment_history)[0]
        i, res = len(self.environment_history[any_obj]), False
        if i < 2:
            return False
        for cls in self.save_history_for:
            res = res or self.environment_history[cls][i] < self.environment_history[cls][i - 1]
        return res

    # reward dict:
    #     'reward':{
    #        'eat_and_forward': {
    #            Squid: { 'energy': 0.1 },
    #            None: { 'energy': -0.05 }
    #        },
    #
    def calc_performance(self, agent, action):
        # pylint: disable=len-as-condition

        rewards = {}
        if not hasattr(agent, 'status'):
            agent.status = self.options.objectives.copy()

        for rewarded_action, object_and_objectives in self.options.rewards.items():
            if action == rewarded_action:
                for rewarded_thing, obj_and_reward in object_and_objectives.items():
                    if rewarded_thing and len(self.list_things_at(agent.location, rewarded_thing)):
                        for obj, rew in obj_and_reward.items():
                            agent.status[obj] += rew
                            rewards[obj] = rew
                            agent.alive = agent.alive and agent.status[obj] > 0
                    elif rewarded_thing is None:
                        for obj, rew in obj_and_reward.items():
                            agent.status[obj] += rew
                            rewards[obj] = rew
                            agent.alive = agent.alive and agent.status[obj] > 0

        l.info(agent.__name__, 'alive:', agent.alive,
               ', status:', agent.status,
               ', rewards:', rewards,
               ', env_history:', [self.environment_history[cls][len(self.environment_history[cls])-1] for cls in self.save_history_for])

        return rewards

    def execute_action(self, agent, action, time):
        self.show_message((agent.__name__ + ' performing ' + action + ' at location ' +
                           str(agent.location) + ' and time ' + str(time)))
        def up():
            agent.direction += Direction.L
            agent.bump = self.move_to(agent, agent.direction.move_forward(agent.location))
            agent.direction += Direction.R

        def down():
            agent.direction += Direction.R
            agent.bump = self.move_to(agent, agent.direction.move_forward(agent.location))
            agent.direction += Direction.L

        def forward():
            agent.bump = self.move_to(agent, agent.direction.move_forward(agent.location))
            # a torus world
            agent.location = (agent.location[0] % self.width, agent.location[1])

        def eat():
            squid = self.list_things_at(agent.location, Squid)
            if squid:
                self.delete_thing(squid[0])

        # The direction of the agent should always be 'right' in this world
        assert agent.direction.direction == Direction.R

        agent.bump = False
        if action == 'sing_eat_and_forward':
            self.add_non_spatial(Song(), time)
            eat()
            forward()
        elif action == 'eat_and_forward':
            eat()
            forward()
        elif action == 'dive_and_forward':
            down()
            forward()
        elif action == 'up_and_forward':
            up()
            forward()
        elif action == 'forward':
            forward()
        else:
            l.error('execute_action:unknow action', action, 'for agent', agent, 'at time', time)
