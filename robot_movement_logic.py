from time import sleep, time
import random
import threading
import os
from ev3dev2_mock import (MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, 
                              ColorSensor, UltrasonicSensor, GyroSensor, 
                              INPUT_1, INPUT_2, INPUT_4, Sound)
from tools import clamp_speed
from config import OBJECT_SEARCH_DISTANCE_CM, LINE_COLOR_NAME, SPIN_SEARCH_SPEED, SEARCH_TIME_LEFT_S, SEARCH_TIME_RIGHT_S
from tools import background_music_loop
from tools import BATTLE_MAP

# Segue em linha reta com correção do giroscópio
def follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    left_speed = clamp_speed(base_speed + turn_power)
    right_speed = clamp_speed(base_speed - turn_power)
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))



# Gira o robô para a esquerda ou direita
def perform_search_spin(tank_pair, color_sensor, us_sensor, duration_s, left_speed, right_speed, distance_check_func):
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))
    start_search_time = time()
    while (time() - start_search_time) < duration_s:
        if color_sensor.color_name == LINE_COLOR_NAME:
            return 'FOUND_LINE'
        current_distance = us_sensor.distance_centimeters
        if distance_check_func(current_distance):
            return 'TARGET_REACHED'
        sleep(0.01)
    return 'NOT_FOUND'



# Reorienta o robot quando perde a linha vermelha
def search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro, distance_check_func):
    tank_pair.off()
    
    # Procura à esquerda
    search_result = perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_LEFT_S,
        left_speed=SPIN_SEARCH_SPEED,
        right_speed=-SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )
    
    # Encontra a linha à esquerda
    if search_result == 'FOUND_LINE':
        gyro.reset()
        return 'FOUND_LINE'
    
    # Encontra um inimigo ao regressar à linha a partir da esquerda
    if search_result == 'TARGET_REACHED':
        return 'TARGET_REACHED'

    # Não encontrou à esquerda, vai procurar à direita
    search_result = perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_RIGHT_S,
        left_speed=-SPIN_SEARCH_SPEED,
        right_speed=SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )

    # Encontra a linha à direita
    if search_result == 'FOUND_LINE':
        gyro.reset()
        return 'FOUND_LINE'

    # Encontra um inimigo ao regressar à linha a partir da direita
    if search_result == 'TARGET_REACHED':
        return 'TARGET_REACHED'
    
    # Não encontrou a linha à direita, nem à esquerda
    print("Perdi-me! Nao consigo encontrar a linha vermelha!") # O 'ã' em 'Nao' foi removido para evitar erros de codificacao.
    return 'NOT_FOUND'



# Deixa a linha vermelha
def leave_current_line(tank_pair, color_sensor, spin_speed):
    tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))



# Regressa ao centro após se aproximar do inimigo
def follow_line_return_to_distance(tank_pair, gyro, color_sensor, us_sensor, return_speed, kp, target_distance_cm):
    gyro.reset()
    target_angle = 0

    # Pequeno recuo cego para trás para sair da cor do inimigo 
    tank_pair.on_for_rotations(SpeedPercent(30), SpeedPercent(30), 0.5)

    stop_condition_check = lambda dist: dist >= target_distance_cm
    while not stop_condition_check(us_sensor.distance_centimeters):
        if color_sensor.color_name == LINE_COLOR_NAME:
            follow_straight_on_line(tank_pair, gyro, return_speed, kp, target_angle)
        else:
            search_status = search_for_lost_line(
                tank_pair, color_sensor, us_sensor, gyro,
                distance_check_func=stop_condition_check
            )
            if search_status == 'FOUND_LINE':
                target_angle = 0
                continue
            else:
                break 
        sleep(0.01)
    tank_pair.off()



# Aproxima-se do inimigo até chegar a uma certa distância
def follow_line_until_obstacle(tank_pair, gyro, color_sensor, us_sensor, base_speed, kp):
    
    dist_phase_1 = 15   # Distância para ficar do inimigo antes de chegar à cor do inimigo (cartolina no chão à frente do inimigo)
    dist_phase_2 = 8    # Distância para ficar do inimigo após cobrir a cor do inimigo (cartolina no chão à frente do inimigo)
    
    # Fase 1 - Ficar a dist_phase_1 do inimigo (antes de chegar à cor do inimigo)
    gyro.reset()
    target_angle = 0
    while us_sensor.distance_centimeters > dist_phase_1:
        if color_sensor.color_name == LINE_COLOR_NAME:
            follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle)
        else:
            search_status = search_for_lost_line(
                tank_pair, color_sensor, us_sensor, gyro,
                distance_check_func=lambda d: d <= dist_phase_1
            )
            if search_status == 'FOUND_LINE':
                target_angle = 0
                continue
            else:
                break 
        sleep(0.01)

    # Fase 2 - Ficar a dist_phase_2 do inimigo (após cobrir cor do inimigo)
    gyro.reset() 
    while us_sensor.distance_centimeters > dist_phase_2:
        current_angle = gyro.angle
        error = 0 - current_angle
        correction = error * kp
        left_speed = clamp_speed(base_speed - correction)
        right_speed = clamp_speed(base_speed + correction)
        tank_pair.on(left_speed, right_speed)
        sleep(0.01)

    tank_pair.off()



def search_enemies(tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed, enemies, current_turn):
    print(f"\n[SIMULAÇÃO] Robô escaneando slots no Turno {current_turn}...")
    
    enemies_log = ["Empty"] * 6
    
    for slot_idx in range(1, 7): # De 1 a 6
        data = BATTLE_MAP.get(slot_idx)
        
        # O inimigo só é "detectado" se o turno atual >= turno de spawn
        if data and current_turn >= data['spawn_turn']:
            # Se o inimigo ainda não foi morto
            if enemies[slot_idx - 1] is None:
                # GUARDAMOS O TIPO (ex: 'Tank') em vez da cor
                unit_type = data['unit_type']
                print(f"Slot {slot_idx}: Detectado {unit_type} (Surgiu no Turno {data['spawn_turn']})")
                enemies_log[slot_idx - 1] = unit_type
            else:
                # Se já existe no array 'enemies', pegamos o tipo dele
                unit_type = enemies[slot_idx - 1].type
                print(f"Slot {slot_idx}: Inimigo {unit_type} já conhecido/em combate.")
                enemies_log[slot_idx - 1] = unit_type
        else:
            print(f"Slot {slot_idx}: Vazio (Aguardando turno de surgimento).")
            enemies_log[slot_idx - 1] = None
            
    return enemies_log


# Gira o robot no centro do campo de batalha até encontrar a linha do slot alvo.
# Uma vez na linha correta, avança em direção ao inimigo, executa uma ação (ataque) e depois regressa à sua posição inicial no centro.
def rotate_perform_action_return(tank_pair, color_sensor, gyro, us_sensor, spin_speed, forward_speed, scheduled_actions):

    FULL_TURN_MIN_ANGLE = 340           # Ângulo mínimo para considerar que o robot deu uma volta completa
    SKIPPED_LINE_ANGLE_THRESHOLD = 90   # Ângulo acima do qual o robot considera que saltou uma ou mais linhas
    EXPECTED_SEGMENT_ANGLE = 60         # Ângulo esperado entre duas linhas consecutivas
    KP_GAIN = 1.5                 

    # Funcao para atacar
    def check_and_attack(current_idx):
       
        # Verifica se o índice da linha atual esta na lista de acoes agendadas
        if current_idx in scheduled_actions:
            print("Linha {} (Alvo) alcancada. A verificar se existe inimigo...".format(current_idx))
            
            sleep(0.1) 
            distance_cm = us_sensor.distance_centimeters
            
            # Se um objeto for detetado dentro da distância definida, inicia a sequência de ataque
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:
                print("Inimigo detetado a {}cm. A aproximar...".format(distance_cm)) 
                
                # Avança em direção ao inimigo
                follow_line_until_obstacle(
                    tank_pair=tank_pair, 
                    gyro=gyro, 
                    color_sensor=color_sensor,
                    us_sensor=us_sensor, 
                    base_speed=forward_speed, 
                    kp=KP_GAIN
                )
                
                tank_pair.off()
                sleep(0.5)

                # Executa a ação de ataque passada como callback
                scheduled_actions[current_idx]()
                
                # Recua para a distância original para se preparar para a próxima rotação
                return_speed = forward_speed * -1
                follow_line_return_to_distance(
                    tank_pair=tank_pair, 
                    gyro=gyro, 
                    color_sensor=color_sensor,
                    us_sensor=us_sensor, 
                    return_speed=return_speed, 
                    kp=KP_GAIN, 
                    target_distance_cm=distance_cm - 2
                )
            else:
                print("Nao existe nenhum inimigo no slot para atacar.")
            

            tank_pair.off()
            sleep(0.2)

    try:
        gyro.reset()
        tank_pair.off()
        
        # Variáveis para controlar a rotação e a posição
        accumulated_angle = 0
        current_line_index = 0
        scanning = True
        
        print("A iniciar rotina de rotacao para ataques multiplos. Alvos: {}".format(list(scheduled_actions.keys())))
        
        # Verifica a posição inicial (linha 0) antes de começar a girar
        check_and_attack(current_line_index)

        # Loop principal para girar e encontrar as linhas
        while scanning:
            
            # Condição de paragem: se o robot deu uma volta completa ou passou por todas as 6 linhas
            if accumulated_angle >= FULL_TURN_MIN_ANGLE or current_line_index >= 6:
                print("Volta completa. De regresso a posicao inicial.")
                break

            gyro.reset()
            
            # Gira para sair da linha atual
            tank_pair.on(left_speed=spin_speed * -1, right_speed=spin_speed)
            sleep(0.5) 

            # Continua a girar até o sensor de cor detetar a próxima linha vermelha
            while color_sensor.color_name != LINE_COLOR_NAME:
                sleep(0.01)
            
            tank_pair.off()

            # Calcula o ângulo percorrido para chegar à nova linha
            segment_angle = abs(gyro.angle)
            accumulated_angle += segment_angle
            
            # Lógica para corrigir se o robot saltar uma ou mais linhas
            if segment_angle > SKIPPED_LINE_ANGLE_THRESHOLD and current_line_index < 5:
                num_skipped = round(segment_angle / EXPECTED_SEGMENT_ANGLE) - 1
                if num_skipped > 0:
                    print("O robot saltou {} linha(s). A corrigir indice.".format(num_skipped))
                    current_line_index += num_skipped

            current_line_index += 1
            print("Chegou a Linha {}".format(current_line_index)) 
            
            # Verifica se a linha atual é o alvo e ataca se for
            check_and_attack(current_line_index)
            
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
        raise
    except Exception as e:
        print("Erro durante a rotacao e ataque: {}".format(e)) 
    finally:
        tank_pair.off()