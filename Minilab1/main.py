"""
# main.py
# Main execution script to initialize, start, control for 10 seconds, and stop the MysteryGadget
# Author: Lushana3
"""

import time
from Log import *
from MysteryGagdet import MysteryGadget, MysteryGagdet

def main():
    """
    Initialize MysteryGadget components, start the engine simulation,
    control it for approximately 10 seconds using potentiometer readings,
    and then stop the gadget cleanly.
    """
    Log.i("main.py: Initializing MysteryGadget...")

    # Hardware component setup for Raspberry Pi Pico
    # Falls back gracefully to simulation mocks if executed in a host environment without 'machine'
    try:
        from Displays import LCDDisplay
        from Buzzer import PassiveBuzzer
        from LightStrip import LightStrip
        from Sensors import AnalogSensor

        lcd = LCDDisplay(sda=0, scl=1)
        buzzer = PassiveBuzzer(pin=16)
        strip = LightStrip(pin=2, numleds=8, brightness=0.5)
        pot = AnalogSensor(pin=26)
        Log.i("main.py: Hardware components initialized successfully")
    except (ImportError, Exception) as e:
        Log.w(f"main.py: Hardware initialization unavailable ({e}); using simulated components")

        class SimulatedDisplay:
            def clear(self, line=-1):
                pass
            def showText(self, text, row=0, col=0):
                Log.i(f"[LCD Row {row}]: {text.strip()}")

        class SimulatedBuzzer:
            def play(self, tone=500):
                Log.i(f"[Buzzer]: Tone {tone} Hz")
            def stop(self):
                Log.i("[Buzzer]: Stopped")

        class SimulatedLightStrip:
            _numleds = 8
            def setPixel(self, pixelno, color, show=True):
                pass
            def show(self):
                pass
            def off(self):
                Log.i("[LightStrip]: LEDs OFF")

        class SimulatedPotentiometer:
            def __init__(self):
                self._start = time.time()
            def rawValue(self):
                # Simulate dynamic potentiometer adjustment over 10 seconds (ramps up and down)
                elapsed = time.time() - self._start
                # Triangular wave oscillating between 0 and 65535 over ~10 seconds
                cycle = (elapsed % 10.0) / 10.0
                val = cycle * 2.0 if cycle <= 0.5 else (1.0 - cycle) * 2.0
                return int(val * 65535)

        lcd = SimulatedDisplay()
        buzzer = SimulatedBuzzer()
        strip = SimulatedLightStrip()
        pot = SimulatedPotentiometer()

    # 1. Create an instance of MysteryGadget
    gadget = MysteryGadget(display=lcd, buzzer=buzzer, lightstrip=strip, potentiometer=pot)

    # 2. Start the MysteryGadget
    Log.i("main.py: Starting MysteryGadget...")
    gadget.start()

    # 3. Control for about 10 seconds (monitoring potentiometer input)
    Log.i("main.py: Controlling MysteryGadget for approximately 10 seconds...")
    gadget.control(duration=10.0, delay=0.2)

    # 4. Stop the MysteryGadget
    Log.i("main.py: Stopping MysteryGadget...")
    gadget.stop()

    Log.i("Testing complete - MysteryGadget 10-second run finished")

if __name__ == "__main__":
    main()
