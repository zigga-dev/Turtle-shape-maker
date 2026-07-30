"""Turtle Shape Maker - draw shapes for turtle."""

import tkinter as tk

APP_NAME = "Turtle Shape Maker"

# Settings

# grid goes from -GRID_RANGE to GRID_RANGE
GRID_RANGE = 20
CELL = 12  # pixels between grid points
MARGIN = 28  # pixels around the grid
CANVAS_SIZE = 2 * (MARGIN + GRID_RANGE * CELL)
CENTRE = CANVAS_SIZE // 2  # pixel position of (0, 0)


# Grid maths

def point_to_pixel(point):
    x, y = point
    # canvas y goes down but turtle y goes up, so flip it
    return CENTRE + x * CELL, CENTRE - y * CELL


# The window

class ShapeMakerApp:
    """The main window."""

    def __init__(self, root):
        self.root = root

        root.title(APP_NAME)
        root.resizable(False, False)  # the grid has a fixed size

        self.build_window()
        self.draw_grid()

    def build_window(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_SIZE,
                                height=CANVAS_SIZE, background="white",
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(padx=12, pady=12)

    def draw_grid(self):
        far = CANVAS_SIZE - MARGIN
        for value in range(-GRID_RANGE, GRID_RANGE + 1):
            # Every 5th line is darker, and the axes are darker again.
            if value == 0:
                colour = "#888888"
            elif value % 5 == 0:
                colour = "#cccccc"
            else:
                colour = "#ececec"
            # vertical and horizontal line
            x, y = point_to_pixel((value, value))
            self.canvas.create_line(x, MARGIN, x, far, fill=colour)
            self.canvas.create_line(MARGIN, y, far, y, fill=colour)


def main():
    root = tk.Tk()
    ShapeMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
