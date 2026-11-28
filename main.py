"""
# main.py
# Entry point for Lab 4 IoT CRM device (Raspberry Pi Pico 2W / Wokwi).
# Set LOAD_MODE in config.py to 'A' or 'B' to choose the sequence.
# Author: Lushana3
"""

from Log import *
from CRMController import CRMController

# Hide the PicoLibrary's chatty info logs so the console shows only the
# sequence trace (the lines that match the sequence diagram).
Log.level = ERROR


def main():
    controller = CRMController()
    try:
        controller.run()
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    main()
