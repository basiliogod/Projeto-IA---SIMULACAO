from ev3dev2_mock import (MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, 
                              ColorSensor, UltrasonicSensor, GyroSensor, 
                              INPUT_1, INPUT_2, INPUT_4, Sound, SpeedPercent)
import os
import random



# Rola dado 
def roll_digital_dice():
    return random.randint(1, 6)


BATTLE_MAP = {} 
# Imprime a tabela do enunciado preenchida
def print_initial_setup():
    BATTLE_MAP.clear()
    
    print("=" * 60)
    print("{:<10} | {:<18} | {:<20}".format("Posicao", "Tipo de atacante", "Turno inicial (1-6)"))
    print("=" * 60)
    
    unit_map = {
        "Tanque (Verde)": "Tank",
        "Artilharia (Amarelo)": "Artillery",
        "Infantaria (Azul)": "Infantry"
    }
    
    for i in range(1, 7):
        dice_type = roll_digital_dice()
        dice_turn = roll_digital_dice()
    
        if dice_type <= 2:
            unit = "Tanque (Verde)"
        elif dice_type <= 4:
            unit = "Artilharia (Amarelo)"
        else:
            unit = "Infantaria (Azul)"
            
        BATTLE_MAP[i] = {
            'unit_type': unit_map[unit],
            'spawn_turn': dice_turn
        }
    
        print("Slot{:<4} | {:<18} | {:<20}".format(i, unit, dice_turn))
    
    print("=" * 60)



# Garante que a velocidade do motor está entre -100 e 100
def clamp_speed(speed):
    if speed > 100:
        return 100
    if speed < -100:
        return -100
    return speed



# Toca musica de fundo em loop até o evento de paragem ser ativado
# Usado para tocar musica enquanto o robo faz o reconhecimento do ambiente
def background_music_loop(stop_event):
    speaker = Sound()
    
    SOUND_FILE = 'search_song.wav'

    while not stop_event.is_set():
        try:
            pass
            #speaker.play_file(SOUND_FILE, volume=100)
        except Exception as e:
            print("Erro: Nao foi possivel encontrar o ficheiro de musica 'search_song.wav': {}".format(e))
            return



def playSound(sound):
    speaker = Sound()
    #speaker.play_file(sound, volume=100)
    pass