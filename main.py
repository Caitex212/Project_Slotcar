import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import serial
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

from data_manager import load_data, save_data
from serial_communication import record_lap_time

class SlotCarManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Slot Car Rally Manager")

        self.drivers = load_data('drivers.json', 1)
        self.results = load_data('results.json', 1)
        settings = load_data('settings.json', 0)
        self.serial_port = settings.get('serial_port', 'COM3')
        self.early_start_penalty = settings.get('early_start_penalty', 2)
        self.results_table2 = None
        self.results_window = None
        self.overlay_label = None

        self.create_widgets()
        pygame.mixer.init()

        self.save_settings()

    def save_settings(self):
        settings = {
            'serial_port': self.serial_port,
            'early_start_penalty': self.early_start_penalty
        }
        save_data('settings.json', settings)

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

        self.results_table = ttk.Treeview(frame, columns=("Rank", "Driver", "Last Lap", "Best Lap"), show='headings', style="Custom.Treeview")
        self.results_table.heading("Rank", text="Pos")
        self.results_table.heading("Driver", text="Driver")
        self.results_table.heading("Last Lap", text="Last Lap (s)")
        self.results_table.heading("Best Lap", text="Best Lap (s)")
        self.results_table.column("Rank", anchor=tk.CENTER, width=50)
        self.results_table.column("Driver", anchor=tk.CENTER, width=250)
        self.results_table.column("Last Lap", anchor=tk.CENTER, width=150)
        self.results_table.column("Best Lap", anchor=tk.CENTER, width=150)
        self.results_table.grid(row=7, column=0, columnspan=4, pady=10, sticky="nsew")
        self.update_results_table()

    def set_serial_port(self):
        try:
            self.serial_port = self.port_entry.get()
            self.save_settings()
            messagebox.showinfo("Serial Port Set", f"Serial port set to {self.serial_port}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set serial port: {str(e)}")

    def set_early_start_penalty(self):
        try:
            self.early_start_penalty = int(self.penalty_entry.get())
            self.save_settings()
            messagebox.showinfo("Penalty Set", f"Early start penalty set to {self.early_start_penalty} seconds")
        except ValueError:
            messagebox.showerror("Error", "Invalid penalty value. Please enter an integer.")

    def add_driver(self):
        try:
            driver_name = self.driver_entry.get()
            if driver_name:
                self.drivers.append(driver_name)
                save_data('drivers.json', self.drivers)
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
                confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove {driver_name}?")
                if confirm:
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
        
    def show_overlay(self, text):
        if self.overlay_label:
            self.overlay_label.destroy()
        if self.results_table2:
            self.overlay_label = tk.Label(self.results_table2, text=text, font=("Helvetica", 128, "bold"))
            self.overlay_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def hide_overlay(self):
        if self.overlay_label:
            self.overlay_label.destroy()
            self.overlay_label = None
        
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
            sound_file = f"_internal/sounds/{second}.wav" #remove _internal if you want to execute from source
            pygame.mixer.Sound(sound_file).play()
        except Exception as e:
            print(f"Failed to play countdown sound: {str(e)}")

    def countdown(self, seconds, driver, laps):
        try:
            with serial.Serial(self.serial_port, 9600, timeout=1) as ser:
                next = seconds
                counter = 0
                for second in range((seconds + 1) * 100, 0, -1):
                    time.sleep(0.01)
                    check_early = False
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        if line == '1':
                            check_early = True
                    if check_early:
                        ser.close()
                        self.show_overlay("Early Start!")
                        self.countdown_label.config(text="Early Start!")
                        self.play_countdown_sound("GO")
                        self.run_race(driver, laps, True, True)
                        return
                    counter = counter + 1
                    if counter >= 100:
                        counter = 0
                        self.show_overlay(f"{next}")
                        self.countdown_label.config(text=f"Stage starts in: {next}")
                        self.play_countdown_sound(next)
                        next = next - 1
                self.show_overlay("Go!")
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
                self.hide_overlay()

            best_lap = min(lap_times)
            last_lap = lap_times[-1]

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

    def update_results_table(self):
        try:
            self.results_table.delete(*self.results_table.get_children())
            sorted_results = sorted([result for result in self.results if 'best_time' in result], key=lambda x: x['best_time'])
            for index, result in enumerate(sorted_results, start=1):
                self.results_table.insert("", tk.END, values=(index, result['driver'], f"{result['last_time']:.3f}", f"{result['best_time']:.3f}"), tags=('oddrow' if index % 2 == 0 else 'evenrow'))
                self.results_table.tag_configure('oddrow', background='white')
                self.results_table.tag_configure('evenrow', background='#f0f0f0')
            if self.results_table2:
                self.results_table2.delete(*self.results_table2.get_children())
                sorted_results2 = sorted([result for result in self.results if 'best_time' in result], key=lambda x: x['best_time'])
                for index, result in enumerate(sorted_results2, start=1):
                    self.results_table2.insert("", tk.END, values=(index, result['driver'], f"{result['last_time']:.3f}", f"{result['best_time']:.3f}"), tags=('oddrow' if index % 2 == 0 else 'evenrow'))
                    self.results_table2.tag_configure('oddrow', background='white')
                    self.results_table2.tag_configure('evenrow', background='#f0f0f0')
            self.dump_leaderboard_to_excel()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update results table: {str(e)}")

    def dump_leaderboard_to_excel(self):
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Leaderboard"

            headers = ["Rank", "Driver", "Last Lap (s)", "Best Lap (s)"]
            ws.append(headers)

            for col in ws.iter_cols(min_col=1, max_col=4, min_row=1, max_row=1):
                for cell in col:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center")
                    cell.border = Border(
                        left=Side(border_style="thin"),
                        right=Side(border_style="thin"),
                        top=Side(border_style="thin"),
                        bottom=Side(border_style="thin")
                    )
                    ws.column_dimensions[cell.column_letter].width = 20
                ws.column_dimensions["A"].width = 10
                ws.column_dimensions["B"].width = 40

            sorted_results = sorted([result for result in self.results if 'best_time' in result], key=lambda x: x['best_time'])

            for index, result in enumerate(sorted_results, start=1):
                row_data = [index, result['driver'], f"{result['last_time']:.3f}", f"{result['best_time']:.3f}"]
                row_index = ws.max_row + 1
                ws.append(row_data)

                for col_index, cell_value in enumerate(row_data, start=1):
                    cell = ws.cell(row=row_index, column=col_index)
                    cell.alignment = Alignment(horizontal="center")
                    cell.border = Border(
                        left=Side(border_style="thin"),
                        right=Side(border_style="thin"),
                        top=Side(border_style="thin"),
                        bottom=Side(border_style="thin")
                    )

                    if index % 2 == 0:
                        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

            wb.save("leaderboard.xlsx")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to dump leaderboard to Excel: {str(e)}")

    def show_results(self):
        try:
            if self.results_window:
                self.results_window.destroy()
                self.results_table2.destroy()
            self.results_window = tk.Toplevel(self.root)
            self.results_window.title("Race Results")

            results_frame = tk.Frame(self.results_window, bg='#f0f0f0')
            results_frame.pack(fill=tk.BOTH, expand=True)

            results_frame.grid_rowconfigure(0, weight=1)
            results_frame.grid_columnconfigure(0, weight=1)

            self.results_table2 = ttk.Treeview(results_frame, columns=("Rank", "Driver", "Last Lap", "Best Lap"), show='headings', style="Custom.Treeview")
            self.results_table2.heading("Rank", text="Pos")
            self.results_table2.heading("Driver", text="Driver")
            self.results_table2.heading("Last Lap", text="Last Lap (s)")
            self.results_table2.heading("Best Lap", text="Best Lap (s)")
            self.results_table2.column("Rank", anchor=tk.CENTER, width=50)
            self.results_table2.column("Driver", anchor=tk.CENTER, width=250)
            self.results_table2.column("Last Lap", anchor=tk.CENTER, width=150)
            self.results_table2.column("Best Lap", anchor=tk.CENTER, width=150)
            self.results_table2.grid(row=0, column=0, sticky="nsew")

            fullscreen_button = tk.Button(self.results_window, text="Toggle Fullscreen", command=lambda: self.toggle_fullscreen(self.results_window))
            fullscreen_button.pack(pady=10)
            self.update_results_table()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show results: {str(e)}")

    def toggle_fullscreen(self, window):
        state = not window.attributes('-fullscreen')
        window.attributes('-fullscreen', state)

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Custom.Treeview", font=("Helvetica", 14), rowheight=30)
    style.configure("Custom.Treeview.Heading", font=("Helvetica", 16, "bold"))
    style.configure("Custom.TreeviewLarge", font=("Helvetica", 20), rowheight=40)
    style.configure("Custom.TreeviewLarge.Heading", font=("Helvetica", 24, "bold"))
    app = SlotCarManager(root)
    root.mainloop()