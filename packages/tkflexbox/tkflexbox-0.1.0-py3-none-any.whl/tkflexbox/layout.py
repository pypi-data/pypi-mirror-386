import tkinter as tk
from tkinter import ttk

def StrictGridFrame(parent, column=0, row=0, columnspan=1, rowspan=1):
    frame = tk.Frame(parent)
    frame.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky="nsew")
    frame.grid_propagate(False)
    return frame

def FullPageGrid(parent, rows=10, columns=10):
    parent.grid(column=0, row=0, sticky="nsew")
    for i in range(rows):
        parent.grid_rowconfigure(i, weight=1, uniform="grid")
    for i in range(columns):
        parent.grid_columnconfigure(i, weight=1, uniform="grid")

class FlexBoxFrame(tk.Frame):
    def __init__(self, parent, rows=10, columns=10):
        super().__init__(parent)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)


        self.grid(column=0, row=0, sticky="nsew")
        for i in range(rows):
            self.grid_rowconfigure(i, weight=1, uniform="grid")
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1, uniform="grid")

    def StrictGridFrame(self, column=0, row=0, columnspan=1, rowspan=1):
        frame = tk.Frame(self)
        frame.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky="nsew")
        frame.grid_propagate(False)
        return frame
    
    def place_widget(self, widget, row, column, rowspan=1, columnspan=1, relx=0, rely=0, relwidth=1, relheight=1, **kwargs):
        strictbox = self.StrictGridFrame(column=column, row=row, columnspan=columnspan, rowspan=rowspan)
        placed_widget = widget(strictbox, **kwargs)
        placed_widget.place(relx=0, rely=0, relwidth=1, relheight=1)
        return placed_widget
