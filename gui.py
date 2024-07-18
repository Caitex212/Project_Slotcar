import tkinter as tk
from tkinter import ttk, messagebox
from data_manager import load_data, save_data
from serial_communication import record_lap_time
import threading
import time
import pygame
import serial

class SlotCarManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Slot Car Rally Manager")

        self.drivers = load_data('drivers.json')
        self.results = load_data('results.json')
        self.serial_port = 'COM3'
        self.early_start_penalty = 2  # default 2 seconds penalty

        self.create_widgets()
        pygame.mixer.init()

    def create_widgets(self):
        frame = tk.Frame(self.root, bg='#f0f0f0', bd=2, relief='sunken')
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.driver_label = tk.Label(frame, text="Driver Name:", bg='#f0f0f0')
        self.driver_label.grid(row=0, column=0, pady=5)

        self.driver_entry = tk.Entry(frame)
        self.driver_entry.grid(row=0, column=1, pady=5)

        self.add_driver_button = tk.Button(frame, text="Add Driver", command=self.add_driver, bg='#007bff', fg='white', relief='raised', bd=2)
        self.add_driver_button.grid(row=0, column=2, pady=5, padx=5)

        self.remove_driver_button = tk.Button(frame, text="Remove Driver", command=self.remove_driver, bg='#dc3545', fg='white', relief='raised', bd=2)
        self.remove_driver_button.grid(row=0, column=3, pady=5, padx=5)

        self.driver_listbox = tk.Listbox(frame, bg='white', relief='groove', bd=2)
        self.driver_listbox.grid(row=1, column=0, columnspan=4, pady=10, sticky="nsew")
        self.update_driver_listbox()

        self.laps_label = tk.Label(frame, text="Number of Laps:", bg='#f0f0f0')
        self.laps_label.grid(row=2, column=0, pady=5)

        self.laps_entry = tk.Entry(frame)
        self.laps_entry.grid(row=2, column=1, pady=5)

        self.start_race_button = tk.Button(frame, text="Start Race", command=self.start_race, bg='#28a745', fg='white', relief='raised', bd=2)
        self.start_race_button.grid(row=2, column=2, pady=5, padx=5)

        self.port_label = tk.Label(frame, text="Serial Port:", bg='#f0f0f0')
        self.port_label.grid(row=3, column=0, pady=5)

        self.port_entry = tk.Entry(frame)
        self.port_entry.insert(0, self.serial_port)
        self.port_entry.grid(row=3, column=1, pady=5)

        self.set_port_button = tk.Button(frame, text="Set Port", command=self.set_serial_port, bg='#17a2b8', fg='white', relief='raised', bd=2)
        self.set_port_button.grid(row=3, column=2, pady=5, padx=5)

        self.penalty_label = tk.Label(frame, text="Early Start Penalty (s):", bg='#f0f0f0')
        self.penalty_label.grid(row=4, column=0, pady=5)

        self.penalty_entry = tk.Entry(frame)
        self.penalty_entry.insert(0, str(self.early_start_penalty))
        self.penalty_entry.grid(row=4, column=1, pady=5)

        self.set_penalty_button = tk.Button(frame, text="Set Penalty", command=self.set_early_start_penalty, bg='#17a2b8', fg='white', relief='raised', bd=2)
        self.set_penalty_button.grid(row=4, column=2, pady=5, padx=5)

        self.countdown_label = tk.Label(frame, text="", font=("Helvetica", 16), bg='#f0f0f0')
        self.countdown_label.grid(row=5, column=0, columnspan=4, pady=10)

        self.results_button = tk.Button(frame, text="Show Results", command=self.show_results, bg='#ffc107', fg='white', relief='raised', bd=2)
        self.results_button.grid(row=6, column=0, columnspan=4, pady=10)

        self.results_table = ttk.Treeview(frame, columns=("Driver", "Last Lap", "Best Lap"), show='headings', style="Custom.Treeview")
        self.results_table.heading("Driver", text="Driver")
        self.results_table.heading("Last Lap", text="Last Lap (s)")
        self.results_table.heading("Best Lap", text="Best Lap (s)")
        self.results_table.column("Driver", anchor=tk.CENTER, width=150)
        self.results_table.column("Last Lap", anchor=tk.CENTER, width=150)
        self.results_table.column("Best Lap", anchor=tk.CENTER, width=150)
        self.results_table.grid(row=7, column=0, columnspan=4, pady=10, sticky="nsew")
        self.update_results_table()

    def set_serial_port(self):
        try:
            self.serial_port = self.port_entry.get()
            messagebox.showinfo("Serial Port Set", f"Serial port set to {self.serial_port}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set serial port: {str(e)}")

    def set_early_start_penalty(self):
        try:
            self.early_start_penalty = int(self.penalty_entry.get())
            messagebox.showinfo("Penalty Set", f"Early start penalty set to {self.early_start_penalty} seconds")
        except ValueError:
            messagebox.showerror("Error", "Invalid penalty value. Please enter an integer.")

    def add_driver(self):
        try:
            driver_name = self.driver_entry.get()
            if driver_name:
                self.drivers.append(driver_name)
                save_data('drivers.json', self.drivers)
                messagebox.showinfo("Success", f"Driver {driver_name} added.")
                self.driver_entry.delete(0, tk.END)
                self.update_driver_listbox()
            else:
                messagebox.showerror("Error", "Driver name cannot be empty.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add driver: {str(e)}")

    def remove_driver(self):
        try:
            selected_driver = self.driver_listbox.curselection()
            if selected_driver:
                driver_name = self.driver_listbox.get(selected_driver)
                self.drivers.remove(driver_name)
                self.results = [result for result in self.results if result['driver'] != driver_name]
                save_data('drivers.json', self.drivers)
                save_data('results.json', self.results)
                messagebox.showinfo("Success", f"Driver {driver_name} removed.")
                self.update_driver_listbox()
                self.update_results_table()
            else:
                messagebox.showerror("Error", "No driver selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove driver: {str(e)}")


    def update_driver_listbox(self):
        try:
            self.driver_listbox.delete(0, tk.END)
            for driver in self.drivers:
                self.driver_listbox.insert(tk.END, driver)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update driver list: {str(e)}")

    def start_race(self):
        try:
            selected_driver = self.driver_listbox.curselection()
            if selected_driver:
                driver = self.driver_listbox.get(selected_driver)
                laps = self.get_number_of_laps()
                
                if driver and laps:
                    threading.Thread(target=self.countdown, args=(5, driver, laps)).start()  # 5 second countdown
            else:
                messagebox.showerror("Error", "No driver selected.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start race: {str(e)}")

    def play_countdown_sound(self, second):
        try:
            sound_file = f"sounds/{second}.wav"
            pygame.mixer.Sound(sound_file).play()
        except Exception as e:
            print(f"Failed to play countdown sound: {str(e)}")

    def countdown(self, seconds, driver, laps):
        try:
            with serial.Serial(self.serial_port, 9600, timeout=1) as ser:
                for second in range(seconds, 0, -1):
                    self.countdown_label.config(text=f"Race starts in {second}...")
                    self.play_countdown_sound(second)
                    time.sleep(1)
                    check_early = False
                    if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8').strip()
                            if line == '1':
                                check_early = True
                    if check_early:
                        ser.close()
                        self.countdown_label.config(text="Early Start!")
                        self.play_countdown_sound("GO")
                        self.run_race(driver, laps, True, True)
                        return
            self.countdown_label.config(text="Go!")
            self.play_countdown_sound("GO")
            ser.close()
            self.run_race(driver, laps, False, False)
        except Exception as e:
            messagebox.showerror("Error", f"Serial communication error: {str(e)}")
            return False

    def run_race(self, driver, laps, early_start, count_first):
        try:
            self.countdown_label.config(text="")
            lap_times = []
            lap_count = 0

            while lap_count < laps:
                lap_start = time.time()
                lap_end = record_lap_time(self.serial_port, count_first)
                lap_time = lap_end - lap_start
                if lap_count == 0 and early_start:
                    lap_time += self.early_start_penalty
                lap_times.append(lap_time)
                lap_count += 1

            best_lap = min(lap_times)
            last_lap = lap_times[-1]

            # Update existing driver or append new entry
            driver_found = False
            for result in self.results:
                if result['driver'] == driver:
                    result['last_time'] = last_lap
                    result['best_time'] = min(result['best_time'], best_lap)
                    driver_found = True
                    break

            if not driver_found:
                self.results.append({'driver': driver, 'last_time': last_lap, 'best_time': best_lap})

            save_data('results.json', self.results)
            self.update_results_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run race: {str(e)}")


    def get_number_of_laps(self):
        try:
            laps = int(self.laps_entry.get())
            if laps > 0:
                return laps
            else:
                messagebox.showerror("Error", "Number of laps must be greater than zero.")
                return None
        except ValueError:
            messagebox.showerror("Error", "Invalid number of laps. Please enter an integer.")
            return None

    def update_results_table(self):
        try:
            self.results_table.delete(*self.results_table.get_children())
            sorted_results = sorted([result for result in self.results if 'best_time' in result], key=lambda x: x['best_time'])
            for result in sorted_results:
                self.results_table.insert("", tk.END, values=(result['driver'], f"{result['last_time']:.3f}", f"{result['best_time']:.3f}"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update results table: {str(e)}")

    def show_results(self):
        results_window = tk.Toplevel(self.root)
        results_window.title("Race Results")

        results_window.attributes('-fullscreen', True)  # Enable fullscreen

        results_frame = tk.Frame(results_window, bg='#f0f0f0')
        results_frame.pack(fill=tk.BOTH, expand=True)

        results_table = ttk.Treeview(results_frame, columns=("Driver", "Last Lap", "Best Lap"), show='headings', style="Custom.TreeviewLarge")
        results_table.heading("Driver", text="Driver")
        results_table.heading("Last Lap", text="Last Lap (s)")
        results_table.heading("Best Lap", text="Best Lap (s)")
        results_table.column("Driver", anchor=tk.CENTER, width=200)
        results_table.column("Last Lap", anchor=tk.CENTER, width=200)
        results_table.column("Best Lap", anchor=tk.CENTER, width=200)
        results_table.pack(fill=tk.BOTH, expand=True)

        close_button = tk.Button(results_window, text="Close", command=results_window.destroy, bg='#dc3545', fg='white', relief='raised', bd=2)
        close_button.pack(pady=10)

        sorted_results = sorted([result for result in self.results if 'best_time' in result], key=lambda x: x['best_time'])
        for result in sorted_results:
            results_table.insert("", tk.END, values=(result['driver'], f"{result['last_time']:.3f}", f"{result['best_time']:.3f}"))

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Custom.Treeview", font=("Helvetica", 14), rowheight=30)
    style.configure("Custom.Treeview.Heading", font=("Helvetica", 16, "bold"))
    style.configure("Custom.TreeviewLarge", font=("Helvetica", 20), rowheight=40)
    style.configure("Custom.TreeviewLarge.Heading", font=("Helvetica", 24, "bold"))
    app = SlotCarManager(root)
    root.mainloop()
