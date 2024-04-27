# Reward Tester

## Description

A script for RLBot that prints reward values.

![Logo](https://github.com/Nutelladroid/RewardTester/blob/main/logo.png?raw=true)

## Getting Started

### 1. Add the script to RLBot

Add the `cfg` file to RLBot and toggle Reward Tester in the script section.

### 2. Define and Add a Reward


Create your reward and add it to `reward_functions.py`. Then, import the reward in `RewardTester.py`:

```
from reward_functions import ExampleReward
```

Add the reward to the `self.reward_functions` dictionary:

```
self.reward_functions = {ExampleReward(): 1.0}
```
### 3. Configure Print Settings

In `RewardTester.py`, adjust the print settings to control what is printed in the terminal:
```
self.print_individual_rewards = True
self.print_individual_total_rewards = True
self.print_general_rewards = False
```
Choose which players to print individual rewards for:
```
self.players_to_print = [0, 1]  # or None to print all players
```
### 4. Adjust Tick Skip Setting

Modify the `tick_skip` value, keeping in mind its impact on your reward design:
```
self.tick_skip = 8
```
### 5. Run the Game

Run the game in window mode and observe the terminal output.

## Acknowledgments

This project uses code from:

* [JPK314/rlgym-compat](https://github.com/JPK314/rlgym-compat) (27 April 2024)
* [RLBot/RLBot](https://github.com/RLBot/RLBot/tree/master) (27 April 2024)
