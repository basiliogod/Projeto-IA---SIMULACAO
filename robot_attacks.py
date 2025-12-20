from time import sleep, time
from ev3dev2_mock import (MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, 
                              ColorSensor, UltrasonicSensor, GyroSensor, 
                              INPUT_1, INPUT_2, INPUT_4, Sound, SpeedPercent)

from config import LINE_COLOR_NAME

# Ataque de som
def sound_attack():
    speaker = Sound()
    speaker.beep()

# Ataque de toque
def touch_attack(tank_pair):
    tank_pair.on_for_rotations(SpeedPercent(-55), SpeedPercent(-55), 0.2)
    sleep(0.2)
    tank_pair.on_for_rotations(SpeedPercent(55), SpeedPercent(55), 0.2)

# Ataque de grua
def crane_attack(tank_pair, weapon_motor, color_sensor):
    
    # Fica de costas para o inimigo (-180º)
    tank_pair.on_for_rotations(SpeedPercent(30), SpeedPercent(30), 0.5)
    tank_pair.on(SpeedPercent(20), SpeedPercent(-20))
    sleep(1.0)
    while color_sensor.color_name != LINE_COLOR_NAME:
        sleep(0.01)
    tank_pair.off()
    tank_pair.on_for_rotations(SpeedPercent(20), SpeedPercent(20), 0.5)

    # Ativa o ataque (mexe o motor)
    weapon_motor.on_for_seconds(SpeedPercent(70), seconds=2)

    # Volta à posição inicial (+180º)
    tank_pair.on_for_rotations(SpeedPercent(-20), SpeedPercent(-20), 0.5)
    tank_pair.on(SpeedPercent(-20), SpeedPercent(20))
    sleep(1.0)
    while color_sensor.color_name != LINE_COLOR_NAME:
        sleep(0.01)
    tank_pair.off()
    tank_pair.on_for_rotations(SpeedPercent(-20), SpeedPercent(-20), 0.5)