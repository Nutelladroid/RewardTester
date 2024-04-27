from .physics_object import PhysicsObject
from collections import defaultdict

class PlayerData(object):
    def __init__(self):
        self.car_id: int = -1
        self.team_num: int = -1
        self.match_goals: int = -1
        self.match_saves: int = -1
        self.match_shots: int = -1
        self.match_demolishes: int = -1
        self.match_assists: int = -1
        self.boost_pickups: int = -1
        self.is_demoed: bool = False
        self.on_ground: bool = False
        self.ball_touched: bool = False
        self.has_jump: bool = False
        self.has_jumped: bool = False
        self.has_flip: bool = False
        self.has_flipped: bool = False
        self.boost_amount: float = -1
        self.car_data: PhysicsObject = PhysicsObject()
        self.inverted_car_data: PhysicsObject = PhysicsObject()
        self._steer_input: float = 0.0
        self._throttle_input: float = 0.0
        self._pitch_input: float = 0.0
        self._roll_input: float = 0.0
        self._jump_input: bool = False
        self._boost_input: bool = False
        self._handbrake_input: bool = False
        self._use_item_input: bool = False

    @property
    def steer_input(self):
        return self._steer_input

    @steer_input.setter
    def steer_input(self, value):
        self._steer_input = value

    @property
    def throttle_input(self):
        return self._throttle_input

    @throttle_input.setter
    def throttle_input(self, value):
        self._throttle_input = value

    @property
    def pitch_input(self):
        return self._pitch_input

    @pitch_input.setter
    def pitch_input(self, value):
        self._pitch_input = value

    @property
    def roll_input(self):
        return self._roll_input

    @roll_input.setter
    def roll_input(self, value):
        self._roll_input = value

    @property
    def jump_input(self):
        return self._jump_input

    @jump_input.setter
    def jump_input(self, value):
        self._jump_input = value

    @property
    def boost_input(self):
        return self._boost_input

    @boost_input.setter
    def boost_input(self, value):
        self._boost_input = value

    @property
    def handbrake_input(self):
        return self._handbrake_input

    @handbrake_input.setter
    def handbrake_input(self, value):
        self._handbrake_input = value

    @property
    def use_item_input(self):
        return self._use_item_input

    @use_item_input.setter
    def use_item_input(self, value):
        self._use_item_input = value

    def __getitem__(self, index):
        return self

    def __setitem__(self, index, value):
        self.car_id = index
        self._steer_input = value.steer_input
        self._throttle_input = value.throttle_input
        self._pitch_input = value.pitch_input
        self._roll_input = value.roll_input
        self._jump_input = value.jump_input
        self._boost_input = value.boost_input
        self._handbrake_input = value.handbrake_input
        self._use_item_input = value.use_item_input

# Create a global PlayerData instance
global_player_data = defaultdict(PlayerData)
