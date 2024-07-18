import threading
import tkinter as tk
import gui
import leaderboard

def open_leaderboard():
    leaderboard_root = tk.Tk()
    leaderboard_app = leaderboard.LeaderboardApp(leaderboard_root)
    leaderboard_root.mainloop()

if __name__ == "__main__":
    threading.Thread(target=open_leaderboard).start()
    
    gui_root = tk.Tk()
    app = gui.SlotCarManager(gui_root)
    gui_root.mainloop()
