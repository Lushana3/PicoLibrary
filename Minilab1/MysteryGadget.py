"""
# MysteryGadget.py
# Alias module for MysteryGagdet engine simulation class
# Author: Lushana3
"""

from MysteryGagdet import MysteryGagdet, MysteryGadget
from Log import *

if __name__ == "__main__":
    Log.i("MysteryGadget alias verification...")
    # Verify that MysteryGadget references MysteryGagdet
    assert MysteryGadget is MysteryGagdet
    Log.i("Testing complete - all checks passed")
