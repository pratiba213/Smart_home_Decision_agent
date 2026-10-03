class ACUnit:
    def __init__(self):
        self.is_on = False
        self.power_level = 0   # 0 to 100

    def turn_on(self, power_level=50):
        self.is_on = True
        self.power_level = power_level

    def turn_off(self):
        self.is_on = False
        self.power_level = 0

    def status(self):
        return {"on": self.is_on, "power": self.power_level}


class LightSystem:
    def __init__(self):
        self.is_on = False
        self.brightness = 0   # 0 to 100

    def turn_on(self, brightness=100):
        self.is_on = True
        self.brightness = brightness

    def turn_off(self):
        self.is_on = False
        self.brightness = 0

    def status(self):
        return {"on": self.is_on, "brightness": self.brightness}


class CurtainSystem:
    def __init__(self):
        self.position = 0   # 0 = closed, 100 = fully open

    def open(self, percent=100):
        self.position = percent

    def close(self):
        self.position = 0

    def status(self):
        return {"position": self.position}