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

MIN_POINTS = 3
HIGHLIGHT = "#1e90ff"  # unfinished part and mouse marker


# Drawing logic

class ShapeError(Exception):
    """Error with a message to show the user."""


def in_grid(point):
    x, y = point
    return abs(x) <= GRID_RANGE and abs(y) <= GRID_RANGE


class Drawing:
    """Holds the finished parts and the part being drawn."""

    def __init__(self):
        self.parts = []  # finished parts, each a tuple of (x, y) points
        self.current = []  # (x, y) points of the unfinished part

    def is_start(self, point):
        return len(self.current) > 0 and point == self.current[0]

    def add_point(self, point):
        if not in_grid(point):
            raise ShapeError("Click inside the grid.")
        if point in self.current:
            raise ShapeError("That point is already in this part.")
        self.current.append(point)

    def finish_part(self):
        points = self.current
        if not points:
            raise ShapeError("Click the grid to start a part first.")
        if len(points) < MIN_POINTS:
            raise ShapeError(f"A part needs at least {MIN_POINTS} points.")
        self.parts.append(tuple(points))
        self.current = []


# Grid maths: grid points <-> canvas pixels

def point_to_pixel(point):
    x, y = point
    # canvas y goes down but turtle y goes up, so flip it
    return CENTRE + x * CELL, CENTRE - y * CELL


def pixel_to_point(px, py):
    # reverse of point_to_pixel, rounded to nearest grid point
    return round((px - CENTRE) / CELL), round((CENTRE - py) / CELL)


def to_pixels(points):
    # tkinter wants one flat list: [x1, y1, x2, y2, ...].
    pixels = []
    for point in points:
        pixels.extend(point_to_pixel(point))
    return pixels


# The window

class ShapeMakerApp:
    """The main window: the grid and a status line."""

    def __init__(self, root):
        self.root = root
        self.drawing = Drawing()
        self.message = tk.StringVar()
        self.mouse_position = tk.StringVar()

        root.title(APP_NAME)
        root.resizable(False, False)  # the grid has a fixed size

        self.build_window()
        self.draw_grid()
        self.bind_events()
        self.say("Click a grid point to start drawing a part.")

    def build_window(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_SIZE,
                                height=CANVAS_SIZE, background="white",
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(padx=12, pady=(12, 0))

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=12, pady=(6, 12))
        self.message_label = tk.Label(bottom, textvariable=self.message)
        self.message_label.pack(side="left")
        tk.Label(bottom, textvariable=self.mouse_position).pack(side="right")

    def draw_grid(self):
        # light lines first so the darker ones end up on top
        for value in range(-GRID_RANGE, GRID_RANGE + 1):
            if value % 5 != 0:
                self.draw_grid_lines(value, "#ececec")
        for value in range(-GRID_RANGE, GRID_RANGE + 1, 5):
            self.draw_grid_lines(value, "#cccccc")
            # Numbers along the bottom (x) and the left side (y).
            x, y = point_to_pixel((value, value))
            self.canvas.create_text(x, CANVAS_SIZE - MARGIN + 4,
                                    text=str(value), anchor="n",
                                    fill="#888888", font="TkSmallCaptionFont")
            self.canvas.create_text(MARGIN - 4, y, text=str(value),
                                    anchor="e", fill="#888888",
                                    font="TkSmallCaptionFont")
        self.draw_grid_lines(0, "#888888")

    def draw_grid_lines(self, value, colour):
        # vertical and horizontal line
        x, y = point_to_pixel((value, value))
        far = CANVAS_SIZE - MARGIN
        self.canvas.create_line(x, MARGIN, x, far, fill=colour)
        self.canvas.create_line(MARGIN, y, far, y, fill=colour)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.canvas_clicked)
        self.canvas.bind("<Motion>", self.mouse_moved)
        self.canvas.bind("<Leave>", self.mouse_left)
        self.root.bind("<Return>", lambda event: self.finish_part())

    def say(self, text, problem=False):
        # red for problems
        self.message.set(text)
        if problem:
            self.message_label.config(fg="#c0392b")
        else:
            self.message_label.config(fg="black")

    def redraw(self):
        # only delete "shapes" so the grid stays
        self.canvas.delete("shapes")
        # TODO: let the user pick the colours
        for points in self.drawing.parts:
            self.canvas.create_polygon(to_pixels(points), fill="green",
                                       outline="black", width=2,
                                       tags="shapes")
        self.draw_unfinished_part()

    def draw_unfinished_part(self):
        points = self.drawing.current
        if len(points) >= 2:
            self.canvas.create_line(to_pixels(points), fill=HIGHLIGHT,
                                    width=2, tags="shapes")
        # first point is bigger and hollow so you can click it again
        for index, point in enumerate(points):
            x, y = point_to_pixel(point)
            if index == 0:
                radius, fill = 6, "white"
            else:
                radius, fill = 3, HIGHLIGHT
            self.canvas.create_oval(x - radius, y - radius,
                                    x + radius, y + radius, fill=fill,
                                    outline=HIGHLIGHT, width=2,
                                    tags="shapes")

    def canvas_clicked(self, event):
        point = pixel_to_point(event.x, event.y)
        # Clicking the first point again finishes the part.
        if self.drawing.is_start(point):
            self.finish_part()
            return

        try:
            self.drawing.add_point(point)
        except ShapeError as problem:
            self.say(str(problem), problem=True)
        else:
            # only runs if it worked
            self.say(f"Point {len(self.drawing.current)} added at {point}.")
        self.redraw()

    def mouse_moved(self, event):
        # ring on the nearest grid point, and show the coords
        self.canvas.delete("marker")
        point = pixel_to_point(event.x, event.y)
        if not in_grid(point):
            self.mouse_position.set("")
            return
        x, y = point_to_pixel(point)
        self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                                outline=HIGHLIGHT, width=2, tags="marker")
        self.mouse_position.set(f"x {point[0]}, y {point[1]}")

    def mouse_left(self, event):
        self.canvas.delete("marker")
        self.mouse_position.set("")

    def finish_part(self):
        try:
            self.drawing.finish_part()
        except ShapeError as problem:
            self.say(str(problem), problem=True)
            return
        self.say(f"Part {len(self.drawing.parts)} finished.")
        self.redraw()


def main():
    root = tk.Tk()
    ShapeMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
