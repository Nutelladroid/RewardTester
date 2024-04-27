import numpy as np
from Utils.common_values import BALL_RADIUS, CAR_MAX_SPEED, BALL_MAX_SPEED, ORANGE_GOAL_BACK, BLUE_GOAL_BACK, BACK_NET_Y, BACK_WALL_Y, CEILING_Z, SIDE_WALL_X
from Utils.player_data import global_player_data


from collections import defaultdict

class EventReward:
    def __init__(self, weight_scales):
        self.weights = {
            'team_goals': weight_scales.get('teamGoal', 0.0),
            'opponent_goals': weight_scales.get('concede', 0.0),
            'touch': weight_scales.get('touch', 0.0),
            'shots': weight_scales.get('shot', 0.0),
            'saves': weight_scales.get('save', 0.0),
            'demos': weight_scales.get('demo', 0.0),
            'demoed': weight_scales.get('demoed', 0.0),
            'boost_fraction': weight_scales.get('boostPickup', 0.0),
            'assists': weight_scales.get('assist', 0.0)
        }
        self.prev_values = defaultdict(dict)

    def get_reward(self, player_data, game_state, prev_action):
        team_goals = game_state.scoreLine[int(player_data.team_num)]
        opponent_goals = game_state.scoreLine[1 - int(player_data.team_num)]
        car_id = player_data.car_id

        reward = 0

        if car_id not in self.prev_values:
            self.prev_values[car_id] = {
                'team_goals': team_goals,
                'opponent_goals': opponent_goals,
                'touch': player_data.ball_touched,
                'shots': player_data.match_shots,
                'saves': player_data.match_saves,
                'demos': player_data.match_demolishes,
                'demoed': player_data.is_demoed,
                'boost_fraction': player_data.boost_amount,
                'assists': player_data.match_assists
            }
        else:
            prev_values = self.prev_values[car_id]
            reward += self.weights['team_goals'] * (team_goals > prev_values['team_goals'])
            reward += self.weights['opponent_goals'] * (opponent_goals > prev_values['opponent_goals'])
            reward += self.weights['touch'] * (player_data.ball_touched and not prev_values['touch'])
            reward += self.weights['shots'] * (player_data.match_shots > prev_values['shots'])
            reward += self.weights['saves'] * (player_data.match_saves > prev_values['saves'])
            reward += self.weights['demos'] * (player_data.match_demolishes > prev_values['demos'])
            reward += self.weights['demoed'] * (player_data.is_demoed and not prev_values['demoed'])
            reward += self.weights['boost_fraction'] * (player_data.boost_amount > prev_values['boost_fraction'])
            reward += self.weights['assists'] * (player_data.match_assists > prev_values['assists'])

            self.prev_values[car_id] = {
                'team_goals': team_goals,
                'opponent_goals': opponent_goals,
                'touch': player_data.ball_touched,
                'shots': player_data.match_shots,
                'saves': player_data.match_saves,
                'demos': player_data.match_demolishes,
                'demoed': player_data.is_demoed,
                'boost_fraction': player_data.boost_amount,
                'assists': player_data.match_assists
            }

        return reward


class VelocityReward:
    def __init__(self, is_negative=False):
        self.is_negative = is_negative

    def get_reward(self, player_data, game_state, prev_action):
        return np.linalg.norm(player_data.car_data.linear_velocity) / CAR_MAX_SPEED * (1 - 2 * self.is_negative)

class SaveBoostReward:
    def __init__(self, exponent=0.5):
        self.exponent = exponent

    def get_reward(self, player_data, game_state, prev_action):
        return np.clip(player_data.boost_amount ** self.exponent, 0, 1)

class VelocityBallToGoalReward:
    def __init__(self, own_goal=False):
        self.own_goal = own_goal

    def get_reward(self, player_data, game_state, prev_action):
        target_orange_goal = player_data.team_num == 0
        if self.own_goal:
            target_orange_goal = not target_orange_goal

        target_pos = ORANGE_GOAL_BACK if target_orange_goal else BLUE_GOAL_BACK
        ball_dir_to_goal = (target_pos - game_state.ball.position) / np.linalg.norm(target_pos - game_state.ball.position)
        return ball_dir_to_goal.dot(game_state.ball.linear_velocity / BALL_MAX_SPEED)

class VelocityPlayerToBallReward:
    def get_reward(self, player_data, game_state, prev_action):
        dir_to_ball = (game_state.ball.position - player_data.car_data.position) / np.linalg.norm(game_state.ball.position - player_data.car_data.position)
        norm_vel = player_data.car_data.linear_velocity / CAR_MAX_SPEED
        return dir_to_ball.dot(norm_vel)

class FaceBallReward:
    def get_reward(self, player_data, game_state, prev_action):
        dir_to_ball = (game_state.ball.position - player_data.car_data.position) / np.linalg.norm(game_state.ball.position - player_data.car_data.position)
        return player_data.car_data.forward().dot(dir_to_ball)

class TouchBallReward:
    def __init__(self, aerial_weight=0):
        self.aerial_weight = aerial_weight

    def get_reward(self, player_data, game_state, prev_action):
        if player_data.ball_touched:
            ball_height = game_state.ball.position[2] + BALL_RADIUS
            return (ball_height / (BALL_RADIUS * 2)) ** self.aerial_weight
        else:
            return 0

class DistanceToBallReward:
    def __init__(self):
        pass

    def get_reward(self, player_data, game_state, prev_action):
        distance_to_ball = np.linalg.norm(player_data.car_data.position - game_state.ball.position)
        return max(0, 1 - distance_to_ball / (BALL_RADIUS * 2))

class DribbleReward:
    def get_reward(self, player_data, game_state, prev_action):
        MIN_BALL_HEIGHT = 109.0
        MAX_BALL_HEIGHT = 180.0
        MAX_DISTANCE = 197.0
        SPEED_MATCH_FACTOR = 2.0

        if (
            player_data.on_ground
            and MIN_BALL_HEIGHT <= game_state.ball.position[2] <= MAX_BALL_HEIGHT
            and np.linalg.norm(player_data.car_data.position - game_state.ball.position) < MAX_DISTANCE
        ):
            player_speed = np.linalg.norm(player_data.car_data.linear_velocity)
            ball_speed = np.linalg.norm(game_state.ball.linear_velocity)
            speed_match_reward = (
                (player_speed / CAR_MAX_SPEED)
                + SPEED_MATCH_FACTOR
                * (1.0 - abs(player_speed - ball_speed) / (player_speed + ball_speed))
            ) / 2.0
            return speed_match_reward
        else:
            return 0.0

class FlipResetReward:
    def __init__(self, flip_reset_r=1.0, hold_flip_reset_r=0.01):
        self.flip_reset_r = flip_reset_r
        self.hold_flip_reset_r = hold_flip_reset_r
        self.prevhas_jump = defaultdict(bool)
        self.prevhas_flip = defaultdict(bool)
        self.has_reset = defaultdict(bool)

    def reset(self, initial_state):
        self.prevhas_jump.clear()
        self.prevhas_flip.clear()
        self.has_reset.clear()

    def get_reward(self, player_data, game_state, prev_action):
        CAR_UNDER_THRESHOLD = -1.0
        MIN_DISTANCE_FLOOR = 200.0
        MIN_DISTANCE_CEILING = 300.0
        MIN_DISTANCE_WALLS = 700.0
        ENABLE_MULTIPLE_RESETS = 1  # You might want to disable to prevent flip reset farming

        car_id = player_data.car_id
        reward = 0.0

        near_ball = np.linalg.norm(player_data.car_data.position - game_state.ball.position) < 170.0
        height_check = (player_data.car_data.position[2] < MIN_DISTANCE_FLOOR) or (player_data.car_data.position[2] > CEILING_Z - MIN_DISTANCE_CEILING)
        dir_to_ball = (game_state.ball.position - player_data.car_data.position) / np.linalg.norm(game_state.ball.position - player_data.car_data.position)
        Car_wheels_under = np.dot(player_data.car_data.up(), dir_to_ball) > CAR_UNDER_THRESHOLD
        wall_dis_check = ((-SIDE_WALL_X + MIN_DISTANCE_WALLS) > player_data.car_data.position[0]) or \
                         ((SIDE_WALL_X - MIN_DISTANCE_WALLS) < player_data.car_data.position[0]) or \
                         ((-BACK_WALL_Y + MIN_DISTANCE_WALLS) > player_data.car_data.position[1]) or \
                         ((BACK_WALL_Y - MIN_DISTANCE_WALLS) < player_data.car_data.position[1])

        can_jump = player_data.has_flip
        
        # player_data.has_jump = not player_info.jumped , so it only detects the initial reset . If you want to detect multiple resets you need to check if they've flipped. 
        gotReset = (self.prevhas_jump[car_id] < player_data.has_jump) or (ENABLE_MULTIPLE_RESETS * (self.prevhas_flip[car_id] < player_data.has_flip))

        if wall_dis_check or player_data.has_flipped:
            self.has_reset[car_id] = False

        if near_ball and not height_check and not wall_dis_check and Car_wheels_under:
            if gotReset and not self.has_reset[car_id]:
                self.has_reset[car_id] = True
                reward = self.flip_reset_r
        elif self.has_reset[car_id]:
            reward += self.hold_flip_reset_r

        self.prevhas_jump[car_id] = player_data.has_jump
        self.prevhas_flip[car_id] = player_data.has_flip
        return reward

class LiuDistanceBallToGoalReward:
    def __init__(self, own_goal=False):
        self.own_goal = own_goal

    def get_reward(self, player_data, game_state, prev_action):

        if (player_data.team_num == 0 and not self.own_goal) or (
            player_data.team_num == 1 and self.own_goal
        ):
            objective = ORANGE_GOAL_BACK
        else:
            objective = BLUE_GOAL_BACK

        dist = (
            np.linalg.norm(game_state.ball.position - objective)
            - (BACK_NET_Y - BACK_WALL_Y + BALL_RADIUS)
        )

        reward = np.exp(-0.5 * dist / BALL_MAX_SPEED)
        return reward

class LiuDistancePlayerToBallReward:
    def get_reward(self, player_data, game_state, prev_action):

        dist = np.linalg.norm(player_data.car_data.position - game_state.ball.position) - BALL_RADIUS

        reward = np.exp(-0.5 * dist / CAR_MAX_SPEED)
        return reward
        

class AerialDistanceReward:
    def __init__(self, height_scale, distance_scale, ang_vel_w):
        self.height_scale = height_scale
        self.distance_scale = distance_scale
        self.ang_vel_w = ang_vel_w
        self.ball_distance = defaultdict(float)
        self.car_distance = defaultdict(float)
        self.ang_vel_accumulated = defaultdict(float)
        self.prev_ball_pos = defaultdict(lambda: None)
        self.prev_car_pos = defaultdict(lambda: None)

    def get_reward(self, player_data, game_state, prev_action):
        car_id = player_data.car_id
        rew = 0.0

        # Test if player is on the ground
        if player_data.car_data.position[2] < 250:
            # Reset variables if the player lands on the ground
            self.ball_distance[car_id] = 0.0
            self.car_distance[car_id] = 0.0
            self.ang_vel_accumulated[car_id] = 0.0
            # Initialize prev_ball_pos and prev_car_pos if they are None
            if self.prev_ball_pos[car_id] is None:
                self.prev_ball_pos[car_id] = game_state.ball.position.copy()
            if self.prev_car_pos[car_id] is None:
                self.prev_car_pos[car_id] = player_data.car_data.position.copy()
        # First non-ground touch detection
        elif player_data.ball_touched:
            rew = self.height_scale * max(player_data.car_data.position[2] + game_state.ball.position[2] - 500, 0.0)
            self.prev_ball_pos[car_id] = game_state.ball.position.copy()
            self.prev_car_pos[car_id] = player_data.car_data.position.copy()
        # Still off the ground after a touch, add distance and reward for more touches
        elif not player_data.on_ground:
            self.car_distance[car_id] += np.linalg.norm(player_data.car_data.position - self.prev_car_pos[car_id])
            self.ball_distance[car_id] += np.linalg.norm(game_state.ball.position - self.prev_ball_pos[car_id])
            ang_vel_norm = np.linalg.norm(player_data.car_data.angular_velocity) / 5.5
            self.ang_vel_accumulated[car_id] += self.ang_vel_w * ang_vel_norm

            # Cash out on touches
            if player_data.ball_touched:
                rew = self.distance_scale * (self.car_distance[car_id] + self.ball_distance[car_id]) + self.ang_vel_accumulated[car_id]
                self.car_distance[car_id] = 0.0
                self.ball_distance[car_id] = 0.0
                self.ang_vel_accumulated[car_id] = 0.0
                self.prev_ball_pos[car_id] = game_state.ball.position.copy()
                self.prev_car_pos[car_id] = player_data.car_data.position.copy()

        return rew / (2 * 5120)


#The input rewards need to use global_player_data
#TODO make it not use global

class PositiveRollReward:
    def __init__(self, height_threshold=300.0, distance_threshold=500.0):
        self.height_threshold = height_threshold
        self.distance_threshold = distance_threshold

    def get_reward(self, player_data, game_state, prev_action):
        reward = 0.0
        if player_data.car_data.position[2] > self.height_threshold and \
           np.linalg.norm(player_data.car_data.position - game_state.ball.position) < self.distance_threshold and \
           global_player_data[player_data.car_id].roll_input > 0.0:
            reward = 1.0
        return reward

class HoldInputReward:
    def __init__(self, weights):
        self.weights = weights

    def get_reward(self, player_data, game_state, prev_action):
        reward = 0

        # Steer input
        if global_player_data[player_data.car_id].steer_input > 0:
            reward += self.weights['positive_steer']
        elif global_player_data[player_data.car_id].steer_input < 0:
            reward += self.weights['negative_steer']

        # Throttle input
        if global_player_data[player_data.car_id].throttle_input > 0:
            reward += self.weights['positive_throttle']
        elif global_player_data[player_data.car_id].throttle_input < 0:
            reward += self.weights['negative_throttle']

        # Pitch input
        if global_player_data[player_data.car_id].pitch_input > 0:
            reward += self.weights['positive_pitch']
        elif global_player_data[player_data.car_id].pitch_input < 0:
            reward += self.weights['negative_pitch']

        # Roll input
        if global_player_data[player_data.car_id].roll_input > 0:
            reward += self.weights['positive_roll']
        elif global_player_data[player_data.car_id].roll_input < 0:
            reward += self.weights['negative_roll']

        # Jump input
        if global_player_data[player_data.car_id].jump_input:
            reward += self.weights['jump']

        # Boost input
        if global_player_data[player_data.car_id].boost_input:
            reward += self.weights['boost']

        # Handbrake input
        if global_player_data[player_data.car_id].handbrake_input:
            reward += self.weights['handbrake']

        # Use item input
        if global_player_data[player_data.car_id].use_item_input:
            reward += self.weights['use_item']

        return reward








