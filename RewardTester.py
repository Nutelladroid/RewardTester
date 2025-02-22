import time
import numpy as np
import keyboard

from rlbot.agents.base_script import BaseScript
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator, GameInfoState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.messages.flat.PlayerInputChange import PlayerInputChange
from rlbot.socket.socket_manager import SocketRelay
import threading

from Utils.game_state import GameState
from Utils.physics_object import PhysicsObject
from Utils.player_data import PlayerData, global_player_data

from reward_functions import (
    DistanceToBallReward,
    FaceBallReward,
    VelocityBallToGoalReward,
    TouchBallReward,
    EventReward,
    VelocityReward,
    SaveBoostReward,
    VelocityPlayerToBallReward,
    FlipResetReward,
    DribbleReward,
    LiuDistanceBallToGoalReward,
    LiuDistancePlayerToBallReward,
    AerialDistanceReward,
    PositiveRollReward,
    HoldInputReward,
)

class RewardTester(BaseScript):
    def __init__(self):
        super().__init__("Reward Tester")
        self.tick_skip = 8
        self.game_state = GameState(self.get_field_info(), self.tick_skip)
        self.ticks = 0
        self.total_step_reward = 0
        self.total_average_step_reward = 0
        self.total_cumulative_reward = 0
        self.num_steps = 0
        self.player_rewards = {}
        self.socket_relay = SocketRelay()
        self.player_data = None

        # ***PRINT SETTINGS***
        self.print_individual_rewards = True  
        self.print_individual_total_rewards = True  
        self.print_general_rewards = True  
        self.players_to_print = None #[0, 1]  # List of player IDs to print example = [0, 1], or None to print all players

        # ***RENDER SETTINGS***
        self.enable_rendering = True  
        self.enable_individual_reward_rendering = True
        self.enable_general_reward_rendering = True 
        self.render_duration = 0.1  # Clear the text after x seconds
        self.last_render_time = 0
        self.render_text_queue = []  # List to store the text to be rendered
        self.players_to_render = self.players_to_print  # Default to the same as players_to_print

        # Create a dictionary that maps reward functions to their weights
        self.reward_functions = {
            EventReward({
                'teamGoal': 0.0,
                'concede': -0.0,
                'touch': 0.0,
                'shot': 0.0,
                'save': 0.0,
                'demo': 0.0,
                'demoed': -0.0,
                'boostPickup': 0.00,
                'assist': 0.0
            }): 1.0,
            
            HoldInputReward({
                'positive_steer': 0.0,
                'negative_steer': 0.0,
                'positive_throttle': 0.0,
                'negative_throttle': 0.0,
                'positive_pitch': 0.0,
                'negative_pitch': 0.0,
                'positive_roll': 0.0,
                'negative_roll': 0.0,
                'jump': 0.0,
                'boost': 0.0,
                'handbrake': 0.0,
                'use_item': 0.0
            }): 0.0,
            
            FaceBallReward(): 0.0,
            
            VelocityBallToGoalReward(): 0.0,
            
            TouchBallReward(aerial_weight=0.5): 0.0,
            
            VelocityReward(): 0.0,
            
            SaveBoostReward(): 0.0,
            
            VelocityPlayerToBallReward(): 0.0,
            
            FlipResetReward(flip_reset_r=1.0, hold_flip_reset_r=0.01): 00.0,
            
            DribbleReward(): 0.0,
            
            LiuDistanceBallToGoalReward(): 0.0,
            
            LiuDistancePlayerToBallReward(): 0.0,
            
            DistanceToBallReward(): 0.0,
            
            AerialDistanceReward(height_scale=10.0, distance_scale=10.0, ang_vel_w=0.0): 0.0,
            
            PositiveRollReward(height_threshold=300.0, distance_threshold=300.0): 0.0,
            
        }

        self.reset_thread = threading.Thread(target=self.reset_rewards, daemon=True)
        self.reset_thread.start()

    def reset_rewards(self):
        while True:
            if keyboard.is_pressed('r'):
                self.total_step_reward = 0
                self.total_average_step_reward = 0
                self.total_cumulative_reward = 0
                self.num_steps = 0
                self.player_rewards = {}
                print("Rewards reset.")
            time.sleep(0.1)

    def calculate_reward(self, player_data: PlayerData) -> float:
        # Synchronize player data with global player data
        player_data.steer_input = global_player_data[player_data.car_id].steer_input
        player_data.throttle_input = global_player_data[player_data.car_id].throttle_input
        player_data.pitch_input = global_player_data[player_data.car_id].pitch_input
        player_data.roll_input = global_player_data[player_data.car_id].roll_input
        player_data.jump_input = global_player_data[player_data.car_id].jump_input
        player_data.boost_input = global_player_data[player_data.car_id].boost_input
        player_data.handbrake_input = global_player_data[player_data.car_id].handbrake_input
        player_data.use_item_input = global_player_data[player_data.car_id].use_item_input

        reward = 0
        for reward_function, weight in self.reward_functions.items():
            reward += reward_function.get_reward(player_data, self.game_state, None) * weight
        return reward

    def handle_input_change(self, change: PlayerInputChange, seconds: float, frame_num: int):
        player_index = change.PlayerIndex()
        controller_state = change.ControllerState()

        global_player_data[player_index].car_id = player_index
        global_player_data[player_index]._steer_input = controller_state.Steer()
        global_player_data[player_index]._throttle_input = controller_state.Throttle()
        global_player_data[player_index]._pitch_input = controller_state.Pitch()
        global_player_data[player_index]._roll_input = controller_state.Roll()
        global_player_data[player_index]._jump_input = controller_state.Jump()
        global_player_data[player_index]._boost_input = controller_state.Boost()
        global_player_data[player_index]._handbrake_input = controller_state.Handbrake()
        global_player_data[player_index]._use_item_input = controller_state.UseItem()

    def start(self):
        print("Connecting SocketRelay...")
        self.socket_relay.player_input_change_handlers.append(self.handle_input_change)
        self.socket_relay_thread = threading.Thread(target=self.socket_relay.connect_and_run, args=(True, True, True))
        self.socket_relay_thread.start()
        print("SocketRelay connected and running")

        while True:
            # Wait for a packet
            packet = self.wait_game_tick_packet()

            if not packet.game_info.is_round_active:
                self.reset_game_state(packet)
                self.clear_text_if_expired()
                continue

            self.ticks += 1
            if self.ticks < self.tick_skip:
                continue
            self.ticks = 0

            print("--------------------------")
            self.game_state.decode(packet)
            self.reset_game_state(packet)

            if self.players_to_render is None:
                self.players_to_render = list(range(len(self.game_state.players)))
            step_reward = 0
            player_rewards = []
            for player_data in self.game_state.players:
                player_reward = self.calculate_reward(player_data)
                step_reward += player_reward
                player_rewards.append(player_reward)

                if player_data.car_id not in self.player_rewards:
                    self.player_rewards[player_data.car_id] = {'current_reward': 0, 'average_step_reward': 0, 'total_reward': 0}

                self.player_rewards[player_data.car_id]['current_reward'] = player_reward
                self.player_rewards[player_data.car_id]['total_reward'] += player_reward

                # Check if the player should be printed
                if self.print_individual_rewards and (self.players_to_print is None or player_data.car_id in self.players_to_print):
                    print(f"Player {player_data.car_id} current reward: {self.player_rewards[player_data.car_id]['current_reward']:.6f}")
                    print(f"Player {player_data.car_id} average step reward: {self.player_rewards[player_data.car_id]['average_step_reward']:.6f}")

            self.total_step_reward += step_reward
            self.num_steps += 1
            self.total_average_step_reward = self.total_step_reward / self.num_steps
            self.total_cumulative_reward = sum(player_reward['total_reward'] for player_reward in self.player_rewards.values()) / len(self.game_state.players)

            for player_id, player_data in self.player_rewards.items():
                player_data['average_step_reward'] = player_data['total_reward'] / self.num_steps

            if self.print_individual_total_rewards:
                for player_id, player_data in self.player_rewards.items():
                    if self.players_to_print is None or player_id in self.players_to_print:
                        print(f"Player {player_id} total reward: {player_data['total_reward']:.6f}")

            if self.print_general_rewards:
                print(f"Total step reward: {step_reward:.6f}")
                print(f"Total average step reward: {self.total_average_step_reward:.6f}")
                print(f"Total cumulative reward: {self.total_cumulative_reward:.6f}")

            # Append the individual player data to the render queue
            if self.enable_individual_reward_rendering:
                for player_id in self.players_to_render:
                    if player_id in self.player_rewards:
                        self.render_text_queue.append(f"Player {player_id} current reward: {self.player_rewards[player_id]['current_reward']:.6f}\n")
                        self.render_text_queue.append(f"Player {player_id} average step reward: {self.player_rewards[player_id]['average_step_reward']:.6f}\n")
                        self.render_text_queue.append(f"Player {player_id} total reward: {self.player_rewards[player_id]['total_reward']:.6f}\n")
            # Append the general reward text to the render queue
            if self.enable_general_reward_rendering:
                self.render_text_queue.append(f"Total step reward: {step_reward:.6f}\n")
                self.render_text_queue.append(f"Total average step reward: {self.total_average_step_reward:.6f}\n")
                self.render_text_queue.append(f"Total cumulative reward: {self.total_cumulative_reward:.6f}\n")

            self.render_all_text()

            print("--------------------------")

    def render_all_text(self):
        if self.enable_rendering and self.render_text_queue:
            self.game_interface.renderer.begin_rendering()
            y_offset = 30
            x_offset = 20
            render_count = 0
            total_text = len(self.render_text_queue)-(self.enable_general_reward_rendering)*3
            if total_text > 0:
                for text in self.render_text_queue:
                    self.game_interface.renderer.draw_string_2d(x_offset, y_offset, 1, 1, text, self.renderer.lime())
                    y_offset += 30
                    render_count += 1
                    if render_count % ((total_text) // 2) == 0:
                        if x_offset == 20:
                            x_offset = 1500
                            y_offset -= 30*((total_text) // 2)
                        else:
                            x_offset = 20
            self.game_interface.renderer.end_rendering()
            self.last_render_time = time.time()
            self.render_text_queue.clear()  # Clear the render queue after rendering

    def reset_game_state(self, packet):
        self.game_state.decode(packet)

    def clear_text_if_expired(self):
        if self.enable_rendering and time.time() - self.last_render_time > self.render_duration:
            self.game_interface.renderer.begin_rendering()
            self.game_interface.renderer.draw_string_2d(20, 100, 1, 1, "", self.renderer.lime())
            self.game_interface.renderer.end_rendering()

if __name__ == "__main__":
    reward_tester = RewardTester()
    reward_tester.start()
