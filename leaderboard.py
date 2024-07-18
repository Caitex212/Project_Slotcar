import tkinter as tk
from tkinter import ttk
from data_manager import load_data

class LeaderboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Leaderboard")
        
        self.create_widgets()
        self.update_leaderboard()

    def create_widgets(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.fullscreen_button = tk.Button(self.frame, text="Toggle Fullscreen", command=self.toggle_fullscreen)
        self.fullscreen_button.pack(pady=5)

        self.leaderboard_table = ttk.Treeview(self.frame, columns=("Driver", "Last Lap", "Best Lap"), show='headings')
        self.leaderboard_table.heading("Driver", text="Driver")
        self.leaderboard_table.heading("Last Lap", text="Last Lap (s)")
        self.leaderboard_table.heading("Best Lap", text="Best Lap (s)")
        self.leaderboard_table.pack(fill=tk.BOTH, expand=True)

    def toggle_fullscreen(self):
        is_fullscreen = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_fullscreen)

        if not is_fullscreen:
            self.leaderboard_table.tag_configure('larger', font=('Helvetica', 20))
        else:
            self.leaderboard_table.tag_configure('larger', font=('Helvetica', 10))

        self.update_leaderboard()

    def update_leaderboard(self):
        for row in self.leaderboard_table.get_children():
            self.leaderboard_table.delete(row)

        results = load_data('results.json')
        sorted_results = sorted(
            [result for result in results if 'best_time' in result], 
            key=lambda x: x['best_time']
        )
        
        for result in sorted_results:
            self.leaderboard_table.insert("", tk.END, values=(
                result['driver'], f"{result['last_time']:.3f}", f"{result['best_time']:.3f}"
            ))

        self.root.after(2000, self.update_leaderboard)  # Update every 2 seconds

if __name__ == "__main__":
    root = tk.Tk()
    app = LeaderboardApp(root)
    root.mainloop()
