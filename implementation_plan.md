# Implementation Plan: Feedback Kiosk System (Lab 3)

**Author:** Lushana3  
**Target Platform:** Raspberry Pi Pico W / MicroPython / Wokwi Simulator  
**Architecture:** Finite State Machine via `StateModel` (PicoLibrary)

---

## 1. Executive Summary & Diagram Alignment

This implementation plan strictly adheres to the provided UML Class Diagram (`Feedbacksystem class Diagram.png`) and State Diagram (`Feedback State Machine.png`), incorporating all user refinements:

1. **Full Composition inside `FeedbackController.__init__()`**:
   - `FeedbackController.__init__(self)` takes **no parameters**.
   - It internally instantiates all hardware components (`LCDDisplay`, `LightStrip`, `PassiveBuzzer`, `UltrasonicSensor`, 3x `Button`), `SoftwareTimer`, `FeedbackStats`, and `StateModel`.
   - All imports are cleanly placed at the top of the file.
2. **Simplified `main.py`**:
   - `main.py` only imports and creates `FeedbackController()` and calls `controller.run()`.
3. **Exact Class Diagram Fidelity for `FeedbackStats`**:
   - Attributes: only `_happy_count`, `_neutral_count`, and `_unhappy_count`. No extra helper variables.
   - Hardcoded values: minimum 5 votes and $< 30\%$ threshold directly inside `is_low()`.
   - `get_light_level()` takes **no parameters** and maps directly to an 8-LED NeoPixel strip.
   - Satisfaction percentage formula: `((happy + 0.5 * neutral) / total) * 100`.
4. **State Transitions & Entry/Exit Actions**:
   - Only State 4 (`Unhappy`) transitions to State 5 (`Alarm`) on `feedback_below_threshold`.
   - In States 2 (`Happy`), 3 (`Neutral`), and 4 (`Unhappy`):
     - Entry order: `stats.add_...()`, then sound chime/tone, then `showScore()`, then `timer.start(5)`.
   - `showScore()` is its own independent method on `FeedbackController`.
   - In `stateLeft()`, `timer.cancel()` is called when leaving States 1, 2, 3, 4, and 6. Leaving State 5 calls `silenceAlarm()` and `stats.reset()`.
   - In State 4 (`Unhappy`), `stats.is_low()` is evaluated inside `stateDo(4)`.
5. **Display & Non-blocking Alarm Timing**:
   - LCD text strings are strictly $\le 16$ characters per line.
   - Sound chimes use short beeps keeping total playback duration $< 0.5$ seconds to avoid freezing.
   - `alarmTick()` and `flashRed()` use `time.ticks_ms()` directly (switching every 250ms) to alternate tones and colors without blocking `sleep()` and without adding extra unmodeled state attributes.
   - `flashRed()` and `silenceAlarm()` use `lights.setColor(BLACK)` instead of `lights.off()` to avoid the internal `time.sleep(0.1)` delay in `LightStrip.off()`.
   - Clean, direct `if __name__ == "__main__":` blocks without mocks.

---

## 2. File Organization & Responsibilities

| File | Type | Target Class | Role & Dependencies |
| :--- | :--- | :--- | :--- |
| **`FeedbackStats.py`** | New Class | `FeedbackStats` | Pure domain model tracking votes (`_happy_count`, `_neutral_count`, `_unhappy_count`), satisfaction formula, 8-LED light level, and alarm condition ($N \ge 5$ and score $< 30\%$). |
| **`FeedbackController.py`** | New Class | `FeedbackController` | Controller composing LCD, NeoPixel, Buzzer, Ultrasonic Sensor, 3 Buttons, Timer, Stats, and StateModel. Handles entry/exit actions, `stateDo()` polling, tones, `showScore()`, and non-blocking alarm. |
| **`main.py`** | Replaced File | Entrypoint Script | Instantiates `FeedbackController()` with no arguments and calls `run()`. |

*(Core PicoLibrary classes remain completely untouched).*

---

## 3. Hardware Pin Mapping (Internal to `FeedbackController`)

All pins are assigned internally within `FeedbackController.__init__()`:

| Hardware Device | PicoLibrary Class | Pin / Configuration | Notes |
| :--- | :--- | :--- | :--- |
| **LCD Display (1602 I2C)** | `LCDDisplay` | `sda=0, scl=1` | I2C ID 0 on GP0/GP1 |
| **Light Strip (WS2812)** | `LightStrip` | `pin=2, numleds=8, name='Neopixel'` | GP2 driving 8 NeoPixel LEDs |
| **Passive Buzzer** | `PassiveBuzzer` | `pin=15, name='Buzzer'` | GP15 PWM tone output |
| **Ultrasonic Sensor (HC-SR04)** | `UltrasonicSensor` | `trigger=16, echo=17, threshold=10.0, name='uss'` | GP16 Trigger, GP17 Echo; 10 cm trip threshold |
| **Green Button ("Happy / Reset")** | `Button` | `pin=18, name='green'` | GP18 active-low input |
| **Yellow Button ("Neutral")** | `Button` | `pin=19, name='yellow'` | GP19 active-low input |
| **Red Button ("Unhappy")** | `Button` | `pin=20, name='red'` | GP20 active-low input |
| **Software Timer** | `SoftwareTimer` | `name='timer'` | Software timer polled by `StateModel` |

---

## 4. Detailed File Specifications

### File 1: `FeedbackStats.py`

#### Module Header
```python
"""
# FeedbackStats.py
# Encapsulated statistics tracking for the customer feedback kiosk.
# Tracks vote tallies, calculates satisfaction percentages, and evaluates alarm thresholds.
# Author: Lushana3
"""
```

#### Class: `FeedbackStats`

- **Attributes**:
  - `_happy_count : int` - Private counter for happy ratings (initialized to 0)
  - `_neutral_count : int` - Private counter for neutral ratings (initialized to 0)
  - `_unhappy_count : int` - Private counter for unhappy ratings (initialized to 0)

- **Methods**:
  - `__init__()`:
    - Initializes `_happy_count = 0`, `_neutral_count = 0`, `_unhappy_count = 0`.
  - `add_happy() -> None`:
    - Increments `_happy_count` by 1.
  - `add_neutral() -> None`:
    - Increments `_neutral_count` by 1.
  - `add_unhappy() -> None`:
    - Increments `_unhappy_count` by 1.
  - `get_total_count() -> int`:
    - Returns `_happy_count + _neutral_count + _unhappy_count`.
  - `calculate_percentage() -> float`:
    - Returns `((_happy_count + 0.5 * _neutral_count) / total) * 100.0` if `total > 0` else `100.0`.
  - `get_light_level() -> int`:
    - Takes **no parameters**.
    - Scales the percentage to 8 LEDs: `round((calculate_percentage() / 100.0) * 8)`.
    - Clamped between `0` and `8`.
  - `is_low() -> bool`:
    - Returns `True` if `get_total_count() >= 5` and `calculate_percentage() < 30.0`.
    - Otherwise returns `False`.
  - `reset() -> None`:
    - Resets `_happy_count = 0`, `_neutral_count = 0`, `_unhappy_count = 0`.

---

### File 2: `FeedbackController.py`

#### Module Header
```python
"""
# FeedbackController.py
# State machine controller for the Raspberry Pi Pico W Feedback Kiosk.
# Implements the 7-state model managing LCD, LightStrip, Buzzer, Ultrasonic Sensor, and Buttons.
# Author: Lushana3
"""
```

#### Class: `FeedbackController`

- **Attributes**:
  - `display : LCDDisplay`
  - `lights : LightStrip`
  - `buzzer : PassiveBuzzer`
  - `sensor : UltrasonicSensor`
  - `timer : SoftwareTimer`
  - `buttons : list` - `[green_button, yellow_button, red_button]`
  - `stats : FeedbackStats`
  - `model : StateModel`

- **Constructor**:
  - `__init__()`: Takes **no parameters**.
    - Instantiates hardware:
      - `self.display = LCDDisplay(sda=0, scl=1)`
      - `self.lights = LightStrip(pin=2, name='Neopixel', numleds=8)`
      - `self.buzzer = PassiveBuzzer(15, name='Buzzer')`
      - `self.sensor = UltrasonicSensor(trigger=16, echo=17, name='uss', threshold=10.0)`
      - `btn_green = Button(18, 'green')`
      - `btn_yellow = Button(19, 'yellow')`
      - `btn_red = Button(20, 'red')`
      - `self.buttons = [btn_green, btn_yellow, btn_red]`
      - `self.timer = SoftwareTimer(name='timer')`
      - `self.stats = FeedbackStats()`
      - `self.model = StateModel(7, self, debug=True)`
    - Registers components with `self.model`:
      - `self.model.addButton(btn_green)`
      - `self.model.addButton(btn_yellow)`
      - `self.model.addButton(btn_red)`
      - `self.model.addSensor(self.sensor)`
      - `self.model.addTimer(self.timer)`
      - `self.model.addCustomEvent("feedback_below_threshold")`
    - Configures transitions:
      - `addTransition(0, ["uss_trip"], 1)`
      - `addTransition(1, ["green_press"], 2)`
      - `addTransition(1, ["yellow_press"], 3)`
      - `addTransition(1, ["red_press"], 4)`
      - `addTransition(1, ["timer_timeout", "uss_untrip"], 0)`
      - `addTransition(2, ["timer_timeout"], 6)`
      - `addTransition(3, ["timer_timeout"], 6)`
      - `addTransition(4, ["timer_timeout"], 6)`
      - `addTransition(4, ["feedback_below_threshold"], 5)`
      - `addTransition(5, ["green_press"], 0)`
      - `addTransition(6, ["uss_untrip", "timer_timeout"], 0)`

- **State Model Handlers**:
  - `stateEntered(state: int, event: str) -> None`:
    - `0 (Welcome)`: `self.showWelcome()`
    - `1 (Selection)`: `self.showPrompt()`; `self.timer.start(8)`
    - `2 (Happy)`: `self.stats.add_happy()`; `self.happyChime()`; `self.showScore()`; `self.timer.start(5)`
    - `3 (Neutral)`: `self.stats.add_neutral()`; `self.neutralTone()`; `self.showScore()`; `self.timer.start(5)`
    - `4 (Unhappy)`: `self.stats.add_unhappy()`; `self.sadTone()`; `self.showScore()`; `self.timer.start(5)`
    - `5 (Alarm)`: `self.showAlarm()`
    - `6 (Cooldown)`: `self.showNextGuest()`; `self.timer.start(5)`
  - `stateLeft(state: int, event: str) -> None`:
    - If `state in (1, 2, 3, 4, 6)`: `self.timer.cancel()`
    - If `state == 5`: `self.silenceAlarm()`; `self.stats.reset()`
  - `stateDo(state: int) -> None`:
    - `4 (Unhappy)`: Checks `if self.stats.is_low(): self.model.processEvent("feedback_below_threshold")`
    - `5 (Alarm)`: Calls `self.alarmTick()` and `self.flashRed()`
  - `stateEvent(state: int, event: str) -> bool`:
    - Returns `False`.

- **UI Methods (Strictly $\le 16$ chars per line)**:
  - `showWelcome()`:
    - Line 0: `"Welcome!"` (8 chars)
    - Line 1: `"Please step up"` (14 chars)
    - `self.lights.setColor(BLACK)`
  - `showPrompt()`:
    - Line 0: `"Rate your visit:"` (16 chars)
    - Line 1: `"G:)  Y:|  R:("` (14 chars)
  - `showAlarm()`:
    - Line 0: `"MANAGER ALERT!"` (14 chars)
    - Line 1: `"Press G to reset"` (16 chars)
  - `showNextGuest()`:
    - Line 0: `"Thank you!"` (10 chars)
    - Line 1: `"Next guest"` (10 chars)

- **Audio, Light, and Alarm Methods**:
  - `happyChime()`: Plays ascending two-tone chime (`C5` 523Hz 100ms, pause 40ms, `G5` 784Hz 160ms; total ~300ms $< 0.5$s).
  - `neutralTone()`: Plays single tone (`E5` 659Hz 200ms; total 200ms $< 0.5$s).
  - `sadTone()`: Plays descending two-tone chime (`E5` 659Hz 120ms, pause 40ms, `C5` 523Hz 180ms; total ~340ms $< 0.5$s).
  - `showScore()`:
    - Determines `level = self.stats.get_light_level()` and `pct = self.stats.calculate_percentage()`.
    - If `pct >= 70.0`: `color = GREEN`
    - Else if `pct >= 30.0`: `color = YELLOW`
    - Else: `color = RED`
    - Calls `self.lights.setColor(color, level)`.
  - `alarmTick()`:
    - Evaluates `(time.ticks_ms() // 250) % 2`.
    - If 0: `self.buzzer.play(880)`
    - Else: `self.buzzer.play(587)`
  - `flashRed()`:
    - Evaluates `(time.ticks_ms() // 250) % 2`.
    - If 0: `self.lights.setColor(RED)`
    - Else: `self.lights.setColor(BLACK)` (avoiding `lights.off()` sleep delay).
  - `silenceAlarm()`:
    - `self.buzzer.stop()`
    - `self.lights.setColor(BLACK)`
  - `run()`:
    - Calls `self.model.run()`.

---

### File 3: `main.py`

#### Module Header
```python
"""
# main.py
# Main execution entrypoint for Lab 3 Feedback Kiosk.
# Author: Lushana3
"""
```

#### Script Implementation
```python
from FeedbackController import FeedbackController
from Log import *

if __name__ == "__main__":
    Log.i("Starting Feedback Kiosk System...")
    controller = FeedbackController()
    controller.run()
```
