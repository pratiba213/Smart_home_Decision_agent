from simulation.sensors import TemperatureSensor, OccupancySensor, TimeModule
from simulation.devices import ACUnit, LightSystem, CurtainSystem


class Room:
    """
    Represents the entire simulated smart home environment.
    Owns every sensor and every device.
    """
    def __init__(self):
        # Sensors
        self.temp_sensor = TemperatureSensor(base_temp=28.0)
        self.occupancy_sensor = OccupancySensor()
        self.time_module = TimeModule()

        # Devices
        self.ac = ACUnit()
        self.lights = LightSystem()
        self.curtains = CurtainSystem()

    def get_sensor_readings(self):
        """
        Returns current sensor snapshot. Key names are fixed by the
        interface contract — unchanged from before.
        'occupied' is the CONFIRMED (filtered) value, safe for the
        agent to make decisions on.
        """
        return {
            "temperature": self.temp_sensor.read(),
            "occupied": self.occupancy_sensor.read(),
            "hour": self.time_module.read(),
            "period": self.time_module.get_period()
        }

    def get_raw_occupancy(self):
        """
        NEW: returns the unfiltered, noisy occupancy reading —
        only used by the dashboard to visually demonstrate false
        triggers. The agent must never use this.
        """
        return self.occupancy_sensor.read_raw()

    def get_device_states(self):
        """Returns current device states for the dashboard to display."""
        return {
            "ac": self.ac.status(),
            "lights": self.lights.status(),
            "curtains": self.curtains.status()
        }
