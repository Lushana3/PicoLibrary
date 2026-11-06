"""
# NamePlate.py
# Object-oriented implementation of the NamePlate class coordinating display, buttons, status lights, and buzzer
# Author: Lushana3
"""

import time
from Log import *
from Lights import GREEN, RED, YELLOW, BLUE

class NamePlate:
    """
    **NamePlate**

    Composite controller that manages a collection of employees and interfaces
    with an LCD display, a NeoPixel status light strip, a passive buzzer, and
    three navigation/interaction pushbuttons created internally.

    Parameters:
    ----------
    display : LCDDisplay
        Hardware LCD display (16x2) used to show employee name, title, and status.
    lights : LightStrip
        NeoPixel light strip indicating availability status using color.
    buzzer : PassiveBuzzer
        PWM-driven passive buzzer for audible interaction cues.
    employees : list
        List of Employee instances to display (multiplicity 1..*).

    Examples:
    ---------
    1. Create and run a NamePlate:
       ```python
       plate = NamePlate(display=lcd, lights=strip, buzzer=buzzer, employees=[fac, staff])
       plate.run()
       ```
    """

    def __init__(self, display, lights, buzzer, employees):
        """
        Initialize NamePlate hardware components, create internal buttons, and render initial display.
        """
        self.display = display
        self.lights = lights
        self.buzzer = buzzer
        self.employees = employees if employees is not None else []
        self.index = 0

        Log.i(f"NamePlate constructor: initialized with {len(self.employees)} employees")

        # Composition: NamePlate creates its own 3 buttons
        from Button import Button
        self.buttons = [
            Button(10, "prev", handler=self),
            Button(11, "next", handler=self),
            Button(12, "status", handler=self)
        ]

        if self.employees:
            self.updateDisplay()

    def previousEmployee(self):
        """
        Navigate to the previous employee in the list (wrapping around).

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. plate.previousEmployee()
        """
        if not self.employees:
            return
        self.index = (self.index - 1) % len(self.employees)
        Log.i(f"NamePlate: previousEmployee -> index {self.index}: {self.employees[self.index].name}")
        if self.buzzer:
            try:
                self.buzzer.beep(800, 40)
            except Exception as e:
                Log.w(f"NamePlate buzzer error: {e}")
        self.updateDisplay()

    def nextEmployee(self):
        """
        Navigate to the next employee in the list (wrapping around).

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. plate.nextEmployee()
        """
        if not self.employees:
            return
        self.index = (self.index + 1) % len(self.employees)
        Log.i(f"NamePlate: nextEmployee -> index {self.index}: {self.employees[self.index].name}")
        if self.buzzer:
            try:
                self.buzzer.beep(1200, 40)
            except Exception as e:
                Log.w(f"NamePlate buzzer error: {e}")
        self.updateDisplay()

    def buttonPressed(self, name):
        """
        Callback invoked when a registered button is pressed. Dispatches
        to previousEmployee, nextEmployee, or cycles current employee availability.

        Parameters:
        ----------
        name : str
            The name identifier of the button pressed ("prev", "next", or "status").

        Examples:
        ---------
        1. plate.buttonPressed("next")
        """
        Log.i(f"NamePlate: buttonPressed received '{name}'")
        if name == "prev":
            self.previousEmployee()
        elif name == "next":
            self.nextEmployee()
        elif name == "status":
            if self.employees:
                emp = self.employees[self.index]
                emp.cycleAvailability()
                if self.buzzer:
                    try:
                        self.buzzer.beep(1500, 60)
                    except Exception as e:
                        Log.w(f"NamePlate buzzer error: {e}")
                self.updateDisplay()

    def buttonReleased(self, name):
        """
        Callback invoked when a registered button is released.

        Parameters:
        ----------
        name : str
            The name identifier of the button released.

        Examples:
        ---------
        1. plate.buttonReleased("next")
        """
        Log.i(f"NamePlate: buttonReleased received '{name}'")

    def updateDisplay(self):
        """
        Update the LCD text display with current employee information
        and update the status light color based on exact availability status.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. plate.updateDisplay()
        """
        if not self.employees:
            Log.w("NamePlate: No employees to display")
            if self.display:
                try:
                    self.display.clear()
                    self.display.showText("No Employees    ", 0, 0)
                except Exception as e:
                    Log.w(f"NamePlate display clear error: {e}")
            return

        emp = self.employees[self.index]
        lines = emp.getDisplayLines()

        raw0 = lines[0] if len(lines) > 0 else ""
        raw1 = lines[1] if len(lines) > 1 else ""

        # Manually truncate and pad each line to 16 chars without using ljust
        line0 = raw0[:16]
        line0 = line0 + (" " * (16 - len(line0)))

        line1 = raw1[:16]
        line1 = line1 + (" " * (16 - len(line1)))

        Log.i(f"NamePlate updateDisplay: [{line0.strip()}] / [{line1.strip()}]")

        if self.display:
            try:
                self.display.showText(line0, 0, 0)
                self.display.showText(line1, 1, 0)
            except Exception as e:
                Log.w(f"NamePlate display error: {e}")

        if self.lights:
            status = emp.getAvailability()
            if status == "Available":
                color = GREEN
            elif status == "Away":
                color = YELLOW
            elif status == "Busy":
                color = RED
            else:
                color = BLUE

            try:
                self.lights.setColor(color)
            except Exception as e:
                Log.w(f"NamePlate light strip error: {e}")

    def run(self):
        """
        Main execution loop for NamePlate.
        Keeps running while hardware interrupt handlers service button presses.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. plate.run()
        """
        Log.i("NamePlate: Starting run loop...")
        self.updateDisplay()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            Log.i("NamePlate: Run loop terminated")


if __name__ == "__main__":
    Log.i("NamePlate module loaded successfully. Run main.py to execute the system.")
