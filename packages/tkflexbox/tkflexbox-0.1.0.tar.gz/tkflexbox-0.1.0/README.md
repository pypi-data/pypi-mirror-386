# tkflexbox

A python library to implement flexbox like functionality to tkinter.


## install
```bash
pip install tkflexbox
```

## example usage
```bash
import tkflexbox
from tkflexbox import FlexBoxFrame
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.geometry('800x800')
page = FlexBoxFrame(root, rows=5, columns=5)
page.place_widget(ttk.Button, row=1, column=2, columnspan=2, text='Hello world')

root.mainloop()

```
