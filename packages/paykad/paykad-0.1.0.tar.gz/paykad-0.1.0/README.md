# Paykad (Pey-kad) GUI Library

**Paykad** (derived from the Persian word *Pi-kaad*, meaning **planning and blueprint**) is a Python library designed for **fast, readable, and modern Graphical User Interface (GUI) development**. It functions as a **lightweight, object-oriented abstraction layer** over Python's standard **Tkinter** library, simplifying the process of building desktop applications with a clean and intuitive syntax.

---

## 1. Installation and Prerequisites

### 1.1. Installation

Paykad is easily installed via **PyPI**:

```bash
pip install paykad
2. Usage Guide

A Paykad application consistently follows four simple steps: Define Events, Create Elements, Layout, and Run.

2.1. Complete Code Example

Save the following code as app.py:
Python

from paykad import Window, Label, Button

# [1. Event Definition Section]
def handle_button_click():
    """Event Handler: The function executed when the button is clicked."""
    # Dynamically update the Label's text using Paykad's custom method
    my_label.set_text("Thank you for the click! Paykad is active.")

# [2. Element Creation Section]
# Create the main Window (Root container)
app_window = Window(title="Paykad Demonstration", size="450x200")

# Create a Label widget
# The first argument (app_window) is the Parent/Master widget.
my_label = Label(app_window, text="Click the button below to see a change.")

# Create a Button widget
# The 'command' argument links the button to our event handler function.
click_button = Button(app_window, text="Click Here", command=handle_button_click)

# [3. Layout Section]
# Use the pack() method for widget placement. 
# Paykad uses a simplified Grid layout system.
my_label.pack(row=0, column=0, pady=20) 
click_button.pack(row=1, column=0, pady=10) 

# [4. Execution Section]
if __name__ == "__main__":
    # run_loop() starts the main event loop, making the application interactive.
    app_window.run_loop() 

3. Core API Reference

3.1. The Window Class

Method/Argument	Type	Full Description
Window(title, size)	Constructor	The Application Base: Creates the main root window. All other widgets must be attached to this object.
title	String	The text displayed in the window's title bar.
size	String	The initial dimensions of the window (e.g., "800x600").
run_loop()	Main Method	The Event Loop: Starts the GUI application. The program remains active, listening for user input until this loop is terminated.

3.2. The Label Class

Method/Argument	Type	Full Description
Label(master, text)	Constructor	A widget used to display static or dynamic text information to the user.
master	Widget Object	The parent widget (usually the Window) this Label resides within.
text	String	The initial text content displayed by the Label.
set_text(new_text)	Custom Method	Dynamic Update: Changes the text displayed by the Label while the application is running (abstracts away Tkinter's StringVar).

3.3. The Button Class

Method/Argument	Type	Full Description
Button(master, text, command)	Constructor	A clickable widget used to trigger an action or function.
text	String	The text displayed on the button face.
command	Function	The function to be executed immediately upon a mouse click. The function reference must be passed without parentheses.

3.4. The pack() Layout Method (Available on All Widgets)

The pack() method manages the placement of widgets within their parent container. Paykad uses a simplified Grid layout system:
Argument	Type	Full Description
pack()	Layout Method	All widgets inherit this method to be placed within the container's grid layout.
row	Integer	The row number in the grid where the widget should be placed (starts at 0).
column	Integer	The column number in the grid where the widget should be placed (starts at 0).
padx	Integer	Padding X: The amount of horizontal padding (left and right margin) in pixels around the widget.
pady	Integer	Padding Y: The amount of vertical padding (top and bottom margin) in pixels around the widget.