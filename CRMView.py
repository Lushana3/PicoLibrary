"""
# CRMView.py
# View class for the IoT CRM device. Owns the LCD, the NeoPixel LightStrip
# and the passive Buzzer, and knows how to show customers, contacts and
# activities on them.
# Author: Lushana3
"""

import time
from Log import *
from Trace import seq
from Lights import BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, ORANGE, WHITE

# Light colors for contact types (from the CRM contact_type values)
CONTACT_COLORS = {
    'Customer': GREEN,
    'Product Manager': PURPLE,
    'Sales Consultant': CYAN,
    'Other': YELLOW,
}

# Light colors for activity types
ACTIVITY_COLORS = {
    'Meeting': BLUE,
    'Phone Call': ORANGE,
}


class CRMView:
    """
    **CRMView**

    Parameters:
    ----------
    display : LCDDisplay
    lights : LightStrip (8 LEDs)
    buzzer : PassiveBuzzer
    """

    def __init__(self, display, lights, buzzer):
        self._display = display
        self._lights = lights
        self._buzzer = buzzer
        self._numleds = getattr(lights, '_numleds', 8)

    # ------------------------------------------------------------------
    # Text output
    # ------------------------------------------------------------------

    def showLines(self, line0, line1=''):
        """ Show two lines, padded to 16 chars so old text is overwritten """
        l0 = (line0[:16] + ' ' * 16)[:16]
        l1 = (line1[:16] + ' ' * 16)[:16]
        self._display.showText(l0, 0, 0)
        self._display.showText(l1, 1, 0)

    def showMessage(self, line0, line1=''):
        seq('CRMView', 'LCDDisplay', f"showMessage('{line0}', '{line1}')")
        self.showLines(line0, line1)

    def showProgress(self, done, total):
        """ Option A loading bar: text on LCD and LEDs filling up """
        self.showLines('Loading all...', f'Customer {done}/{total}')
        lit = max(1, round(done / total * self._numleds))
        self._lights.setColor(BLUE, lit)

    # ------------------------------------------------------------------
    # Screens for each kind of object
    # ------------------------------------------------------------------

    def showCustomer(self, customer, index, total):
        lines = customer.getDisplayLines(index, total)
        seq('CRMView', 'LCDDisplay', f"showCustomer('{lines[0]}', '{lines[1]}')")
        self.showLines(lines[0], lines[1])
        self._customerLights(customer)

    def showContact(self, contact, index, total):
        lines = contact.getDisplayLines()
        seq('CRMView', 'LCDDisplay', f"showContact('{lines[0]}', '{lines[1]}') {index + 1}/{total}")
        self.showLines(lines[0], lines[1])
        color = CONTACT_COLORS.get(contact.contactType, WHITE)
        seq('CRMView', 'LightStrip', f"setColor({contact.contactType}) pixel {index + 1}")
        self._onePixel(index, color)

    def showActivity(self, activity, index, total):
        lines = activity.getDisplayLines()
        seq('CRMView', 'LCDDisplay', f"showActivity('{lines[0]}', '{lines[1]}') {index + 1}/{total}")
        self.showLines(lines[0], lines[1])
        color = ACTIVITY_COLORS.get(activity.activityType, WHITE)
        seq('CRMView', 'LightStrip', f"setColor({activity.activityType}) pixel {index + 1}")
        self._onePixel(index, color)

    def showEmpty(self, what):
        """ Customer has no contacts or no activities """
        seq('CRMView', 'LCDDisplay', f"showEmpty('No {what}')")
        self.showLines(f'No {what}', 'Yellow: next')
        self._lights.setColor(RED)
        self.sadTone()

    # ------------------------------------------------------------------
    # Lights
    # ------------------------------------------------------------------

    def _customerLights(self, customer):
        """
        Customer status on the light strip:
          details not loaded yet (Option B) -> 1 blue LED
          no activities -> all red (needs attention before the meeting!)
          activities -> one green LED per activity (max 8)
        """
        if not customer.detailsLoaded:
            seq('CRMView', 'LightStrip', "setColor(BLUE, 1) not loaded yet")
            self._lights.setColor(BLUE, 1)
        elif len(customer.activities) == 0:
            seq('CRMView', 'LightStrip', "setColor(RED) no activities")
            self._lights.setColor(RED)
        else:
            n = min(len(customer.activities), self._numleds)
            seq('CRMView', 'LightStrip', f"setColor(GREEN, {n}) activities")
            self._lights.setColor(GREEN, n)

    def _onePixel(self, index, color):
        """ Light only the pixel matching the item's position, like a cursor """
        for i in range(self._numleds):
            self._lights.setPixel(i, color if i == index % self._numleds else BLACK, show=False)
        self._lights.show()

    def lightsOff(self):
        self._lights.setColor(BLACK)

    # ------------------------------------------------------------------
    # Sounds
    # ------------------------------------------------------------------

    def click(self):
        self._buzzer.beep(tone=1200, duration=30)

    def readyChime(self):
        seq('CRMView', 'Buzzer', "readyChime()")
        self._buzzer.beep(tone=523, duration=100)
        time.sleep(0.03)
        self._buzzer.beep(tone=659, duration=100)
        time.sleep(0.03)
        self._buzzer.beep(tone=784, duration=150)

    def sadTone(self):
        seq('CRMView', 'Buzzer', "sadTone()")
        self._buzzer.beep(tone=440, duration=120)
        time.sleep(0.03)
        self._buzzer.beep(tone=330, duration=180)
