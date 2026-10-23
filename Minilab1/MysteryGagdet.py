"""
# MysteryGagdet.py
# Implementation of MysteryGagdet simulating an engine system using an LCD display, buzzer, NeoPixel light strip, and potentiometer
# Author: Lushana3
"""

import time
from Log import *

class MysteryGagdet:
    """
    **MysteryGagdet**
    
    A composite MicroPython gadget simulating an internal combustion engine system.
    Integrates an LCD display, a buzzer, a NeoPixel light strip, and an analog potentiometer.

    - **Engine Start**: Simulates ignition/cranking, generates low-frequency rumble tones, and initializes idle RPM/speed on the display.
    - **Engine Control**: Dynamically monitors potentiometer values to increase or decrease engine RPM and simulated speed.
      Visualizes RPM progressively across the NeoPixel light strip as a tachometer gauge (Green -> Yellow -> Red),
      modulates buzzer pitch to simulate engine revving, and updates the LCD display in real time.
    - **Engine Stop**: Ceases engine sounds, clears tachometer lights, and displays "Engine stopped" on the LCD.

    Parameters:
    ----------
    display : LCDDisplay
        An LCD display instance used to render RPM, speed, and status text.
    buzzer : Buzzer or PassiveBuzzer
        A buzzer used to generate low-frequency engine sounds and throttle-dependent pitches.
    lightstrip : LightStrip
        A NeoPixel light strip used to visualize RPM like a tachometer rev-counter.
    potentiometer : AnalogSensor or ADC
        An analog sensor or potentiometer input used to adjust the engine RPM.

    Examples:
    ---------
    1. Initialize with hardware components and run an engine cycle:
       ```python
       from Displays import LCDDisplay
       from Buzzer import PassiveBuzzer
       from LightStrip import LightStrip
       from Sensors import AnalogSensor
       from MysteryGagdet import MysteryGagdet

       lcd = LCDDisplay(sda=0, scl=1)
       buzzer = PassiveBuzzer(pin=15)
       strip = LightStrip(pin=2, numleds=8)
       pot = AnalogSensor(pin=26)

       gadget = MysteryGagdet(lcd, buzzer, strip, pot)
       gadget.start()
       gadget.control(duration=10)
       gadget.stop()
       ```
    """

    IDLE_RPM = 800
    MAX_RPM = 7000
    MAX_SPEED = 120  # mph
    ADC_MAX = 65535.0

    def __init__(self, display, buzzer, lightstrip, potentiometer):
        """
        Initialize the MysteryGagdet with required hardware components.

        Parameters:
        ----------
        display : LCDDisplay
            LCD display object supporting showText and clear methods.
        buzzer : Buzzer or PassiveBuzzer
            Buzzer object supporting play and stop methods.
        lightstrip : LightStrip
            NeoPixel light strip supporting setPixel, show, and off methods.
        potentiometer : AnalogSensor or ADC
            Potentiometer sensor supporting rawValue or read_u16 methods.
        """
        self._display = display
        self._buzzer = buzzer
        self._lightstrip = lightstrip
        self._potentiometer = potentiometer

        self._running = False
        self._rpm = 0
        self._speed = 0

        Log.i("MysteryGagdet initialized")

    @property
    def is_running(self):
        """Return True if the engine is currently running, False otherwise."""
        return self._running

    @property
    def rpm(self):
        """Return the current simulated engine RPM."""
        return self._rpm

    @property
    def speed(self):
        """Return the current simulated speed in mph."""
        return self._speed

    def _read_potentiometer(self):
        """Safely read the raw value from the potentiometer object."""
        if hasattr(self._potentiometer, 'rawValue'):
            return self._potentiometer.rawValue()
        elif hasattr(self._potentiometer, 'read_u16'):
            return self._potentiometer.read_u16()
        elif callable(self._potentiometer):
            return self._potentiometer()
        else:
            try:
                return float(self._potentiometer)
            except (ValueError, TypeError):
                return 0

    def _update_lightstrip(self, rpm):
        """
        Visualize RPM across the NeoPixel light strip as a tachometer rev-counter.
        
        Colors transition from green (low RPM) to yellow (mid RPM) to red (high RPM / redline).
        """
        if not self._lightstrip:
            return

        num_leds = getattr(self._lightstrip, '_numleds', 8)
        ratio = max(0.0, min(1.0, (rpm - self.IDLE_RPM) / (self.MAX_RPM - self.IDLE_RPM)))
        active_leds = max(1, int(ratio * num_leds)) if self._running else 0

        if hasattr(self._lightstrip, 'setPixel'):
            for i in range(num_leds):
                if i < active_leds:
                    if i < int(num_leds * 0.5):
                        color = (0, 255, 0)      # Green (safe zone)
                    elif i < int(num_leds * 0.8):
                        color = (255, 200, 0)    # Yellow (approaching powerband)
                    else:
                        color = (255, 0, 0)      # Red (redline zone)
                    self._lightstrip.setPixel(i, color, show=False)
                else:
                    self._lightstrip.setPixel(i, (0, 0, 0), show=False)

            if hasattr(self._lightstrip, 'show'):
                self._lightstrip.show()
        elif hasattr(self._lightstrip, 'setColor'):
            color = (0, 255, 0) if ratio < 0.5 else ((255, 200, 0) if ratio < 0.8 else (255, 0, 0))
            self._lightstrip.setColor(color, active_leds)

    def start(self):
        """
        **start** - Simulate starting/cranking of an engine.

        Generates low-frequency cranking sounds on the buzzer, establishes idle RPM,
        and renders initial idle RPM and speed values on the LCD display.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Start the engine:
           ```python
           gadget.start()
           ```
        """
        Log.i("MysteryGagdet: Starting engine...")
        self._running = True
        self._rpm = self.IDLE_RPM
        self._speed = 0

        # Update display to indicate engine starting
        if self._display:
            self._display.clear()
            self._display.showText(("Starting engine" + " " * 16)[:16], row=0, col=0)
            self._display.showText(("Please wait..." + " " * 16)[:16], row=1, col=0)

        # Simulate engine starter cranking sound with rising low-frequency pulses
        if self._buzzer and hasattr(self._buzzer, 'play'):
            for freq in [50, 70, 90, 110]:
                self._buzzer.play(freq)
                time.sleep(0.08)
            # Settle at idle rumble
            self._buzzer.play(70)

        # Show initial idle values on LCD
        if self._display:
            line0 = (f"RPM: {self._rpm}" + " " * 16)[:16]
            line1 = (f"Speed: {self._speed} mph" + " " * 16)[:16]
            self._display.showText(line0, row=0, col=0)
            self._display.showText(line1, row=1, col=0)

        # Update light strip with initial idle indicator
        self._update_lightstrip(self._rpm)

        Log.i(f"MysteryGagdet: Engine started (Idle RPM: {self._rpm}, Speed: {self._speed} mph)")

    def stop(self):
        """
        **stop** - Stop the engine simulation.

        Silences the buzzer, turns off all LEDs on the light strip, sets engine state
        to stopped, and displays **"Engine stopped"** on the LCD screen.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Stop the engine:
           ```python
           gadget.stop()
           ```
        """
        Log.i("MysteryGagdet: Stopping engine...")
        self._running = False
        self._rpm = 0
        self._speed = 0

        # Silence buzzer
        if self._buzzer and hasattr(self._buzzer, 'stop'):
            self._buzzer.stop()

        # Turn off light strip LEDs
        if self._lightstrip:
            if hasattr(self._lightstrip, 'off'):
                self._lightstrip.off()
            elif hasattr(self._lightstrip, 'clear'):
                self._lightstrip.clear()

        # Update LCD display to show engine stopped
        if self._display:
            self._display.clear()
            self._display.showText(("Engine stopped" + " " * 16)[:16], row=0, col=0)
            self._display.showText(("" + " " * 16)[:16], row=1, col=0)

        Log.i("MysteryGagdet: Engine stopped successfully")

    def control(self, duration=None, iterations=None, delay=0.1):
        """
        **control** - Monitor the potentiometer to simulate increasing/decreasing RPM and speed.

        Reads potentiometer input (0 to 65535) and translates it into engine RPM (800 to 7000 RPM)
        and vehicle speed (0 to 120 mph). Visualizes RPM on the light strip as a tachometer,
        modulates the buzzer tone with RPM, and updates the LCD display in real time.

        Parameters:
        ----------
        duration : float, optional
            Duration in seconds to monitor the potentiometer. If None and iterations is None,
            runs until stopped or interrupted (default: None).
        iterations : int, optional
            Number of polling cycles to execute. If None, loops according to duration (default: None).
        delay : float, optional
            Delay in seconds between sensor polling cycles (default: 0.1).

        Examples:
        ---------
        1. Run continuous monitoring:
           ```python
           gadget.start()
           gadget.control()  # Runs until stopped
           ```
        2. Monitor for 5 seconds:
           ```python
           gadget.control(duration=5.0)
           gadget.stop()
           ```
        3. Run for 20 sampling iterations:
           ```python
           gadget.control(iterations=20, delay=0.05)
           ```
        """
        if not self._running:
            Log.i("MysteryGagdet: Engine not running when control invoked. Starting engine...")
            self.start()

        Log.i("MysteryGagdet: Starting throttle control loop...")
        start_time = time.time()
        cycles = 0

        try:
            while self._running:
                # Check termination conditions
                if iterations is not None and cycles >= iterations:
                    break
                if duration is not None and (time.time() - start_time) >= duration:
                    break

                # 1. Read potentiometer raw value (0 - 65535)
                raw_val = self._read_potentiometer()
                if raw_val > self.ADC_MAX:
                    ratio = 1.0
                elif raw_val < 0:
                    ratio = 0.0
                else:
                    ratio = raw_val / self.ADC_MAX

                # 2. Simulate RPM (800 to 7000) and Speed (0 to 120 mph)
                self._rpm = int(self.IDLE_RPM + ratio * (self.MAX_RPM - self.IDLE_RPM))
                self._speed = int(ratio * self.MAX_SPEED)

                # 3. Update LCD display
                if self._display:
                    line0 = (f"RPM: {self._rpm}" + " " * 16)[:16]
                    line1 = (f"Speed: {self._speed} mph" + " " * 16)[:16]
                    self._display.showText(line0, row=0, col=0)
                    self._display.showText(line1, row=1, col=0)

                # 4. Visualize RPM on NeoPixel light strip
                self._update_lightstrip(self._rpm)

                # 5. Modulate buzzer frequency to match engine revs (60Hz to 320Hz)
                if self._buzzer and hasattr(self._buzzer, 'play'):
                    sound_freq = int(60 + ratio * 260)
                    self._buzzer.play(sound_freq)

                cycles += 1
                time.sleep(delay)

        except KeyboardInterrupt:
            Log.i("MysteryGagdet: Control loop interrupted by user")
            self.stop()

        Log.i(f"MysteryGagdet: Control loop finished after {cycles} cycles")


# Convenient alias for proper English spelling
MysteryGadget = MysteryGagdet


if __name__ == "__main__":
    # Test execution block for verification
    Log.i("Beginning MysteryGagdet self-contained verification tests...")

    # Mock hardware components for self-contained desktop verification
    class MockDisplay:
        def __init__(self):
            self.lines = ["", ""]
        def clear(self, line=-1):
            if line == -1:
                self.lines = ["", ""]
            elif 0 <= line <= 1:
                self.lines[line] = ""
        def showText(self, text, row=0, col=0):
            self.lines[row] = text
            Log.i(f"MockDisplay [Row {row}]: {text.strip()}")

    class MockBuzzer:
        def __init__(self):
            self.playing = False
            self.freq = 0
        def play(self, tone=500):
            self.playing = True
            self.freq = tone
            Log.i(f"MockBuzzer: playing {tone} Hz tone")
        def stop(self):
            self.playing = False
            self.freq = 0
            Log.i("MockBuzzer: sound stopped")

    class MockLightStrip:
        def __init__(self, numleds=8):
            self._numleds = numleds
            self.pixels = [(0, 0, 0)] * numleds
        def setPixel(self, pixelno, color, show=True):
            if 0 <= pixelno < self._numleds:
                self.pixels[pixelno] = color
        def show(self):
            lit = sum(1 for c in self.pixels if c != (0, 0, 0))
            Log.i(f"MockLightStrip: {lit}/{self._numleds} LEDs illuminated")
        def off(self):
            self.pixels = [(0, 0, 0)] * self._numleds
            Log.i("MockLightStrip: LEDs turned off")

    class MockPotentiometer:
        def __init__(self, initial_val=0):
            self.val = initial_val
        def rawValue(self):
            return self.val
        def set_val(self, val):
            self.val = val

    # Instantiate mock hardware
    mock_display = MockDisplay()
    mock_buzzer = MockBuzzer()
    mock_lightstrip = MockLightStrip(numleds=8)
    mock_pot = MockPotentiometer(initial_val=0)

    # 1. Instantiate MysteryGagdet
    gadget = MysteryGagdet(mock_display, mock_buzzer, mock_lightstrip, mock_pot)
    assert not gadget.is_running, "Engine should not be running initially"

    # 2. Test start()
    gadget.start()
    assert gadget.is_running, "Engine should be running after start()"
    assert gadget.rpm == MysteryGagdet.IDLE_RPM, f"Expected RPM {MysteryGagdet.IDLE_RPM}, got {gadget.rpm}"
    assert mock_buzzer.playing, "Buzzer should be playing idle engine sound"
    assert "RPM: 800" in mock_display.lines[0], f"Display row 0 should show RPM: 800, got {mock_display.lines[0]}"

    # 3. Test control() with varied potentiometer values
    # Simulating throttle: 25%, 50%, 100%
    throttle_values = [16384, 32768, 65535]
    for val in throttle_values:
        mock_pot.set_val(val)
        gadget.control(iterations=1, delay=0.01)
        expected_ratio = val / 65535.0
        expected_rpm = int(MysteryGagdet.IDLE_RPM + expected_ratio * (MysteryGagdet.MAX_RPM - MysteryGagdet.IDLE_RPM))
        assert gadget.rpm == expected_rpm, f"Expected RPM {expected_rpm}, got {gadget.rpm}"
        Log.i(f"Throttle test val {val} -> RPM: {gadget.rpm}, Speed: {gadget.speed} mph")

    # 4. Test stop()
    gadget.stop()
    assert not gadget.is_running, "Engine should not be running after stop()"
    assert not mock_buzzer.playing, "Buzzer should be stopped"
    assert "Engine stopped" in mock_display.lines[0], f"Display row 0 should show 'Engine stopped', got {mock_display.lines[0]}"

    Log.i("Testing complete - all checks passed")
