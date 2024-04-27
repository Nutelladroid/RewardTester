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
        self.steer_input: float = 0.0
        self.throttle_input: float = 0.0
        self.pitch_input: float = 0.0
        self.roll_input: float = 0.0
        self.jump_input: bool = False
        self.boost_input: bool = False
        self.handbrake_input: bool = False
        self.use_item_input: bool = False

    def __getitem__(self, index):
        return self

    def __setitem__(self, index, value):
        self.car_id = index
        self.steer_input = value.steer_input
        self.throttle_input = value.throttle_input
        self.pitch_input = value.pitch_input
        self.roll_input = value.roll_input
        self.jump_input = value.jump_input
        self.boost_input = value.boost_input
        self.handbrake_input = value.handbrake_input
        self.use_item_input = value.use_item_input

# Create a global PlayerData instance
global_player_data = defaultdict(PlayerData)
