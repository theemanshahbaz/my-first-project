import tkinter as tk
from tkinter import messagebox
import json
import os

# Credentials file
CREDENTIALS_FILE = "data/credentials.json"
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.isfile(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE,"w") as f:
        json.dump({"admin":"admin123"}, f)

def authenticate(username, password):
    with open(CREDENTIALS_FILE,"r") as f:
        creds = json.load(f)
    return creds.get(username) == password

def show_login(root, on_success):
    login_win = tk.Toplevel(root)
    login_win.title("Librarian Login")
    login_win.geometry("400x250")
    login_win.configure(bg="#121212")

    tk.Label(login_win, text="Username:", fg="#00fff5", bg="#121212").pack(pady=10)
    user_entry = tk.Entry(login_win)
    user_entry.pack(pady=5)
    tk.Label(login_win, text="Password:", fg="#00fff5", bg="#121212").pack(pady=10)
    pass_entry = tk.Entry(login_win, show="*")
    pass_entry.pack(pady=5)

    def login_action():
        user = user_entry.get().strip()
        pwd = pass_entry.get().strip()
        if authenticate(user, pwd):
            messagebox.showinfo("Login Success","Welcome Librarian!")
            login_win.destroy()
            on_success()
        else:
            messagebox.showerror("Login Failed","Invalid Username/Password")

    tk.Button(login_win, text="Login", command=login_action, bg="#00d2ff", fg="#121212", width=15).pack(pady=20)
    login_win.grab_set()
    root.wait_window(login_win)
