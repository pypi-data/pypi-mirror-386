# paykad/widgets.py

import tkinter as tk
from tkinter import ttk

# --- کلاس پایه برای تمام ویجت‌های Paykad ---
class BaseWidget:
    def __init__(self, master, tk_widget_class, **kwargs):
        # ذخیره مرجع به ویجت Tkinter
        self.tk_widget = tk_widget_class(master.tk_root if isinstance(master, Window) else master.tk_widget, **kwargs)
        
    def pack(self, row, column, padx=5, pady=5):
        """متد چیدمان Grid ساده."""
        self.tk_widget.grid(row=row, column=column, padx=padx, pady=pady, sticky="w")

# --- Window (پنجره اصلی) ---
class Window:
    def __init__(self, title="Paykad App", size="400x300"):
        self.tk_root = tk.Tk()
        self.tk_root.title(title)
        self.tk_root.geometry(size)

    def run_loop(self):
        """شروع حلقه رویداد GUI."""
        self.tk_root.mainloop()

# --- Label (برچسب متنی) ---
class Label(BaseWidget):
    def __init__(self, master, text=""):
        super().__init__(master, ttk.Label, text=text)
        self.text_var = tk.StringVar(value=text)
        self.tk_widget.config(textvariable=self.text_var)

    def set_text(self, new_text):
        """متد سفارشی برای تغییر متن."""
        self.text_var.set(new_text)

# --- Button (دکمه) ---
class Button(BaseWidget):
    def __init__(self, master, text="Click", command=None):
        # command: تابعی که هنگام کلیک اجرا می‌شود
        super().__init__(master, ttk.Button, text=text, command=command)