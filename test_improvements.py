import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# To be able to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_game_loop
from initialize_robot_enemies import initialize_robot
from hardware import initialize_hardware

class TestWinRateImprovements(unittest.TestCase):

    def run_simulation(self, num_simulations=100):
        """
        Runs the simulation for a given number of times and returns the win rate.
        """
        wins = 0
        defeats = 0

        # Redirect stdout to devnull to suppress prints
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

        for _ in range(num_simulations):
            enemies = [None] * 6
            # Mock hardware
            tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor = MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()

            robot = initialize_robot()
            status = run_game_loop(
                robot=robot,
                tank_pair=tank_pair,
                medium_motor=medium_motor,
                color_sensor=color_sensor,
                us_sensor=us_sensor,
                gyro=gyro_sensor,
                spin_speed=20,
                forward_speed=-20,
                enemies=enemies
            )

            if status == "victory":
                wins += 1
            elif status == "defeat":
                defeats += 1
        
        # Restore stdout
        sys.stdout.close()
        sys.stdout = original_stdout

        win_rate = wins / num_simulations if num_simulations > 0 else 0
        return win_rate

    def test_baseline_win_rate(self):
        """
        Test the baseline win rate of the simulation without any changes.
        """
        win_rate = self.run_simulation()
        print(f"Baseline Win Rate: {win_rate:.2%}")
        # The user mentioned the win rate is around 60-65%, so let's assert that.
        # We'll give it a bit of a margin for randomness.
        self.assertTrue(0.55 <= win_rate <= 0.70)

if __name__ == '__main__':
    unittest.main()
