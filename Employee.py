"""
# Employee.py
# Object-oriented hierarchy representing various employee types for the digital door NamePlate
# Author: Lushana3
"""

import time
from Log import *

class Employee:
    """
    **Employee**

    Base class representing an employee with name, title, contact information,
    and availability status for display on the digital door NamePlate.

    Parameters:
    ----------
    name : str
        The full name of the employee.
    title : str
        The job or professional title of the employee.
    phone : str, optional
        Office phone number or extension (default: "").
    available : str, optional
        Initial availability status (default: "Available").

    Examples:
    ---------
    1. Create a basic employee and check status:
       ```python
       emp = Employee("Jane Doe", "Technician", phone="x1234")
       print(emp.getAvailability())
       ```
    2. Cycle availability:
       ```python
       emp.cycleAvailability()
       ```
    """

    def __init__(self, name, title, phone="", available="Available"):
        """
        Initialize base employee attributes.

        Parameters:
        ----------
        name : str
            Full name of employee.
        title : str
            Position or title.
        phone : str, optional
            Phone number or extension.
        available : str, optional
            Initial availability status string.
        """
        self.name = name
        self.title = title
        self.phone = phone
        self._available = available
        Log.i(f"Employee created: {self.name} ({self.title})")

    def getAvailability(self):
        """
        Return the current availability status string.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. status = emp.getAvailability()
        """
        return self._available

    def cycleAvailability(self):
        """
        Cycle the employee's availability status through standard states:
        Available -> Away -> Busy -> Available.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. emp.cycleAvailability()
        """
        states = ["Available", "Away", "Busy"]
        if self._available in states:
            idx = (states.index(self._available) + 1) % len(states)
            self._available = states[idx]
        else:
            self._available = states[0]
        Log.i(f"Employee {self.name} availability cycled to: {self._available}")
        return self._available

    def getDisplayLines(self):
        """
        Return two lines of text formatted for a 16x2 character LCD display.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. lines = emp.getDisplayLines()
        """
        line0 = f"{self.name[:16]}"
        line1 = f"{self.title[:10]} {self.getAvailability()[:5]}"[:16]
        return [line0, line1]


class Faculty(Employee):
    """
    **Faculty**

    Subclass of Employee representing academic faculty, including courses
    taught and scheduled office hours.

    Parameters:
    ----------
    name : str
        Full name of the faculty member.
    title : str, optional
        Faculty title (default: "Faculty").
    phone : str, optional
        Phone number or extension (default: "").
    courses : list, optional
        List of course code strings taught (default: None).
    officeHours : str, optional
        Scheduled office hours string (default: "").
    available : str, optional
        Initial availability status (default: "Available").

    Examples:
    ---------
    1. Create a faculty member:
       ```python
       fac = Faculty("Dr. Smith", "Professor", courses=["CS101"], officeHours="MWF 10-12")
       lines = fac.getDisplayLines()
       ```
    """

    def __init__(self, name, title="Faculty", phone="", courses=None, officeHours="", available="Available"):
        """
        Initialize faculty attributes including courses and office hours.
        """
        super().__init__(name, title, phone, available)
        self.courses = courses if courses is not None else []
        self.officeHours = officeHours
        Log.i(f"Faculty created: {self.name}, courses: {self.courses}, OH: {self.officeHours}")

    def getDisplayLines(self):
        """
        Return two lines formatted for 16x2 LCD display tailored for faculty.
        Line 0 shows name; Line 1 shows office hours or courses.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. lines = faculty.getDisplayLines()
        """
        line0 = f"{self.name[:16]}"
        if self.officeHours:
            line1 = f"OH: {self.officeHours}"[:16]
        elif self.courses:
            line1 = f"C: {', '.join(self.courses)}"[:16]
        else:
            line1 = f"{self.title[:10]} {self.getAvailability()[:5]}"[:16]
        return [line0, line1]


class Staff(Employee):
    """
    **Staff**

    Subclass of Employee representing staff members.

    Parameters:
    ----------
    name : str
        Full name of the staff member.
    title : str, optional
        Staff position title (default: "Staff").
    phone : str, optional
        Phone extension (default: "").
    available : str, optional
        Initial availability status (default: "Available").

    Examples:
    ---------
    1. Create a staff member:
       ```python
       staff = Staff("Grace Hopper", "Lab Coord", phone="x4002")
       ```
    """

    def __init__(self, name, title="Staff", phone="", available="Available"):
        """
        Initialize staff attributes.
        """
        super().__init__(name, title, phone, available)
        Log.i(f"Staff created: {self.name} ({self.title})")

    def getDisplayLines(self):
        """
        Return two lines formatted for 16x2 LCD display tailored for staff.
        Line 0 shows name; Line 1 shows title and phone.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. lines = staff.getDisplayLines()
        """
        line0 = f"{self.name[:16]}"
        if self.phone:
            line1 = f"{self.title[:9]} {self.phone[:6]}"[:16]
        else:
            line1 = f"{self.title[:16]}"
        return [line0, line1]


class StudentWorker(Employee):
    """
    **StudentWorker**

    Subclass of Employee representing student workers.

    Parameters:
    ----------
    name : str
        Full name of the student worker.
    title : str, optional
        Position title (default: "Student Worker").
    phone : str, optional
        Phone extension (default: "").
    available : str, optional
        Initial availability status (default: "Available").

    Examples:
    ---------
    1. Create a student worker:
       ```python
       sw = StudentWorker("Alan Turing", "Peer Tutor")
       ```
    """

    def __init__(self, name, title="Student Worker", phone="", available="Available"):
        """
        Initialize student worker attributes.
        """
        super().__init__(name, title, phone, available)
        Log.i(f"StudentWorker created: {self.name} ({self.title})")

    def getDisplayLines(self):
        """
        Return two lines formatted for 16x2 LCD display tailored for student workers.
        Line 0 displays name prefixed with SW; Line 1 shows title and availability.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. lines = sw.getDisplayLines()
        """
        line0 = f"SW: {self.name[:12]}"
        line1 = f"{self.title[:10]} {self.getAvailability()[:5]}"[:16]
        return [line0, line1]


class Administrator(Employee):
    """
    **Administrator**

    Subclass of Employee representing administrators whose availability is
    automatically derived from a 24-hour calendar mapping hours (int 0-23)
    to status ("Available", "Away", or "Busy").

    Parameters:
    ----------
    name : str
        Full name of the administrator.
    title : str, optional
        Administrative title (default: "Administrator").
    phone : str, optional
        Phone extension (default: "").
    calendar : dict, optional
        Dictionary mapping hour integer (0-23) to "Available", "Away", or "Busy" (default: None).
    available : str, optional
        Initial availability status (default: "Available").

    Examples:
    ---------
    1. Create an administrator with a 24-hour calendar:
       ```python
       cal = {9: "Busy", 10: "Available", 11: "Away"}
       admin = Administrator("M. Hamilton", "Chair", calendar=cal)
       print(admin.getAvailability())
       ```
    """

    def __init__(self, name, title="Administrator", phone="", calendar=None, available="Available"):
        """
        Initialize administrator attributes and calendar.
        """
        super().__init__(name, title, phone, available)
        self.calendar = calendar if calendar is not None else {}
        Log.i(f"Administrator created: {self.name}, calendar hours registered: {len(self.calendar)}")

    def getAvailability(self):
        """
        Return current availability based on current hour from calendar,
        defaulting to 'Available' if the hour is not in the calendar.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. status = admin.getAvailability()
        """
        if self.calendar:
            current_hour = time.localtime()[3]
            return self.calendar.get(current_hour, "Available")
        return self._available

    def cycleAvailability(self):
        """
        Administrator availability is automatically determined by calendar;
        cannot be manually cycled by button presses.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. admin.cycleAvailability()
        """
        Log.i(f"Administrator {self.name} availability is controlled by calendar and cannot be cycled")

    def getDisplayLines(self):
        """
        Return two lines formatted for 16x2 LCD display tailored for administrators.
        Line 0 shows name; Line 1 shows title and current availability.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. lines = admin.getDisplayLines()
        """
        line0 = f"{self.name[:16]}"
        line1 = f"{self.title[:9]} {self.getAvailability()[:6]}"[:16]
        return [line0, line1]


if __name__ == "__main__":
    Log.i("Running self-contained verification for Employee classes...")

    # 1. Base Employee cycling: Available -> Away -> Busy -> Available
    emp = Employee("Test User", "Engineer", phone="x111", available="Available")
    assert emp.getAvailability() == "Available"
    emp.cycleAvailability()
    assert emp.getAvailability() == "Away"
    emp.cycleAvailability()
    assert emp.getAvailability() == "Busy"
    emp.cycleAvailability()
    assert emp.getAvailability() == "Available"

    # 2. Faculty
    fac = Faculty("Dr. Ada Lovelace", "Professor", "x4001", ["CS101", "CS201"], "MWF 10-12")
    assert fac.courses == ["CS101", "CS201"]
    assert fac.officeHours == "MWF 10-12"
    assert "MWF 10-12" in fac.getDisplayLines()[1]

    # 3. Staff
    staff = Staff("Grace Hopper", "Lab Coord", "x4002")
    assert "Grace Hopper" in staff.getDisplayLines()[0]
    assert "x4002" in staff.getDisplayLines()[1]

    # 4. StudentWorker
    sw = StudentWorker("Alan Turing", "Peer Tutor", "x4003")
    assert "SW: Alan Tur" in sw.getDisplayLines()[0]

    # 5. Administrator with 24-hour calendar lookup
    current_hour = time.localtime()[3]
    test_cal = {current_hour: "Busy"}
    admin = Administrator("M. Hamilton", "Chair", "x4000", calendar=test_cal)
    assert admin.getAvailability() == "Busy"
    admin.cycleAvailability()  # Should do nothing
    assert admin.getAvailability() == "Busy"

    # Test hour not in calendar defaults to "Available"
    admin_empty = Administrator("Empty Admin", "Director", calendar={})
    assert admin_empty.getAvailability() == "Available"

    Log.i("Testing complete - all Employee hierarchy checks passed successfully")
