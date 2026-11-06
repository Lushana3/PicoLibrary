"""
# main.py
# Main execution script to initialize hardware and run the digital door NamePlate on Raspberry Pi Pico / Wokwi
# Author: Lushana3
"""

from Displays import LCDDisplay
from Buzzer import PassiveBuzzer
from LightStrip import LightStrip
from Employee import Faculty, Staff, StudentWorker, Administrator
from NamePlate import NamePlate
from Log import *

def main():
    """
    Initialize physical hardware components, instantiate employees across
    all hierarchy subclasses, and run the NamePlate system on Raspberry Pi Pico / Wokwi.
    """
    Log.i("main.py: Initializing NamePlate hardware...")

    # Hardware components
    # 1. LCD Display via I2C (GP0 = SDA, GP1 = SCL)
    lcd = LCDDisplay(sda=0, scl=1)

    # 2. Passive Buzzer on GP16
    buzzer = PassiveBuzzer(pin=16)

    # 3. NeoPixel LightStrip on GP2 (8 LEDs, 0.5 brightness)
    lights = LightStrip(pin=2, numleds=8, brightness=0.5)

    # 24-hour calendar covering hours 0 to 23 with a mix of statuses
    admin_calendar = {
        0: "Away",       1: "Away",       2: "Away",       3: "Away",
        4: "Away",       5: "Away",       6: "Away",       7: "Away",
        8: "Available",  9: "Busy",      10: "Busy",      11: "Available",
        12: "Away",     13: "Available", 14: "Busy",      15: "Busy",
        16: "Available", 17: "Away",     18: "Away",      19: "Away",
        20: "Away",     21: "Away",      22: "Away",      23: "Away"
    }

    # Instantiate representative employees for all subclasses
    emp1 = Faculty(
        name="Dr. Ada Lovelace",
        title="Professor",
        phone="x4001",
        courses=["CS101", "CS201"],
        officeHours="MWF 10-12"
    )

    emp2 = Staff(
        name="Grace Hopper",
        title="Lab Coord",
        phone="x4002"
    )

    emp3 = StudentWorker(
        name="Alan Turing",
        title="Peer Tutor",
        phone="x4003"
    )

    emp4 = Administrator(
        name="M. Hamilton",
        title="Chair",
        phone="x4000",
        calendar=admin_calendar
    )

    employees = [emp1, emp2, emp3, emp4]

    # Initialize NamePlate (creates its own 3 buttons internally)
    plate = NamePlate(
        display=lcd,
        lights=lights,
        buzzer=buzzer,
        employees=employees
    )

    # Start the event loop
    Log.i("main.py: Starting NamePlate system...")
    plate.run()

if __name__ == "__main__":
    main()
