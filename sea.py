# pylint: disable=missing-docstring, global-statement, invalid-name, too-few-public-methods, no-self-use
#
# A random Mother cachelot and calf
#
# Copyright (C) 2017  Jonas Colmsjö, Claes Strannegård
#

from animatai.agents import Thing, Obstacle, Direction, NonSpatial, XYEnvironment
from gzutils.gzutils import DotDict, Logging


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

class Sea(XYEnvironment):

    # pylint: disable=arguments-differ

    def __init__(self, options):
        self.options = DotDict(options)
        self.options.ENV_ENCODING = [('s', Squid), ('X', Obstacle)]
        self.options.save_history_for = [Squid]
        super().__init__(self.options)

        self.agent_status = {}
        self.agent_U_and_pi = {}

    # to be used after the __call__ function
    def any_measurement_decreased(self):
        any_obj = list(self.environment_history)[0]
        i, res = len(self.environment_history[any_obj]), False
        if i < 2:
            return False
        for cls in self.save_history_for:
            res = res or self.environment_history[cls][i] < self.environment_history[cls][i - 1]
        return res

    def execute_action(self, agent, action, time):
        self.show_message((agent.__name__ + ' performing ' + str(action) + ' at location ' +
                           str(agent.location) + ' and time ' + str(time)))

        self.agent_status[agent.__name__] = agent.status
        self.agent_U_and_pi[agent.__name__] = agent.q_agent.Q_to_U_and_pi()
        self.show_escaped_text('status', str(self.agent_status))
        self.show_escaped_text('U_and_pi',  str(self.agent_U_and_pi))

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
