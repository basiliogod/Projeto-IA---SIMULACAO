from time import sleep, time
from ev3dev2_mock import (MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, 
                              ColorSensor, UltrasonicSensor, GyroSensor, 
                              INPUT_1, INPUT_2, INPUT_4, Sound)

# Inicializa o hardware
def initialize_hardware():
    try:
        tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)
        print("Motores Tanque (B, C): OK")
        
        medium_motor = MediumMotor(OUTPUT_A)
        print("Motor Medio (A): OK")

        color_sensor = ColorSensor(INPUT_4)
        color_sensor.mode = 'COL-COLOR'
        print("Sensor de Cor (Porta 4): OK.")
        
        us_sensor = UltrasonicSensor(INPUT_1)
        us_sensor.mode = 'US-DIST-CM'
        print("Sensor Ultrassonico (Porta 1): OK.")
        
        gyro_sensor = GyroSensor(INPUT_2)
        gyro_sensor.mode = 'GYRO-ANG' 
        print("Sensor Giroscopio (Porta 2): OK.")
        
        sleep(2.0) 
        gyro_sensor.reset()
        
        return tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor
    except Exception as e:
        print("Ocorreu um erro na inicializacao dos sensores e motores: {}".format(e))
        return None, None, None, None, None