import tkinter as tk
from tkinter import filedialog, messagebox
import os
from simba.sandbox.maplight.execute import Execute

def browse_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        dir_var.set(folder_selected)

def run_action():
    folder = dir_var.get()
    if not os.path.isdir(folder):
        messagebox.showwarning("Warning", "Please select a valid directory!")
        return
    executor = Execute(video_dir=folder)
    executor.run()

root = tk.Tk()
root.title("CLASSIFICATION APP")
root.geometry("400x150")
root.resizable(False, False)
dir_var = tk.StringVar()
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill="both", expand=True)

browse_btn = tk.Button(frame, text="BROWSE VIDEO DIRECTORY", command=browse_directory)
browse_btn.pack(pady=(0, 5))

dir_label = tk.Label(frame, textvariable=dir_var, bg="#f0f0f0", anchor="w", relief="sunken", width=50)
dir_label.pack(pady=(0, 10))

run_btn = tk.Button(frame, text="RUN", command=run_action)
run_btn.pack()

root.mainloop()