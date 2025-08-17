import tkinter as tk
from tkinter import ttk, scrolledtext
from heybuddy.state_machine import AppState

class LEDIndicator(tk.Canvas):
    def __init__(self, parent, size=20):
        super().__init__(parent, width=size, height=size, highlightthickness=0)
        self.size = size
        self.create_oval(2, 2, size-2, size-2, fill='gray', tags='led')
        
    def set_color(self, color):
        self.itemconfig('led', fill=color)
        
    def update_for_state(self, state):
        colors = {
            AppState.IDLE: 'gray',
            AppState.RECORDING: 'red',
            AppState.THINKING: 'yellow',
            AppState.SPEAKING: 'blue',
            AppState.OFFLINE: 'orange'
        }
        self.set_color(colors.get(state, 'gray'))

class TranscriptPanel(scrolledtext.ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=4, wrap=tk.WORD, state=tk.DISABLED, **kwargs)
        
    def set_text(self, text):
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.insert(tk.END, f"You said: {text}")
        self.config(state=tk.DISABLED)
        self.see(tk.END)
        
    def clear(self):
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.config(state=tk.DISABLED)

class ResponsePanel(scrolledtext.ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=6, wrap=tk.WORD, state=tk.DISABLED, **kwargs)
        
    def set_text(self, text):
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.insert(tk.END, f"heyBuddy: {text}")
        self.config(state=tk.DISABLED)
        self.see(tk.END)
        
    def clear(self):
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.config(state=tk.DISABLED)

class TalkButton(tk.Button):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            text="Hold to Talk",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="raised",
            bd=3,
            **kwargs
        )
        
    def set_pressed(self, pressed):
        if pressed:
            self.config(relief="sunken", bg="#45a049")
        else:
            self.config(relief="raised", bg="#4CAF50")

class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, relief=tk.SUNKEN, bd=1)
        
        self.online_label = tk.Label(self, text="Offline", fg="red")
        self.online_label.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(self, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
    def set_online_status(self, online):
        if online:
            self.online_label.config(text="Online", fg="green")
        else:
            self.online_label.config(text="Offline", fg="red")
            
    def set_status(self, status):
        self.status_label.config(text=status)