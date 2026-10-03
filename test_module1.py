from simulation.environment import Room

print("=== Testing Module 1: Room Environment (with sensor noise) ===\n")

room = Room()

print("Initial sensor readings:")
print(room.get_sensor_readings())

print("\n--- Setting TRUE occupancy to True (person actually walks in) ---")
room.occupancy_sensor.set(True)

print("\nWatching confirmed vs raw readings over 6 cycles")
print("(confirmed should settle to True after ~2 consistent raw readings):\n")
for i in range(6):
    confirmed = room.get_sensor_readings()["occupied"]
    raw = room.get_raw_occupancy()
    print(f"Cycle {i+1}: raw={raw}   confirmed={confirmed}")

print("\n--- Setting TRUE occupancy back to False (person leaves) ---")
room.occupancy_sensor.set(False)

print("\nWatching confirmed vs raw readings over 6 more cycles:\n")
for i in range(6):
    confirmed = room.get_sensor_readings()["occupied"]
    raw = room.get_raw_occupancy()
    print(f"Cycle {i+1}: raw={raw}   confirmed={confirmed}")

print("\n--- Manually changing temperature to 34°C ---")
room.temp_sensor.set_temperature(34)
print(room.get_sensor_readings())

print("\n--- Manually turning AC ON at 70% ---")
room.ac.turn_on(power_level=70)
print(room.get_device_states())

print("\n=== Module 1 test complete ===")