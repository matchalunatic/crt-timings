from opere import opere
import logging

logger = logging.getLogger(__name__)


class OpereTVResolution(opere.Opere):

    def __init__(self, pixel_clock=960, h_rate=15, h_active=600, max_steps=20000):
        super(OpereTVResolution, self).__init__(max_steps)
        self.pixel_clock = pixel_clock
        self.h_rate = h_rate
        self.h_active = h_active
        logger.info("Inited OpereTVResolution{pixel_clock=%s, h_rate=%s, h_active=%s}", self.pixel_clock, self.h_rate, self.h_active)
        self.goals = [
            self.goal_pixel_clock,
#            self.goal_h_rate,
#            self.goal_h_active
                ]
        self.steps = [
            self.step_h_front_less,
            self.step_h_back_less,
            self.step_h_sync_less,
            self.step_v_front_less,
            self.step_v_back_less,
            self.step_v_sync_less
                ]

    def goal_pixel_clock(self, obj):
        goal = self.pixel_clock
        if obj.p_clock < goal - (0.02 * goal):
            direction = obj.p_clock - goal - (0.02 * goal)
        elif obj.p_clock > goal + (0.02 * goal):
            direction = obj.p_clock - (goal + (0.02 * goal))
        else:
            direction = 0
        logger.debug("p_clock: %s goal: %s", obj.p_clock, goal)
        return direction

    def goal_h_rate(self, obj):
        goal = self.h_rate
        if obj.h_rate < goal - (0.05 * goal):
            direction = -1
        elif obj.h_rate > goal + (0.05 * goal):
            direction = 1
        else:
            direction = 0
        return direction

    def goal_h_active(self, obj):
        goal = self.h_active
        if obj.h_active < goal - (0.05 * goal):
            direction = -1
        elif obj.p_clock > goal + (0.05 * goal):
            direction = 1
        else:
            direction = 0
        return direction

    def step_h_front_less(self, obj):
        if self.goals_states[self.goal_pixel_clock] == -1:
            direction = -1
        else:
            direction = 1

        if obj.h_front > 8 and min(
                obj.h_front, obj.h_sync, obj.h_back) != obj.h_front:
            obj.set_h_front(obj.h_front - 8 * direction)

    def step_h_sync_less(self, obj):
        if self.goals_states[self.goal_pixel_clock] == -1:
            direction = -1
        else:
            direction = 1

        if obj.h_sync > 8 and min(
                obj.h_front, obj.h_sync, obj.h_back) != obj.h_sync:
            obj.set_h_sync(obj.h_sync - 8 * direction)

    def step_h_back_less(self, obj):
        if self.goals_states[self.goal_pixel_clock] == -1:
            direction = -1
        else:
            direction = 1

        if obj.h_back > 8 and min(
                obj.h_front, obj.h_sync, obj.h_back) != obj.h_back:
            obj.set_h_back(obj.h_back - 8 * direction)

    def step_v_front_less(self, obj):
        if self.goals_states[self.goal_pixel_clock] == -1:
            direction = -1
        else:
            direction = 1

        if obj.v_front > 3 and min(
                obj.v_sync, obj.v_front, obj.v_back) != obj.v_front:
            obj.v_front -= 1
            obj.set_v_front(obj.v_front - 1 * direction)

    def step_v_sync_less(self, obj):
        if self.goals_states[self.goal_pixel_clock] == -1:
            direction = -1
        else:
            direction = 1

        if obj.v_sync > 3 and min(
                obj.v_sync, obj.v_front, obj.v_back) != obj.v_sync:
            obj.set_v_sync(obj.v_sync - 1 * direction)

    def step_v_back_less(self, obj):
        if self.goals_states[self.goal_pixel_clock] == -1:
            direction = -1
        else:
            direction = 1

        if obj.v_back > 3 and min(
                obj.v_sync, obj.v_front, obj.v_back) != obj.v_back:
            obj.set_v_back(obj.v_back - 1 * direction)

