import tkinter as tk
from tkinter import PhotoImage, NW
import customtkinter as ctk
import cv2

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Selector")
        self.camera_index = None
        self.cap = None

        self.create_widgets()
        self.list_cameras()

    def create_widgets(self):
        self.label = ctk.CTkLabel(self.root, text="Select a Camera")
        self.label.pack(pady=10)

        self.radio_var = tk.IntVar()
        self.radio_var.set(-1)  # No camera selected initially

        self.radio_frame = ctk.CTkFrame(self.root)
        self.radio_frame.pack(pady=10)

        self.select_button = ctk.CTkButton(self.root, text="Select", command=self.select_camera)
        self.select_button.pack(pady=10)

    def list_cameras(self):
        self.cameras = self.get_available_cameras()
        if not self.cameras:
            ctk.CTkMessagebox.show_error("Error", "No cameras available.")
            self.root.destroy()
        else:
            for i, cam in enumerate(self.cameras):
                radio_button = ctk.CTkRadioButton(self.radio_frame, text=cam, variable=self.radio_var, value=i)
                radio_button.pack(anchor='w')

    def get_available_cameras(self):
        available_cameras = []
        for i in range(10):  # Check first 10 indexes.
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(f"Camera {i}")
                cap.release()
        return available_cameras

    def select_camera(self):
        selection = self.radio_var.get()
        if selection != -1:
            self.camera_index = selection
            self.show_camera_feed()

    def show_camera_feed(self):
        self.clear_window()
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            ctk.CTkMessagebox.show_error("Error", f"Cannot open camera {self.camera_index}.")
            self.root.destroy()
            return

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.update_frame()

    def photo_image(self, img):
        h, w = img.shape[:2]
        data = f'P6 {w} {h} 255 '.encode() + img[..., ::-1].tobytes()
        return PhotoImage(width=w, height=h, data=data, format='PPM')

    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, img = self.cap.read()
            if ret:
                photo = self.photo_image(img)
                self.canvas.create_image(0, 0, image=photo, anchor=NW)
                self.canvas.image = photo
            else:
                print("Failed to capture frame")
        else:
            print("Camera is not opened or not available")

        self.root.after(30, self.update_frame)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_closing(self):
        if self.cap:
            self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

    root = ctk.CTk()
    app = CameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
