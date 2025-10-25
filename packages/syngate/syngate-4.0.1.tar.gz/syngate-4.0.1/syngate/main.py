import time
import random
from datetime import datetime
import os

from .import syngate_withopen as f
from . import session_id_generator



f.hide("*", display=False)
f.warning(False)


# ============================================================
# 🕒 High-Precision Timing Utilities
# ============================================================

def sg_display(state: str, fifo_counter: float = 0):
    """
    Single-line SYNGATE display.
    Shows ⟳ xN if fifo_counter > 0 (indicating retry/second round).
    """
    state = state.upper().strip()
    time_str = datetime.now().strftime("%H:%M:%S")

    icons = {
        "HOLDING": "🔴",
        "QUEUING": "🟡",
        "DEQUEUE": "🟢",
        "FLYOVER": "⚫",
    }

    icon = icons.get(state, "⚪")
    retry_suffix = f" ⟳ x{int((fifo_counter) / 0.05)}" if fifo_counter > 0 else ""

    print(f"🧩 SYNGATE ▸ {state:<8} {icon} | {time_str}{retry_suffix}")


def get_precise_timestamp():
    """
    Returns a high-resolution, monotonic timestamp (in seconds).
    """
    return time.perf_counter()


def active_event_tag(queue_name):
    """
    Writes an 'Active' tag with the current high-precision timestamp.
    """
    now = get_precise_timestamp()
    f.w(queue_name, ["Active", now], is2d=False)


def done(queue_name):
    """
    Writes a 'Done' tag with the current high-precision timestamp.
    """
    now = get_precise_timestamp()
    f.w(queue_name, ["Done", now], is2d=False)


def active(queue_name, pulse):
    """
    Writes an 'Active' tag with a timestamp offset by pulse seconds.
    """
    now = get_precise_timestamp()
    f.w(queue_name, ["Active", now + pulse], is2d=False)


def ready_to_go_check(queue_id, pulse):
    """
    Determines whether the last tag is stale enough to proceed.
    Uses high-resolution timing.
    """
    last_write = f.r(queue_id)
    if not last_write:
        return True

    tag_status, tag_timestamp = last_write
    now = get_precise_timestamp()
    elapsed = now - tag_timestamp

    if tag_status == "Active":
        return elapsed > pulse
    elif tag_status == "Done":
        return True
    return False


def jitter(interval=0.1, max_value=1):
    """
    Returns a random jitter value from 0 to max_value in steps of interval.
    """
    if interval <= 0:
        raise ValueError("interval must be > 0")
    if max_value < 0:
        raise ValueError("max_value must be >= 0")

    steps = int(max_value // interval)
    return round(random.randint(0, steps) * interval, 10)


# ============================================================
# 🧭 Precise Real-Time Phase Alignment
# ============================================================

def wait_until_secs_modulo(mod: int, tolerance: float = 0.002):
    """
    Wait until system time (wall clock) % mod is within tolerance (seconds).

    Uses microsecond-level precision with adaptive sleep.
    """
    if mod <= 0:
        raise ValueError("mod must be positive")

    while True:
        now = time.time()
        remainder = now % mod

        if remainder < tolerance or (mod - remainder) < tolerance:
            break

        # Sleep adaptively based on remaining time
        time_to_next = mod - remainder
        time.sleep(0.0005 if time_to_next < 0.01 else min(0.002, time_to_next / 5))


def get_current_time_seconds():
    """
    Returns current seconds + microseconds as a float (wall clock).
    """
    now = datetime.now()
    return now.second + now.microsecond / 1_000_000


def get_last_digit_of_precise_second():
    """
    Returns the last digit of the second (0–9) plus fractional precision.
    """
    fractional = time.time() % 60
    sec = int(fractional)
    return (sec % 10) + (fractional - sec)


def is_in_valid_range(seconds: float) -> bool:
    """
    Checks if the current second falls into a valid 4-second window.
    """
    valid_ranges = [(0, 4), (10, 14), (20, 24), (30, 34), (40, 44), (50, 54)]
    return any(start <= seconds <= end for start, end in valid_ranges)



def is_first_session_id_equal(queue_id, session_id_to_check):
    """
    Checks if the first session ID in the queue matches the given one.

    Args:
        queue_id (str): The queue identifier.
        session_id_to_check (str): Session ID to verify.

    Returns:
        bool: True if it matches, else False.
    """
    last_write = f.r(queue_id)

    if isinstance(last_write, list) and last_write:
        first_session_id = last_write[0]
        return first_session_id == session_id_to_check

    return False

# ============================================================
# 🚪 Precise Entry Gate
# ============================================================

def enter(queue_name, pulse, wait=True, display=True):
    """
    High-precision synchronized entry gate.
    """
    # --- Validate types ---
    if not isinstance(queue_name, str):
        raise TypeError(f"queue_name must be a string, got {type(queue_name).__name__}")
    if not (isinstance(pulse, (int, float)) and pulse > 0):
        raise ValueError(f"pulse must be a positive number, got {pulse}")
    if not isinstance(wait, bool):
        raise TypeError(f"wait must be a bool, got {type(wait).__name__}")
    if not isinstance(display, bool):
        raise TypeError(f"display must be a bool, got {type(display).__name__}")

    queue_name = queue_name.strip()
    session_id = session_id_generator.get()
    queue_id = f"{queue_name}_queue"

    error_counter = 0
    fifo_counter = 0.0
    holding_tag = False # controls red display

    while True:
        try:
            # --- Phase alignment loop ---
            while True:
                seconds = get_current_time_seconds()
                if is_in_valid_range(seconds):
                    yellow_pass = False # error will be raise if 2+ read, dont miss yellow display
                    if ready_to_go_check(queue_name, pulse):
                        if fifo_counter:
                            time.sleep(fifo_counter)
                        break
                    elif not wait:
                        if display:
                            sg_display("FLYOVER")
                        return False
                else:
                    if display and not holding_tag:
                        holding_tag = True
                        sg_display("HOLDING", fifo_counter) 

                # Align tightly with 10s boundaries
                wait_until_secs_modulo(10, tolerance=0.001)

            yellow_pass = True
            if display:
                sg_display("QUEUING")

            lucky_pick = False
            if get_last_digit_of_precise_second() < 4.5:
                f.w(queue_id, session_id, is2d=False)

                if get_last_digit_of_precise_second() < 5:
                    wait_until_secs_modulo(6, tolerance=0.001)
                    lucky_pick = is_first_session_id_equal(queue_id, session_id)

            if lucky_pick:
                if ready_to_go_check(queue_name, pulse):
                    if display:
                        sg_display("DEQUEUE")
                    active_event_tag(queue_name)
                    return True

            elif not lucky_pick and not wait:
                if display:
                    sg_display("FLYOVER")
                return False

            holding_tag = True
            fifo_counter = max(fifo_counter + 0.05, 0)
            sg_display("HOLDING", fifo_counter)
            wait_until_secs_modulo(10, tolerance=0.001)
            
        except (FileNotFoundError, OSError, PermissionError) as e:
            if yellow_pass == False:
                time.sleep(0.25)
                sg_display("QUEUING")
                
            holding_tag = True
            fifo_counter = max(fifo_counter + 0.05, 0)
            sg_display("HOLDING", fifo_counter)
            wait_until_secs_modulo(10, tolerance=0.001)

            
            error_counter += 1
            if error_counter > 12:
                raise
            # Brief recovery delay before retry
            time.sleep(0.005)
