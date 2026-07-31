"""Turtle Shape Maker - draw shapes for turtle."""

import tkinter as tk

APP_NAME = "Turtle Shape Maker"

# Settings

# grid goes from -GRID_RANGE to GRID_RANGE
GRID_RANGE = 20
CELL = 12  # pixels between grid points
MARGIN = 28  # pixels around the grid for the axis numbers
CANVAS_SIZE = 2 * (MARGIN + GRID_RANGE * CELL)
CENTRE = CANVAS_SIZE // 2  # pixel position of (0, 0)


# Grid maths: grid points <-> canvas pixels

def in_grid(point):
    x, y = point
    return abs(x) <= GRID_RANGE and abs(y) <= GRID_RANGE


def point_to_pixel(point):
    x, y = point
    # canvas y goes down but turtle y goes up, so flip it
    return CENTRE + x * CELL, CENTRE - y * CELL


def pixel_to_point(px, py):
    # reverse of point_to_pixel, rounded to nearest grid point
    return round((px - CENTRE) / CELL), round((CENTRE - py) / CELL)


# The window

class ShapeMakerApp:
    """The main window."""

    def __init__(self, root):
        self.root = root
        self.mouse_position = tk.StringVar()

        root.title(APP_NAME)
        root.resizable(False, False)  # the grid has a fixed size

        self.build_window()
        self.draw_grid()
        self.canvas.bind("<Motion>", self.mouse_moved)
        self.canvas.bind("<Leave>", self.mouse_left)

    def build_window(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_SIZE,
                                height=CANVAS_SIZE, background="white",
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(padx=12, pady=(12, 0))
        tk.Label(self.root, textvariable=self.mouse_position).pack(
            anchor="e", padx=12, pady=(6, 12))

    def draw_grid(self):
        far = CANVAS_SIZE - MARGIN
        for value in range(-GRID_RANGE, GRID_RANGE + 1):
            # Every 5th line is darker and numbered, and the axes are
            # darker again.
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
            if value % 5 == 0:
                # Numbers along the bottom (x) and the left side (y).
                self.canvas.create_text(x, far + 4, text=str(value),
                                        anchor="n", fill="#888888",
                                        font="TkSmallCaptionFont")
                self.canvas.create_text(MARGIN - 4, y, text=str(value),
                                        anchor="e", fill="#888888",
                                        font="TkSmallCaptionFont")

    def mouse_moved(self, event):
        # Show the grid point under the mouse in the corner.
        point = pixel_to_point(event.x, event.y)
        if in_grid(point):
            self.mouse_position.set(f"x {point[0]}, y {point[1]}")
        else:
            self.mouse_position.set("")

    def mouse_left(self, event):
        self.mouse_position.set("")


def main():
    root = tk.Tk()
    ShapeMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
