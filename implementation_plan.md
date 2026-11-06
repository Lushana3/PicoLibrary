# Implementation Plan: Digital Door NamePlate System

**Author:** Lushana3  
**Target Project:** PicoLibrary (Raspberry Pi Pico / MicroPython / Wokwi)  
**Task:** Implement the multi-employee digital door nameplate system based on the provided UML class diagram.

---

## 1. Overview & Diagram Mapping

This implementation plan details the architecture, file organization, classes, attributes, methods, and hardware connections for the **NamePlate** system shown in the UML diagram.

### Diagram Elements & Codebase Mapping

| UML Class Diagram Element | Status in Codebase | Target File | Role & Description |
| :--- | :--- | :--- | :--- |
| **`Display`** | Existing | `Displays.py` | Abstract display base class defining `reset()`, `clear()`, `showNumber()`, `showText()`, `scroll()`. |
| **`LCDDisplay`** | Existing | `Displays.py` | Subclass of `Display` interfacing with physical LCD 1602 via I2C or GPIO pins. |
| **`Light`** | Existing | `Lights.py` | Base class for digital/PWM output lights. |
| **`LightStrip`** | Existing | `LightStrip.py` | Subclass of `Light` driving WS2812 / NeoPixel strip for status indication. |
| **`Buzzer`** | Existing | `Buzzer.py` | Base class for buzzer devices. |
| **`PassiveBuzzer`** | Existing | `Buzzer.py` | Subclass of `Buzzer` producing PWM-driven audio tones. |
| **`Button`** | Existing | `Button.py` | Pushbutton class with hardware IRQ and debounce callback dispatch to `handler`. |
| **`Employee`** | **Created** | `Employee.py` | Base class representing an employee with contact details and availability. |
| **`Faculty`** | **Created** | `Employee.py` | Subclass of `Employee` adding courses and office hours. |
| **`Staff`** | **Created** | `Employee.py` | Subclass of `Employee` with staff-specific display formatting. |
| **`StudentWorker`** | **Created** | `Employee.py` | Subclass of `Employee` with student worker display formatting. |
| **`Administrator`** | **Created** | `Employee.py` | Subclass of `Employee` with 24-hour calendar integration and automatic availability. |
| **`NamePlate`** | **Created** | `NamePlate.py` | Core controller managing employees, display, light strip, buzzer, and creating 3 internal buttons. |
| **`main.py`** | **Replaced** | `main.py` | Entrypoint script initializing hardware, employees, and running the `NamePlate`. |

---

## 2. Diagram Relationships & Multiplicities

```
+--------------------------------------------------------------------------+
|                                NamePlate                                 |
+--------------------------------------------------------------------------+
      | 1                     | 1                     | 1            | 1
      | (shows)               | (status light)        | (sounds)     | (receives)
      v                       v                       v              v
+------------+         +------------+         +---------------+  +------------+
| LCDDisplay |         | LightStrip |         | PassiveBuzzer |  | 3x Button  |
+------------+         +------------+         +---------------+  +------------+
      ^                       ^                       ^
      | inherits              | inherits              | inherits
+------------+         +------------+         +---------------+
|  Display   |         |   Light    |         |    Buzzer     |
+------------+         +------------+         +---------------+

                                NamePlate
                                    | 1
                                    | (displays)
                                    v 1..*
                               +----------+
                               | Employee |
                               +----------+
                                    ^
        +---------------+-----------+-----------+---------------+
        |               |                       |               |
   +---------+      +-------+           +---------------+ +---------------+
   | Faculty |      | Staff |           | StudentWorker | | Administrator |
   +---------+      +-------+           +---------------+ +---------------+
```

1. **`NamePlate` $\xrightarrow{\text{displays}}$ `Employee` (`1..*`)**: Aggregates a list of 1 or more `Employee` instances. Navigation is controlled via `previousEmployee()` and `nextEmployee()`.
2. **`NamePlate` $\xrightarrow{\text{receives}}$ `Button` (`3`)**: Composes 3 buttons created internally in `NamePlate.__init__`:
   - **Button 1 ("prev") on GP10**: Navigates to the previous employee.
   - **Button 2 ("next") on GP11**: Navigates to the next employee.
   - **Button 3 ("status") on GP12**: Toggles / cycles the availability status of the current employee (except Administrator, which is automated).
3. **`NamePlate` $\xrightarrow{\text{shows}}$ `LCDDisplay` (`1`)**: Formats and renders 2 lines of 16-character text from the current employee's `getDisplayLines()`. Uses manual whitespace padding (no `ljust()`, which is unsupported in MicroPython).
4. **`NamePlate` $\xrightarrow{\text{status light}}$ `LightStrip` (`1`)**: Visually indicates employee availability using exact status mapping:
   - `"Available"` $\to$ `GREEN`
   - `"Away"` $\to$ `YELLOW`
   - `"Busy"` $\to$ `RED`
5. **`NamePlate` $\xrightarrow{\text{sounds}}$ `PassiveBuzzer` (`1`)**: Plays audible feedback chirps/beeps upon button presses and employee changes.
6. **Inheritance Hierarchies**:
   - `Faculty`, `Staff`, `StudentWorker`, `Administrator` inherit from `Employee`.
   - `LCDDisplay` inherits from `Display`.
   - `LightStrip` inherits from `Light`.
   - `PassiveBuzzer` inherits from `Buzzer`.

---

## 3. File Structure & Responsibilities

- **`Employee.py`**: Contains all 5 employee classes (`Employee`, `Faculty`, `Staff`, `StudentWorker`, and `Administrator`).
- **`NamePlate.py`**: Contains `NamePlate` controller (creates its own 3 buttons inside `__init__`).
- **`main.py`**: Direct hardware driver for Raspberry Pi Pico and Wokwi.

---

## 4. Detailed Specification of Files, Classes, and Methods

### File 1: `Employee.py`

#### Module Header
```python
"""
# Employee.py
# Object-oriented hierarchy representing various employee types for the digital door NamePlate
# Author: Lushana3
"""
```

#### Class 1: `Employee` (Base Class)
- **Attributes:**
  - `name : str` (Public) - Full name of the employee.
  - `title : str` (Public) - Position or job title.
  - `phone : str` (Public) - Office phone or extension.
  - `_available : str` (Private / Protected) - Current availability status string (`"Available"`, `"Away"`, or `"Busy"`).
- **Methods:**
  - `__init__(name: str, title: str, phone: str = "", available: str = "Available")`: Initializes employee attributes.
  - `getAvailability() -> str`: Returns `self._available`.
  - `cycleAvailability() -> str`: Cycles `self._available` using a local list in the exact order: `Available -> Away -> Busy -> Available`.
  - `getDisplayLines() -> list[str]`: Returns 2 lines formatted for a 16x2 LCD display.

#### Class 2: `Faculty` (inherits from `Employee`)
- **Attributes:**
  - Inherited: `name`, `title`, `phone`, `_available`.
  - `courses : list` (Public) - List of course codes taught.
  - `officeHours : str` (Public) - Scheduled office hours.
- **Methods:**
  - `__init__(name: str, title: str = "Faculty", phone: str = "", courses: list = None, officeHours: str = "", available: str = "Available")`: Calls `super().__init__` and initializes faculty fields.
  - `getDisplayLines() -> list[str]`: Line 0 shows faculty name; Line 1 shows office hours or courses.

#### Class 3: `Staff` (inherits from `Employee`)
- **Attributes:**
  - Inherited: `name`, `title`, `phone`, `_available`.
- **Methods:**
  - `__init__(name: str, title: str = "Staff", phone: str = "", available: str = "Available")`: Calls `super().__init__`.
  - `getDisplayLines() -> list[str]`: Line 0 shows name; Line 1 shows title and phone.

#### Class 4: `StudentWorker` (inherits from `Employee`)
- **Attributes:**
  - Inherited: `name`, `title`, `phone`, `_available`.
- **Methods:**
  - `__init__(name: str, title: str = "Student Worker", phone: str = "", available: str = "Available")`: Calls `super().__init__`.
  - `getDisplayLines() -> list[str]`: Line 0 displays student worker name; Line 1 shows title and availability.

#### Class 5: `Administrator` (inherits from `Employee`)
- **Attributes:**
  - Inherited: `name`, `title`, `phone`, `_available`.
  - `calendar : dict` (Public) - Dictionary mapping an integer hour (0-23) to `"Available"`, `"Away"`, or `"Busy"`.
- **Methods:**
  - `__init__(name: str, title: str = "Administrator", phone: str = "", calendar: dict = None, available: str = "Available")`: Initializes administrator attributes and calendar dict.
  - `getAvailability() -> str`: Looks up the current hour using `time.localtime()[3]` in `self.calendar`. Returns that status, or `"Available"` if the hour is not in the calendar.
  - `cycleAvailability()`: Does nothing (administrator availability is controlled automatically by calendar).
  - `getDisplayLines() -> list[str]`: Line 0 shows name; Line 1 shows title and current status.

---

### File 2: `NamePlate.py`

#### Module Header
```python
"""
# NamePlate.py
# Object-oriented implementation of the NamePlate class coordinating display, buttons, status lights, and buzzer
# Author: Lushana3
"""
```

#### Class: `NamePlate`
- **Attributes:**
  - `employees : list[Employee]` - List of registered employees.
  - `index : int` - Index of the active employee.
  - `display : LCDDisplay` - Hardware LCD text display (16x2).
  - `lights : LightStrip` - NeoPixel light strip representing status light.
  - `buzzer : PassiveBuzzer` - Buzzer for audible cues.
  - `buttons : list[Button]` - 3 Button instances created internally in `__init__`.
- **Methods:**
  - `__init__(display, lights, buzzer, employees)`:
    - Stores component references.
    - Creates 3 internal `Button` instances (`"prev"` on GP10, `"next"` on GP11, `"status"` on GP12) with `handler=self`.
    - Renders initial display.
  - `previousEmployee()`:
    - Decrements `index` with wrap-around, plays 800Hz beep, calls `updateDisplay()`.
  - `nextEmployee()`:
    - Increments `index` with wrap-around, plays 1200Hz beep, calls `updateDisplay()`.
  - `buttonPressed(name: str)`:
    - `"prev"` $\to$ `previousEmployee()`
    - `"next"` $\to$ `nextEmployee()`
    - `"status"` $\to$ calls `emp.cycleAvailability()`, plays 1500Hz beep, calls `updateDisplay()`.
  - `buttonReleased(name: str)`:
    - Logs button release.
  - `updateDisplay()`:
    - Obtains lines from `emp.getDisplayLines()`.
    - Manually truncates and pads each line to 16 characters using string slicing and concatenation (no `ljust()`).
    - Writes lines to `display.showText(line0, 0, 0)` and `display.showText(line1, 1, 0)`.
    - Sets `lights.setColor(color)` using exact status:
      - `"Available"` $\to$ `GREEN`
      - `"Away"` $\to$ `YELLOW`
      - `"Busy"` $\to$ `RED`
  - `run()`:
    - Executes the main event loop while pushbuttons operate via hardware interrupts.

---

### File 3: `main.py`

#### Module Header
```python
"""
# main.py
# Main execution script to initialize hardware and run the digital door NamePlate on Raspberry Pi Pico / Wokwi
# Author: Lushana3
"""
```

#### Contents & Workflow
1. **Direct Hardware Initialization**:
   - `LCDDisplay(sda=0, scl=1)`
   - `PassiveBuzzer(pin=16)`
   - `LightStrip(pin=2, numleds=8, brightness=0.5)`
2. **24-Hour Administrator Calendar**:
   - Covers all 24 hours (0-23) with a realistic mix of `"Available"`, `"Away"`, and `"Busy"` so it can be tested at any hour of the day.
3. **Employee Population**:
   - `Faculty`: Dr. Ada Lovelace (CS101, CS201; OH: MWF 10-12)
   - `Staff`: Grace Hopper (Lab Coord, x4002)
   - `StudentWorker`: Alan Turing (Peer Tutor, x4003)
   - `Administrator`: M. Hamilton (Chair, x4000, 24-hour calendar)
4. **Execution**:
   - Instantiates `NamePlate(display=lcd, lights=lights, buzzer=buzzer, employees=employees)` (NamePlate creates its own buttons).
   - Starts `plate.run()`.
