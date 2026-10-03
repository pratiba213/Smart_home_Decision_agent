import random
import datetime


class TemperatureSensor:
    """
    Simulates a temperature sensor.
    Returns temperature in Celsius.
    """
    def __init__(self, base_temp=28.0):
        self.base_temp = base_temp
        self.current_temp = base_temp

    def read(self):
        fluctuation = random.uniform(-0.3, 0.3)
        self.current_temp += fluctuation
        self.current_temp = round(self.current_temp, 1)
        return self.current_temp

    def set_temperature(self, temp):
        """Allows manual override — used by the dashboard slider."""
        self.current_temp = float(temp)


class OccupancySensor:
    """
    Simulates a PIR motion/occupancy sensor.

    Real PIR sensors suffer from two well-documented error types:
      - False-on (false positive): reports occupied when nobody is there
        (triggered by noise, sunlight, air currents, pets)
      - False-off (false negative): reports empty when someone IS there
        but sitting still, or outside line of sight

    This class simulates both error types, then applies a confirmation
    buffer (same idea as sensor-fusion/temporal smoothing used in real
    occupancy-detection research) so a single bad reading doesn't
    immediately flip the system's decision.
    """
    def __init__(self, false_positive_rate=0.05, false_negative_rate=0.08,
                 confirmation_threshold=2):
        self.true_occupied = False          # the "ground truth" — what's actually true
        self.false_positive_rate = false_positive_rate   # chance of a false "YES" when empty
        self.false_negative_rate = false_negative_rate   # chance of a false "NO" when occupied
        self.confirmation_threshold = confirmation_threshold

        self._raw_reading = False           # the noisy, unfiltered sensor output
        self._confirmed_state = False       # the trusted, filtered output
        self._pending_state = False
        self._pending_count = 0

    def _simulate_raw_reading(self):
        """
        Produces one noisy PIR-style reading based on the true state,
        with a chance of false-on / false-off error.
        """
        if self.true_occupied:
            # Chance of a false-off: sensor misses a real occupant
            if random.random() < self.false_negative_rate:
                return False
            return True
        else:
            # Chance of a false-on: sensor falsely triggers on an empty room
            if random.random() < self.false_positive_rate:
                return True
            return False

    def read(self):
        """
        Returns the CONFIRMED occupancy state (filtered, trustworthy).
        This is what the agent/rule base should always use.
        """
        self._raw_reading = self._simulate_raw_reading()

        # Confirmation buffer: only accept a state change after it
        # repeats `confirmation_threshold` times in a row.
        if self._raw_reading == self._confirmed_state:
            self._pending_count = 0
        else:
            if self._raw_reading == self._pending_state:
                self._pending_count += 1
            else:
                self._pending_state = self._raw_reading
                self._pending_count = 1

            if self._pending_count >= self.confirmation_threshold:
                self._confirmed_state = self._raw_reading
                self._pending_count = 0

        return self._confirmed_state

    def read_raw(self):
        """
        Returns the UNFILTERED, noisy reading — useful for the dashboard
        to visibly demonstrate false triggers during a demo.
        """
        return self._raw_reading

    def toggle(self):
        """Toggles the TRUE occupancy state (ground truth), e.g. person walks in/out."""
        self.true_occupied = not self.true_occupied

    def set(self, state: bool):
        """Manually sets the TRUE occupancy state."""
        self.true_occupied = bool(state)


class TimeModule:
    """
    Returns the current time of day.
    Uses the real system clock.
    """
    def read(self):
        return datetime.datetime.now().hour  # 0-23

    def get_period(self):
        hour = self.read()
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"