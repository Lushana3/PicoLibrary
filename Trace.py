"""
# Trace.py
# Prints sequence-diagram style messages with a running timestamp so the
# console output can be compared line by line with the UML sequence diagrams.
# Author: Lushana3
"""

import time

_start = time.ticks_ms()


def seq(sender, receiver, message):
    """
    Print one message arrow:  [   1234 ms] Sender -> Receiver: message
    """
    elapsed = time.ticks_diff(time.ticks_ms(), _start)
    print(f"[{elapsed:>7} ms] {sender} -> {receiver}: {message}")


def note(text):
    """ Print a note (not a message), e.g. timing summaries """
    elapsed = time.ticks_diff(time.ticks_ms(), _start)
    print(f"[{elapsed:>7} ms] NOTE: {text}")
