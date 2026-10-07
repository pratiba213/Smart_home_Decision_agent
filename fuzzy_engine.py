"""
MODULE 3 — Fuzzy Logic Engine (Mamdani inference using scikit-fuzzy)

Inputs  : temperature (15-45 °C) and hour (0-23)
Outputs : AC power (0-100 %) and curtain position (0-100 %)

The four Mamdani steps are written out explicitly so they can be explained
in the viva:
    1. Fuzzification   - crisp value -> membership degree per fuzzy set
    2. Rule evaluation - AND = min, OR = max, NOT = 1 - x
    3. Aggregation     - clipped output sets combined with max
    4. Defuzzification - centroid (centre of gravity)

Public interface (the only thing other modules use):
    FuzzyEngine().compute(temperature, hour)
        -> {"ac_power": float, "curtain_position": float}

If anything goes wrong, safe defaults are returned (AC 0, curtains 50) so the
agent loop never crashes on a bad sensor reading.
"""
import math

import numpy as np
import skfuzzy as fuzz


# Operating ranges (also used for input clamping / validation)
TEMP_MIN, TEMP_MAX = 15.0, 45.0
HOUR_MIN, HOUR_MAX = 0, 23

# Safe fallback outputs
DEFAULT_AC_POWER = 0.0
DEFAULT_CURTAIN_POSITION = 50.0


class FuzzyEngine:
    def __init__(self):
        # Universes of discourse
        self.temp_x = np.arange(TEMP_MIN, TEMP_MAX + 0.5, 0.5)     # 15 .. 45
        self.hour_x = np.arange(HOUR_MIN, HOUR_MAX + 1, 1)         # 0 .. 23
        self.out_x = np.arange(0, 101, 1)                          # 0 .. 100

        self._build_membership_functions()

        # Kept for explainability / logging / dashboard
        self.last_memberships = {}
        self.last_fired_rules = []

    # ------------------------------------------------------------------
    # Membership functions
    # ------------------------------------------------------------------
    def _build_membership_functions(self):
        # --- Temperature (from the report, section 4.2) ---
        self.temp_mf = {
            "cold":        fuzz.trapmf(self.temp_x, [15, 15, 18, 22]),
            "comfortable": fuzz.trimf(self.temp_x,  [20, 24, 28]),
            "warm":        fuzz.trimf(self.temp_x,  [25, 29, 33]),
            "hot":         fuzz.trapmf(self.temp_x, [30, 35, 45, 45]),
        }

        # --- Hour of day ---
        # 'night' wraps around midnight, so it is the OR (max) of two shapes.
        # NOTE: the late-night shape starts at 20 (not 21 as in the draft
        # report) so that hour 21 has non-zero membership in some set.
        self.hour_mf = {
            "night": np.fmax(fuzz.trapmf(self.hour_x, [0, 0, 4, 6]),
                             fuzz.trapmf(self.hour_x, [20, 21, 23, 23])),
            "morning":   fuzz.trimf(self.hour_x, [5, 8, 12]),
            "afternoon": fuzz.trimf(self.hour_x, [11, 14, 17]),
            "evening":   fuzz.trimf(self.hour_x, [16, 19, 21]),
        }

        # --- Output: AC power (%) ---
        self.ac_mf = {
            # narrow on purpose: its centroid must stay below the agent's AC_MIN_ON (10 %)
            # however low the rule strength clips it
            "off":    fuzz.trapmf(self.out_x, [0, 0, 5, 15]),
            "low":    fuzz.trimf(self.out_x,  [10, 30, 50]),
            "medium": fuzz.trimf(self.out_x,  [30, 55, 80]),
            "high":   fuzz.trimf(self.out_x,  [70, 100, 100]),
        }

        # --- Output: curtain position (% open) ---
        self.curtain_mf = {
            "closed": fuzz.trapmf(self.out_x, [0, 0, 5, 25]),
            "half":   fuzz.trimf(self.out_x,  [25, 50, 75]),
            "open":   fuzz.trapmf(self.out_x, [75, 95, 100, 100]),
        }

    # ------------------------------------------------------------------
    # Step 1 — Fuzzification
    # ------------------------------------------------------------------
    def _fuzzify(self, temperature, hour):
        t = {name: float(fuzz.interp_membership(self.temp_x, mf, temperature))
             for name, mf in self.temp_mf.items()}
        h = {name: float(fuzz.interp_membership(self.hour_x, mf, hour))
             for name, mf in self.hour_mf.items()}
        return t, h

    # ------------------------------------------------------------------
    # Step 2 — Rule evaluation (IF-THEN rules)
    #   AND = min, OR = max, NOT = 1 - x
    #   Each rule: (description, firing strength, output set name)
    # ------------------------------------------------------------------
    @staticmethod
    def _ac_rules(t, h):
        return [
            ("IF hot THEN AC high",
             t["hot"], "high"),
            ("IF warm AND (afternoon OR evening OR night) THEN AC medium",
             min(t["warm"], max(h["afternoon"], h["evening"], h["night"])), "medium"),
            ("IF warm AND morning THEN AC low",
             min(t["warm"], h["morning"]), "low"),
            ("IF comfortable AND afternoon THEN AC low",
             min(t["comfortable"], h["afternoon"]), "low"),
            ("IF comfortable THEN AC off",
             t["comfortable"], "off"),
            ("IF cold THEN AC off",
             t["cold"], "off"),
        ]

    @staticmethod
    def _curtain_rules(t, h):
        return [
            ("IF morning THEN curtains open",
             h["morning"], "open"),
            ("IF afternoon AND NOT hot THEN curtains half",
             min(h["afternoon"], 1.0 - t["hot"]), "half"),
            ("IF afternoon AND hot THEN curtains closed (block sun)",
             min(h["afternoon"], t["hot"]), "closed"),
            ("IF evening THEN curtains closed",
             h["evening"], "closed"),
            ("IF night THEN curtains closed",
             h["night"], "closed"),
        ]

    # ------------------------------------------------------------------
    # Steps 3 + 4 — Aggregation (max of clipped sets) and centroid
    # ------------------------------------------------------------------
    def _infer(self, rules, output_mf, default):
        aggregated = np.zeros_like(self.out_x, dtype=float)
        for _desc, strength, out_name in rules:
            clipped = np.fmin(strength, output_mf[out_name])      # implication (min)
            aggregated = np.fmax(aggregated, clipped)             # aggregation (max)

        if aggregated.sum() == 0:                # no rule fired -> nothing to defuzzify
            return default
        return float(fuzz.defuzz(self.out_x, aggregated, "centroid"))

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    @staticmethod
    def _sanitize(temperature, hour):
        temperature = float(temperature)
        hour = float(hour)
        if math.isnan(temperature) or math.isnan(hour):
            raise ValueError("NaN sensor value")
        temperature = min(max(temperature, TEMP_MIN), TEMP_MAX)
        hour = int(round(min(max(hour, HOUR_MIN), HOUR_MAX)))
        return temperature, hour

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def compute(self, temperature, hour):
        """
        Run the full Mamdani pipeline.
        Returns {"ac_power": 0-100, "curtain_position": 0-100}.
        """
        try:
            temperature, hour = self._sanitize(temperature, hour)

            t, h = self._fuzzify(temperature, hour)
            ac_rules = self._ac_rules(t, h)
            curtain_rules = self._curtain_rules(t, h)

            ac_power = self._infer(ac_rules, self.ac_mf, DEFAULT_AC_POWER)
            curtain = self._infer(curtain_rules, self.curtain_mf, DEFAULT_CURTAIN_POSITION)

            self.last_memberships = {"temperature": t, "hour": h}
            self.last_fired_rules = [desc for desc, s, _ in ac_rules + curtain_rules if s > 0]

            return {"ac_power": round(ac_power, 1),
                    "curtain_position": round(curtain, 1)}

        except Exception as exc:                 # never let a bad reading crash the agent
            self.last_memberships = {}
            self.last_fired_rules = [f"ERROR -> safe defaults ({exc})"]
            return {"ac_power": DEFAULT_AC_POWER,
                    "curtain_position": DEFAULT_CURTAIN_POSITION}