import random
from time import sleep, time
from ev3dev2_mock import (MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, 
                              ColorSensor, UltrasonicSensor, GyroSensor, 
                              INPUT_1, INPUT_2, INPUT_4, Sound, SpeedPercent)

from tools import print_initial_setup, roll_digital_dice, clamp_speed
from enemy_class import ENEMY_STATS, Enemy
from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot
from robot_attacks import touch_attack, sound_attack, crane_attack
from game_logic import check_game_status, handle_game_over
from robot_movement_logic import search_enemies
from robot_attack_logic import robot_turn_logic
from enemy_attack_logic import enemy_attack_phase

# Inicializa o robot
def initialize_robot():
    robot = Robot()
    print("\nRobot inicializado com {:.0f}HP e {:.0f}EN.".format(robot.current_health, robot.energy))
    return robot



# Cria um array de instâncias de inimigos correspondentes ao array de cores detetados no ambiente pelo robot
def initialize_enemies_by_color(type_list, current_turn,global_enemies):
    enemy_object_list = []

    for i, unit_type in enumerate(type_list):
        if unit_type is None:
            enemy_object_list.append(None) 

        else:
            if global_enemies[i] is None:
                if unit_type in ENEMY_STATS:
                    new_enemy = Enemy(unit_type, current_turn, i+1)
                    enemy_object_list.append(new_enemy)
                    print("Slot {}: Criado inimigo '{}'".format(i+1, unit_type))
                else:
                    print("Slot {}: Inimigo ignorado (Tipo desconhecido: '{}').".format(i+1, unit_type))
                    enemy_object_list.append(None)
            else:
                enemy_object_list.append(None)        

    return enemy_object_list