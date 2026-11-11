"""
# FeedbackController.py
# State machine controller for the Raspberry Pi Pico W Feedback Kiosk.
# Implements the 7-state model managing LCD, LightStrip, Buzzer, Ultrasonic Sensor, and Buttons.
# Author: Lushana3
"""

import time
from Log import *
from Lights import RED, GREEN, YELLOW, BLACK
from Displays import LCDDisplay
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from Sensors_advanced import UltrasonicSensor
from Button import Button
from Counters import SoftwareTimer
from StateModel import StateModel
from FeedbackStats import FeedbackStats


class FeedbackController:
    """
    Finite state machine controller for the customer feedback kiosk.

    Composes and orchestrates all kiosk hardware devices (LCD display, NeoPixel
    light strip, passive buzzer, ultrasonic distance sensor, and three pushbuttons)
    together with a software timer, statistics tracker, and a 7-state finite state
    machine from the PicoLibrary.

    States:
    0 - Welcome: Idle screen waiting for a guest to approach within 10 cm.
    1 - Selection: Displays rating prompt and waits for button press or timeout.
    2 - Happy: Records green vote, plays happy chime, displays score, waits 5s.
    3 - Neutral: Records yellow vote, plays neutral tone, displays score, waits 5s.
    4 - Unhappy: Records red vote, plays sad tone, displays score, evaluates alarm in stateDo, waits 5s.
    5 - Alarm: Manager alert flashing red and alternating tones until green button is pressed.
    6 - Cooldown: Displays thank you screen and waits for guest to walk away.

    Parameters:
    ----------
    None (All hardware and subcomponents are created internally via composition).

    Examples:
    ---------
    1. Instantiating and running the kiosk:
       controller = FeedbackController()
       controller.run()
    """

    def __init__(self):
        """
        Initialize FeedbackController by creating all composed hardware components,
        the software timer, feedback stats tracker, and configuring the 7-state model.
        """
        Log.i("FeedbackController.__init__: Initializing hardware and state model...")

        # 1. Instantiate hardware components
        self.display = LCDDisplay(sda=0, scl=1)
        self.lights = LightStrip(pin=2, name='Neopixel', numleds=8)
        self.buzzer = PassiveBuzzer(15, name='Buzzer')
        self.sensor = UltrasonicSensor(trigger=16, echo=17, name='uss', threshold=10.0)

        btn_green = Button(18, 'green')
        btn_yellow = Button(19, 'yellow')
        btn_red = Button(20, 'red')
        self.buttons = [btn_green, btn_yellow, btn_red]

        self.timer = SoftwareTimer(name='timer')
        self.stats = FeedbackStats()

        # 2. Instantiate StateModel with 7 states (0 to 6)
        self.model = StateModel(7, self, debug=True)

        # 3. Register inputs and timer with the state model
        self.model.addButton(btn_green)
        self.model.addButton(btn_yellow)
        self.model.addButton(btn_red)
        self.model.addSensor(self.sensor)
        self.model.addTimer(self.timer)
        self.model.addCustomEvent("feedback_below_threshold")

        # 4. Configure State Transitions
        # State 0 (Welcome) -> guest approaches
        self.model.addTransition(0, ["uss_trip"], 1)

        # State 1 (Selection) -> votes or abandons
        self.model.addTransition(1, ["green_press"], 2)
        self.model.addTransition(1, ["yellow_press"], 3)
        self.model.addTransition(1, ["red_press"], 4)
        self.model.addTransition(1, ["timer_timeout", "uss_untrip"], 0)

        # Vote states -> Cooldown on timeout
        self.model.addTransition(2, ["timer_timeout"], 6)
        self.model.addTransition(3, ["timer_timeout"], 6)
        self.model.addTransition(4, ["timer_timeout"], 6)

        # State 4 (Unhappy) -> Alarm if satisfaction drops below threshold
        self.model.addTransition(4, ["feedback_below_threshold"], 5)

        # State 5 (Alarm) -> Manager resets via Green button
        self.model.addTransition(5, ["green_press"], 0)

        # State 6 (Cooldown) -> Next guest arrives / current guest steps away
        self.model.addTransition(6, ["uss_untrip", "timer_timeout"], 0)

        Log.i("FeedbackController.__init__: Initialization complete.")

    def run(self):
        """
        Start executing the state machine.
        """
        Log.i("FeedbackController: Starting state machine execution...")
        self.model.run()

    # -------------------------------------------------------------------------
    # StateModel Lifecycle Handlers
    # -------------------------------------------------------------------------

    def stateEntered(self, state, event):
        """
        Perform state entry actions.

        Parameters:
        ----------
        state : int
            State number being entered (0 to 6).
        event : str
            Event that triggered the transition.
        """
        Log.i(f"FeedbackController: stateEntered -> State {state} on event '{event}'")

        if state == 0:
            self.showWelcome()

        elif state == 1:
            self.showPrompt()
            self.timer.start(8)

        elif state == 2:
            self.stats.add_happy()
            self.happyChime()
            self.showScore()
            self.timer.start(5)

        elif state == 3:
            self.stats.add_neutral()
            self.neutralTone()
            self.showScore()
            self.timer.start(5)

        elif state == 4:
            self.stats.add_unhappy()
            self.sadTone()
            self.showScore()
            self.timer.start(5)

        elif state == 5:
            self.showAlarm()

        elif state == 6:
            self.showNextGuest()
            self.timer.start(5)

    def stateLeft(self, state, event):
        """
        Perform state exit actions.

        Cancels active timers when leaving states 1, 2, 3, 4, and 6.
        Silences alarm and resets statistics when leaving state 5.

        Parameters:
        ----------
        state : int
            State number being exited (0 to 6).
        event : str
            Event causing the exit.
        """
        Log.i(f"FeedbackController: stateLeft -> State {state} on event '{event}'")

        if state in (1, 2, 3, 4, 6):
            self.timer.cancel()

        if state == 5:
            self.silenceAlarm()
            self.stats.reset()

    def stateDo(self, state):
        """
        Execute continuous polling or periodic activity for the active state.

        In state 4 (Unhappy), polls whether stats.is_low() has been triggered.
        In state 5 (Alarm), drives alternating non-blocking buzzer tones and flashing lights.

        Parameters:
        ----------
        state : int
            Currently active state number.
        """
        if state == 4:
            if self.stats.is_low():
                Log.i("State 4 stateDo: Satisfaction < 30% after 5+ votes! Triggering alarm...")
                self.model.processEvent("feedback_below_threshold")

        elif state == 5:
            self.alarmTick()
            self.flashRed()

    def stateEvent(self, state, event) -> bool:
        """
        Handler for in-state events.

        Parameters:
        ----------
        state : int
            Current state.
        event : str
            Event received.

        Returns:
        -------
        bool
            False (no in-state events used).
        """
        return False

    # -------------------------------------------------------------------------
    # Display Methods (All text lines <= 16 characters)
    # -------------------------------------------------------------------------

    def showWelcome(self):
        """
        Display the idle welcome screen on the LCD and turn off the light strip.
        """
        Log.i("FeedbackController: Showing Welcome screen")
        self.display.clear()
        self.display.showText("Welcome!", 0, 0)
        self.display.showText("Please step up", 1, 0)
        self.lights.setColor(BLACK)

    def showPrompt(self):
        """
        Prompt the visitor to rate their visit using the three buttons.
        """
        Log.i("FeedbackController: Showing Rating Prompt")
        self.display.clear()
        self.display.showText("Rate your visit:", 0, 0)
        self.display.showText("G:)  Y:|  R:(", 1, 0)

    def showAlarm(self):
        """
        Display the manager alert message on the LCD.
        """
        Log.i("FeedbackController: Showing Manager Alert screen")
        self.display.clear()
        self.display.showText("MANAGER ALERT!", 0, 0)
        self.display.showText("Press G to reset", 1, 0)

    def showNextGuest(self):
        """
        Display the thank you and cooldown screen on the LCD.
        """
        Log.i("FeedbackController: Showing Cooldown / Thank you screen")
        self.display.clear()
        self.display.showText("Thank you!", 0, 0)
        self.display.showText("Next guest", 1, 0)

    def showScore(self):
        """
        Illuminate the NeoPixel light strip according to current satisfaction score
        and display the score on the LCD.

        Scales the 0-100% score to 0-8 LEDs. Color indicates overall satisfaction level:
        - >= 70%: Green
        - 30% - 69%: Yellow
        - < 30%: Red
        """
        level = self.stats.get_light_level()
        pct = self.stats.calculate_percentage()
        Log.i(f"FeedbackController.showScore: {pct:.1f}% -> {level}/8 LEDs")

        if pct >= 70.0:
            color = GREEN
        elif pct >= 30.0:
            color = YELLOW
        else:
            color = RED

        self.lights.setColor(color, level)

        self.display.clear()
        self.display.showText("Thanks for vote!", 0, 0)
        self.display.showText(f"Score: {round(pct)}%", 1, 0)

    # -------------------------------------------------------------------------
    # Audio, Light, and Alarm Methods
    # -------------------------------------------------------------------------

    def happyChime(self):
        """
        Play an ascending cheerful chime on the passive buzzer (duration < 0.5s).
        """
        Log.i("FeedbackController: Playing happy chime")
        self.buzzer.beep(tone=523, duration=100)
        time.sleep(0.04)
        self.buzzer.beep(tone=784, duration=160)

    def neutralTone(self):
        """
        Play a neutral tone on the passive buzzer (duration < 0.5s).
        """
        Log.i("FeedbackController: Playing neutral tone")
        self.buzzer.beep(tone=659, duration=200)

    def sadTone(self):
        """
        Play a descending tone on the passive buzzer (duration < 0.5s).
        """
        Log.i("FeedbackController: Playing sad tone")
        self.buzzer.beep(tone=659, duration=120)
        time.sleep(0.04)
        self.buzzer.beep(tone=440, duration=180)

    def alarmTick(self):
        """
        Play a non-blocking two-tone alarm alternating every 250ms based on time.ticks_ms().
        """
        phase = (time.ticks_ms() // 250) % 2
        tone = 880 if phase == 0 else 587
        self.buzzer.play(tone)

    def flashRed(self):
        """
        Flash the light strip red alternating every 250ms based on time.ticks_ms() without blocking.
        Uses lights.setColor(BLACK) instead of lights.off() to avoid blocking delays.
        """
        phase = (time.ticks_ms() // 250) % 2
        if phase == 0:
            self.lights.setColor(RED)
        else:
            self.lights.setColor(BLACK)

    def silenceAlarm(self):
        """
        Stop buzzer audio and turn off red flashing lights without blocking.
        """
        Log.i("FeedbackController: Silencing alarm")
        self.buzzer.stop()
        self.lights.setColor(BLACK)


if __name__ == "__main__":
    controller = FeedbackController()
    controller.run()
