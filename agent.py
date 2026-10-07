"""
MODULE 4b — SmartHomeAgent

Perceive -> Reason -> Act loop behind a single entry point:

    SmartHomeAgent().decide(room)

    PERCEIVE : room.get_sensor_readings()            (confirmed occupancy only)
    REASON   : FuzzyEngine.compute()  (Module 3)  +  rule_base.apply_rules()
    ACT      : room.ac / room.lights / room.curtains

Drop-in replacement for FakeAgent (same decide(room) signature).
"""
import threading

from fuzzy_logic.fuzzy_engine import FuzzyEngine
from agent.rule_base import apply_rules


class SmartHomeAgent:
    def __init__(self, fuzzy_engine=None, verbose=True):
        self.fuzzy = fuzzy_engine or FuzzyEngine()
        self.verbose = verbose
        self.last_decision = None        # the dashboard can show this
        self._lock = threading.Lock()    # decide() can be called from the GUI thread
                                         # and the Auto-Mode thread at the same time

    def decide(self, room):
        with self._lock:
            # ---------------- PERCEIVE ----------------
            readings = room.get_sensor_readings()

            # ---------------- REASON ------------------
            fuzzy_out = self.fuzzy.compute(readings["temperature"], readings["hour"])
            decision = apply_rules(readings, fuzzy_out)

            # ---------------- ACT ---------------------
            self._act(room, decision)

            # ---------------- RECORD ------------------
            decision["inputs"] = dict(readings)
            decision["fuzzy_raw"] = dict(fuzzy_out)
            decision["fuzzy_rules"] = list(self.fuzzy.last_fired_rules)
            self.last_decision = decision

            if self.verbose:
                self._log(decision)
            return decision

    @staticmethod
    def _act(room, d):
        if d["ac_power"] > 0:
            room.ac.turn_on(power_level=d["ac_power"])
        else:
            room.ac.turn_off()

        if d["light_brightness"] > 0:
            room.lights.turn_on(brightness=d["light_brightness"])
        else:
            room.lights.turn_off()

        if d["curtain_position"] > 0:
            room.curtains.open(percent=d["curtain_position"])
        else:
            room.curtains.close()

    @staticmethod
    def _log(d):
        r = d["inputs"]
        print(f"[Agent] {r['temperature']}°C | {'occupied' if r['occupied'] else 'empty'} | "
              f"{r['period']} ({r['hour']}:00)  ->  "
              f"AC {d['ac_power']}%  Lights {d['light_brightness']}%  "
              f"Curtains {d['curtain_position']}%")
        for rule in d["fired_rules"]:
            print(f"        rule: {rule}")