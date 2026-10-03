import tkinter as tk
import threading
import time


class Dashboard:
    """
    Live GUI for the Smart Home Decision Agent simulation.
    Displays sensor readings and device states.
    Provides manual controls to trigger different scenarios.
    Also shows raw vs. confirmed occupancy to demonstrate
    false-positive/false-negative filtering.
    """
    def __init__(self, room, agent):
        self.room = room
        self.agent = agent
        self.auto_mode = False

        self.root = tk.Tk()
        self.root.title("Smart Home Decision Agent")
        self.root.geometry("640x460")
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="Smart Home Decision Agent",
                 font=("Arial", 16, "bold")).pack(pady=10)

        # --- Sensors panel ---
        sensor_frame = tk.LabelFrame(self.root, text="Sensors", padx=10, pady=10)
        sensor_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.temp_label = tk.Label(sensor_frame, text="Temp: --", font=("Arial", 12))
        self.temp_label.pack(anchor="w")
        self.occ_label = tk.Label(sensor_frame, text="Occupied (confirmed): --", font=("Arial", 12))
        self.occ_label.pack(anchor="w")
        self.raw_occ_label = tk.Label(sensor_frame, text="Occupied (raw sensor): --",
                                       font=("Arial", 10), fg="gray40")
        self.raw_occ_label.pack(anchor="w")
        self.time_label = tk.Label(sensor_frame, text="Time: --", font=("Arial", 12))
        self.time_label.pack(anchor="w")

        # --- Devices panel ---
        device_frame = tk.LabelFrame(self.root, text="Devices", padx=10, pady=10)
        device_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        self.ac_label = tk.Label(device_frame, text="AC: --", font=("Arial", 12))
        self.ac_label.pack(anchor="w")
        self.light_label = tk.Label(device_frame, text="Lights: --", font=("Arial", 12))
        self.light_label.pack(anchor="w")
        self.curtain_label = tk.Label(device_frame, text="Curtains: --", font=("Arial", 12))
        self.curtain_label.pack(anchor="w")

        # --- Controls ---
        ctrl_frame = tk.Frame(self.root)
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(ctrl_frame, text="Toggle Occupancy",
                  command=self._toggle_occ).pack(side="left", padx=5)
        tk.Button(ctrl_frame, text="Run Agent Once",
                  command=self._run_once).pack(side="left", padx=5)
        self.auto_btn = tk.Button(ctrl_frame, text="Auto Mode: OFF",
                                    command=self._toggle_auto)
        self.auto_btn.pack(side="left", padx=5)

        # --- Temperature slider ---
        tk.Label(self.root, text="Set Temperature (°C):").pack()
        self.temp_slider = tk.Scale(self.root, from_=15, to=40,
                                     orient="horizontal", length=350,
                                     command=self._set_temp)
        self.temp_slider.set(28)
        self.temp_slider.pack()

        # --- Note explaining the raw vs confirmed distinction ---
        tk.Label(self.root,
                 text="Note: 'raw sensor' can flicker (simulated false triggers).\n"
                      "'confirmed' is the filtered value the agent actually uses.",
                 font=("Arial", 9), fg="gray50").pack(pady=(10, 0))

        self._update_display()

    def _update_display(self):
        readings = self.room.get_sensor_readings()
        raw_occupied = self.room.get_raw_occupancy()
        states = self.room.get_device_states()

        self.temp_label.config(text=f"Temp: {readings['temperature']}°C")
        self.occ_label.config(text=f"Occupied (confirmed): {'YES' if readings['occupied'] else 'NO'}")
        self.raw_occ_label.config(text=f"Occupied (raw sensor): {'YES' if raw_occupied else 'NO'}")
        self.time_label.config(text=f"Time: {readings['period'].title()} ({readings['hour']}:00)")

        ac = states["ac"]
        self.ac_label.config(text=f"AC: {'ON' if ac['on'] else 'OFF'}  |  Power: {ac['power']}%")

        lights = states["lights"]
        self.light_label.config(text=f"Lights: {'ON' if lights['on'] else 'OFF'}  |  Brightness: {lights['brightness']}%")

        curtains = states["curtains"]
        self.curtain_label.config(text=f"Curtains: {curtains['position']}% open")

        self.root.after(1000, self._update_display)   # refresh every second

    def _toggle_occ(self):
        self.room.occupancy_sensor.toggle()

    def _set_temp(self, val):
        self.room.temp_sensor.set_temperature(val)

    def _run_once(self):
        self.agent.decide(self.room)

    def _toggle_auto(self):
        self.auto_mode = not self.auto_mode
        self.auto_btn.config(text=f"Auto Mode: {'ON' if self.auto_mode else 'OFF'}")
        if self.auto_mode:
            threading.Thread(target=self._auto_loop, daemon=True).start()

    def _auto_loop(self):
        while self.auto_mode:
            self.agent.decide(self.room)
            time.sleep(3)

    def run(self):
        self.root.mainloop()