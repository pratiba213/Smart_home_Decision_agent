class FakeAgent:
    """
    Temporary stand-in for the real SmartHomeAgent.
    Has the same method signature: decide(room).
    Delete this file once your teammate's real agent.py is ready.
    """
    def decide(self, room):
        readings = room.get_sensor_readings()

        if readings["temperature"] > 30 and readings["occupied"]:
            room.ac.turn_on(power_level=75)
        else:
            room.ac.turn_off()

        if readings["occupied"] and readings["period"] in ["evening", "night"]:
            room.lights.turn_on(brightness=100)
        else:
            room.lights.turn_off()

        if readings["period"] == "morning":
            room.curtains.open(percent=100)
        elif readings["period"] == "night":
            room.curtains.close()

        print(f"[FakeAgent] Decision made based on: {readings}")