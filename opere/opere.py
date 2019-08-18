"""opere: an stupid operational research library.

This is stupid because it is very difficult to optimize a nonlinear
system.

goals: ordered collection of callables that take the manipulated
object as parameter and return either:
    negative float (before goal), 0 (goal reached), positive float
    (after goal).

steps: ordered collection of callables that take the manipulated
object as parameter and do something

End conditions: all goals are reached or a pre-defined number of
steps have been taken.
        
Goal functions should be defined as having a wiggle space. They
should not expect exact results but results in acceptable ranges.

Steps should be simple (avoid while loops: each iteration would
be a step, and the goals would be the end condition).

Steps should take in account the goals_states and goals_derivatives
so to decide in which direction they should push their value,
if they are correlated.

An Opere object exposes a call(obj) method that can be used to
compose together operations researches.

For the moment, the program works OK with one goal but this hardly
qualifies as operational research. 
"""

import itertools
import collections
import logging

logger = logging.getLogger(__name__)

class Opere(object):
    def __init__(self, max_steps=1000):
        self.max_steps = max_steps
        self.steps_left = self.max_steps
        self.goals = []
        self.steps = []
        self.goals_states = {}
        self.goals_values = {}
        self.goals_derivatives = {}

    def call(self, obj):
        """Loops over steps until we have reached all goals
           or we have exhausted our step count"""
        steps_cycle = itertools.cycle(self.steps)
        for goal in self.goals:
            self.goals_states[goal] = goal(obj)
            self.goals_values[goal] = collections.deque(maxlen=100)
            self.goals_derivatives[goal] = collections.deque(maxlen=100)
            self.goals_values[goal].append(self.goals_states[goal])

        while self.steps_left > 0:
            for goal in self.goals:
                old_value = self.goals_states[goal]
                new_value = goal(obj)
                self.goals_states[goal] = new_value
                self.goals_values[goal].append(new_value)
                self.goals_derivatives[goal].append(new_value - old_value)
            if all(a == 0 for a in self.goals_states.values()):
                logger.debug("Goals all reached in %s steps", self.max_steps - self.steps_left)
                return True
            step = next(steps_cycle)
            step(obj)
            self.steps_left -= 1
        return False
