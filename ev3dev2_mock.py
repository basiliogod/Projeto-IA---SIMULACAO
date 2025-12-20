import random

class MockDevice:
    def __init__(self, address=None): self.address = address
    def off(self): pass

class MoveTank(MockDevice):
    def __init__(self, left, right): super().__init__()
    def on(self, left_speed, right_speed): pass
    def on_for_rotations(self, left, right, rot): pass
    def off(self): pass

class MediumMotor(MockDevice):
    def on_for_seconds(self, speed, seconds): pass

class ColorSensor(MockDevice):
    def __init__(self, port): 
        super().__init__(port)
        self.mode = None
    @property
    def color_name(self):
        return random.choice(['Red', 'White', 'Black', 'Blue', 'Green', 'Yellow', 'Brown','None'])

class UltrasonicSensor(MockDevice):
    @property
    def distance_centimeters(self):
        return random.uniform(5.0, 39.0)

class GyroSensor(MockDevice):
    def __init__(self, port):
        super().__init__(port)
        self.angle = 0
    def reset(self): self.angle = 0

class Sound:
    def beep(self): print("*BEEP*")
    def play_file(self, file, volume=100): print(f"Tocando: {file}")

def SpeedPercent(value): return value

OUTPUT_A, OUTPUT_B, OUTPUT_C = 'outA', 'outB', 'outC'
INPUT_1, INPUT_2, INPUT_4 = 'in1', 'in2', 'in4'