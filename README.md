# Reward Tester

## Description

Script for RLBot which prints reward values.

![Logo](https://github.com/Nutelladroid/RewardTester/blob/main/logo.png?raw=true)


## How to use
### Add the script to RLBot

Add the cfg file to RLbot. Remember to toggle Reward Tester in the script section once added.

### Add Reward

Create your reward and add it to **reward_functions.py** and import the reward in **RewardTester.py** :

`from reward_functions import (ExampleReward)`

Add it to : 

`self.reward_functions = {ExampleReward(): 1.0}`


### Print Settings

Check the print settings in **RewardTester.py**. Here you can decide what to print in the terminal.
```
    self.print_individual_rewards = True 
    self.print_individual_total_rewards = True 
    self.print_general_rewards = False 
```
This will only print the individual rewards of players with index 0 and 1
```
    self.players_to_print = [0, 1] 
```
*or*

This will print the individual rewards of all the players 
```
    self.players_to_print = None 
```

### Run Game
Once everything is set, just run the game in window mode and look at the terminal






## Used code from:

https://github.com/JPK314/rlgym-compat (27 April 2024)

https://github.com/RLBot/RLBot/tree/master (27 April 2024)

