"""
# main.py
# Main execution entrypoint for Lab 3 Feedback Kiosk on Raspberry Pi Pico W / Wokwi.
# Author: Lushana3
"""

from FeedbackController import FeedbackController
from Log import *

def main():
    """
    Instantiate FeedbackController and execute the feedback kiosk state machine.
    """
    Log.i("main.py: Starting Feedback Kiosk System...")
    controller = FeedbackController()
    controller.run()


if __name__ == "__main__":
    main()
