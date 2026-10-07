"""
MODULE 4a — Rule Base (crisp rules)

Takes the sensor readings + the fuzzy engine's suggestion and produces the
FINAL decision. Pure function: no device access, easy to test.

Priority order (highest first):
    (i)   not occupied              -> AC off, lights off      (occupancy override)
    (ii)  morning AND occupied      -> curtains 100 % open
    (iii) night AND not occupied    -> curtains closed (privacy)
    (iv)  afternoon AND temp > 32   -> curtains closed (block sun, reduce AC load)

Lighting is purely rule-based (not fuzzy):
    occupied: evening/night 100 %, morning 60 %, afternoon 0 %.   empty: 0 %.
"""

AC_MIN_ON = 10                 # fuzzy output below this % means "AC stays off"
CURTAIN_SNAP_CLOSED = 15       # fuzzy curtain <= 15 % -> fully closed
CURTAIN_SNAP_OPEN = 85         # fuzzy curtain >= 85 % -> fully open
HOT_AFTERNOON_TEMP = 32        # °C, rule (iv)

LIGHTS_WHEN_OCCUPIED = {
    "morning": 60,
    "afternoon": 0,
    "evening": 100,
    "night": 100,
}


def _clamp_percent(value):
    return int(round(min(max(float(value), 0), 100)))


def apply_rules(readings, fuzzy_output):
    """
    readings     : dict from Room.get_sensor_readings()
                   (temperature, occupied, hour, period)
    fuzzy_output : dict from FuzzyEngine.compute()
                   (ac_power, curtain_position)

    Returns a dict:
        ac_power, light_brightness, curtain_position   (ints, 0-100)
        fired_rules                                    (list of strings)
    """
    temperature = readings["temperature"]
    occupied = bool(readings["occupied"])
    period = readings["period"]
    fired = []

    # ---- start from the fuzzy suggestion --------------------------------
    ac = _clamp_percent(fuzzy_output["ac_power"])
    if ac < AC_MIN_ON:
        ac = 0

    curtain = _clamp_percent(fuzzy_output["curtain_position"])
    if curtain <= CURTAIN_SNAP_CLOSED:
        curtain = 0
    elif curtain >= CURTAIN_SNAP_OPEN:
        curtain = 100

    # ---- lighting schedule (crisp) --------------------------------------
    if occupied:
        light = LIGHTS_WHEN_OCCUPIED.get(period, 0)
        fired.append(f"Lighting schedule: occupied in {period} -> lights {light}%")
    else:
        light = 0

    # ---- crisp overrides, in priority order -----------------------------
    # (i) occupancy override
    if not occupied:
        ac = 0
        light = 0
        fired.append("(i) Room empty -> AC off, lights off")

    # (ii) morning sun when someone is in
    if period == "morning" and occupied:
        curtain = 100
        fired.append("(ii) Morning + occupied -> curtains 100% open")

    # (iii) privacy at night when empty
    if period == "night" and not occupied:
        curtain = 0
        fired.append("(iii) Night + empty -> curtains closed")

    # (iv) block afternoon heat
    if period == "afternoon" and temperature > HOT_AFTERNOON_TEMP:
        curtain = 0
        fired.append(f"(iv) Afternoon + temp > {HOT_AFTERNOON_TEMP}°C -> curtains closed")

    return {
        "ac_power": ac,
        "light_brightness": light,
        "curtain_position": curtain,
        "fired_rules": fired,
    }