"""Turtle Shape Maker: draw custom shapes for Python's turtle module."""

import json
import math
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Turtle Shape Maker"

# Settings

# Points can go from -GRID_RANGE to GRID_RANGE on each axis.
GRID_RANGE = 20
CELL = 12  # pixels between grid points
MARGIN = 28  # pixels around the grid for the axis numbers
NUMBER_EVERY = 5  # every 5th grid line is darker and numbered
CANVAS_SIZE = 2 * (MARGIN + GRID_RANGE * CELL)
CENTRE = CANVAS_SIZE // 2  # pixel position of (0, 0)
GRID_LOW = MARGIN  # pixel position of the grid's top and left edges
GRID_HIGH = CANVAS_SIZE - MARGIN  # pixel position of its bottom and right

# Drawing rules.
MIN_POINTS = 3
MAX_POINTS = 40
MAX_PARTS = 12
MAX_NAME_LENGTH = 20
DEFAULT_NAME = "my_shape"

# Colour names that tkinter and turtle both accept.
COLOURS = ("black", "grey", "white", "brown", "red", "orange",
           "yellow", "green", "cyan", "blue", "purple", "pink")
START_FILL = "green"
START_OUTLINE = "black"

# Window appearance.
CANVAS_BACKGROUND = "white"
MINOR_LINE = "#ececec"
MAJOR_LINE = "#cccccc"
AXIS_LINE = "#888888"
QUIET_TEXT = "#888888"  # axis numbers
SWATCH_EDGE = "#999999"
HIGHLIGHT = "#1e90ff"  # unfinished part, selected part, mouse marker
PROBLEM_TEXT = "#c0392b"  # error messages
SMALL_FONT = "TkSmallCaptionFont"
HEADING_FONT = "TkHeadingFont"
LINE_WIDTH = 2
DOT_RADIUS = 3
START_RADIUS = 6  # bigger, so the first point is easy to click again
MARKER_RADIUS = 5
SELECTED_DASH = (5, 3)  # 5 pixels of line, then a 3 pixel gap
LABEL_GAP = 4  # gap between the grid and its numbers
SWATCH = 20  # colour square size
SWATCH_GAP = 6
SWATCH_STEP = SWATCH + SWATCH_GAP  # distance from one square to the next
PALETTE_COLUMNS = 6
PAD = 12  # window padding
GAP = 10  # between groups of controls
SMALL_GAP = 3
LIST_ROWS = 5
SHAPES_TAG = "shapes"  # tag for canvas items redrawn on every change
MARKER_TAG = "marker"  # tag for the ring that follows the mouse

# Exported files.
MAX_LINE_LENGTH = 79  # PEP 8 line limit
INDENT = " " * 4
# A program saved with the name of one of Python's own modules, such as
# turtle.py or random.py, would be imported instead of the real module, so
# it would not run. sys.stdlib_module_names needs Python 3.10 or newer.
BLOCKED_FILE_NAMES = sys.stdlib_module_names
EXPORT_SIZE = 2  # exported shape is twice the drawing size
EXPORT_STEP = 10  # pixels moved per key press
EXPORT_TURN = 15  # degrees turned per key press


# Drawing logic

class ShapeError(Exception):
    """Error with a message to show the user."""


class Part:
    """One filled polygon in the shape."""

    def __init__(self, points, fill, outline):
        self.points = points  # tuple of (x, y) tuples
        self.fill = fill
        self.outline = outline


def in_grid(point):
    x, y = point
    return abs(x) <= GRID_RANGE and abs(y) <= GRID_RANGE


def cross(a, b, c):
    """Return > 0 if a -> b -> c turns left, < 0 if right, 0 if straight."""
    (ax, ay), (bx, by), (cx, cy) = a, b, c
    # The cross product of the vectors a->b and a->c.
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def on_segment(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    # p must be on the line through a and b, and inside the box around them.
    return (cross(a, b, p) == 0
            and min(ax, bx) <= px <= max(ax, bx)
            and min(ay, by) <= py <= max(ay, by))


def segments_meet(a, b, c, d):
    """Return True if segment a-b crosses or touches segment c-d."""
    # proper cross: a, b on opposite sides of c-d and c, d on
    # opposite sides of a-b
    if (cross(c, d, a) * cross(c, d, b) < 0
            and cross(a, b, c) * cross(a, b, d) < 0):
        return True
    # touching: an end point lies on the other segment
    return (on_segment(a, c, d) or on_segment(b, c, d)
            or on_segment(c, a, b) or on_segment(d, a, b))


def turns_back(a, b, c):
    """Return True if a -> b -> c goes back along line a-b."""
    (ax, ay), (bx, by), (cx, cy) = a, b, c
    # dot product > 0 means c is on the same side of b as a
    same_side = (ax - bx) * (cx - bx) + (ay - by) * (cy - by) > 0
    return cross(a, b, c) == 0 and same_side


def all_in_line(points):
    # Every point is in line with the first two points.
    return all(cross(points[0], points[1], point) == 0 for point in points)


class Drawing:
    """The finished parts, plus the part being drawn.

    Every change is checked first, and a ShapeError is raised if it breaks
    a rule, so the drawing can never hold a broken part.
    """

    def __init__(self):
        self.parts = []  # finished Part objects, back to front
        self.current = []  # (x, y) points of the unfinished part

    def is_empty(self):
        return not self.parts and not self.current

    def is_start(self, point):
        return len(self.current) > 0 and point == self.current[0]

    def add_point(self, point):
        if not in_grid(point):
            raise ShapeError("Click inside the grid.")
        # Starting a new part when there are already MAX_PARTS.
        if not self.current and len(self.parts) >= MAX_PARTS:
            raise ShapeError(f"A shape can have up to {MAX_PARTS} parts. "
                             "Delete one to start another.")
        if len(self.current) >= MAX_POINTS:
            raise ShapeError(f"A part can have up to {MAX_POINTS} points. "
                             "Finish this part first.")
        if point in self.current:
            raise ShapeError("That point is already in this part.")

        # The new line goes from the last point to this point. It must not
        # double back over the last line, or meet any earlier line.
        if len(self.current) >= 2:
            last = self.current[-1]
            if turns_back(self.current[-2], last, point):
                raise ShapeError("That line would go back over the last "
                                 "one.")
            # skip the newest line, it always touches the new one
            for i in range(len(self.current) - 2):
                if segments_meet(self.current[i], self.current[i + 1],
                                 last, point):
                    raise ShapeError("That line would cross another line "
                                     "in this part.")

        self.current.append(point)

    def finish_part(self, fill, outline):
        points = self.current
        if not points:
            raise ShapeError("Click the grid to start a part first.")
        if len(points) < MIN_POINTS:
            raise ShapeError(f"A part needs at least {MIN_POINTS} points.")
        if all_in_line(points):
            raise ShapeError("These points are all in one straight line, "
                             "so the part would have no inside.")

        # Finishing adds a closing line from the last point to the first.
        # add_point already checked every other line, so only this one is
        # left. It must not double back at either end...
        first, last = points[0], points[-1]
        crosses = (turns_back(points[-2], last, first)
                   or turns_back(last, first, points[1]))
        # ...or meet a line that doesn't share one of its ends. The first
        # and last lines share an end with it, so the loop skips them.
        for i in range(1, len(points) - 2):
            if segments_meet(points[i], points[i + 1], last, first):
                crosses = True
        if crosses:
            raise ShapeError("Joining the last point to the first would "
                             "cross a line. Undo a point and try another "
                             "way round.")

        part = Part(tuple(points), fill, outline)
        self.parts.append(part)
        self.current = []
        return part

    def undo_point(self):
        # Returns False when there is nothing to undo.
        if not self.current:
            return False
        self.current.pop()
        return True

    def cancel_part(self):
        self.current = []

    def delete_part(self, index):
        del self.parts[index]

    def recolour(self, index, kind, colour):
        # kind is "fill" or "outline".
        part = self.parts[index]
        if kind == "fill":
            part.fill = colour
        else:
            part.outline = colour

    def clear(self):
        self.parts = []
        self.current = []


# Names and files

def check_shape_name(text):
    """Return the name without outer spaces, or raise ShapeError."""
    name = text.strip()
    if not name:
        raise ShapeError("Please give your shape a name.")
    if len(name) > MAX_NAME_LENGTH:
        raise ShapeError(f"The shape name can be up to {MAX_NAME_LENGTH} "
                         "characters long.")
    if not name[0].isalpha():
        raise ShapeError("The shape name must start with a letter.")
    for character in name:
        # Quotes and backslashes are never allowed, so the name is always
        # safe to put inside a string in the exported program.
        if not (character.isalnum() or character in " _"):
            raise ShapeError("The shape name can only use letters, numbers, "
                             "spaces and _.")
    return name


def suggested_file_name(name):
    # "My Ship" becomes "my_ship". Blocked names get "_shape" added.
    stem = "_".join(name.lower().split())
    if stem in BLOCKED_FILE_NAMES:
        stem += "_shape"
    return stem


def blocked_module(path):
    # Returns the module name if path is a blocked .py file, else None.
    stem, extension = os.path.splitext(os.path.basename(path))
    if extension.lower() == ".py" and stem.lower() in BLOCKED_FILE_NAMES:
        return stem.lower()
    return None


# Export and import
# The export functions expect a name that has passed check_shape_name and
# at least one part. The window checks both before calling them.

def points_assignment(variable, points):
    """Return a line like "part_1 = ((0, 10), (8, -6), (-8, -6))"."""
    items = [str(point) for point in points]
    one_line = f"{variable} = ({', '.join(items)})"
    if len(one_line) <= MAX_LINE_LENGTH:
        return one_line

    # too long, so wrap the points over several lines
    lines = [f"{variable} = ("]
    row = INDENT
    for item in items:
        if len(row) + len(item) + 1 > MAX_LINE_LENGTH:  # +1 for the comma
            lines.append(row.rstrip())
            row = INDENT
        row += item + ", "
    lines.append(row.rstrip())
    lines.append(")")
    return "\n".join(lines)


def make_text(name, parts):
    # all comments or python so it can be pasted into a program
    lines = [
        f"# Turtle shape: {name}",
        f"# Made with {APP_NAME}.",
        "#",
        "# Each part is a tuple of (x, y) points. To use one part as a shape:",
        f'#     turtle.register_shape("{name}", part_1)',
        '# To use several parts, join them with turtle.Shape("compound") and',
        "# addcomponent(). The top of the drawing is the front of the shape,",
        "# so use setheading(90) to show it the same way up as it was drawn.",
        "",
    ]
    for number, part in enumerate(parts, start=1):
        lines.append(f"# Part {number}: {part.fill}, with a {part.outline} "
                     "outline")
        lines.append(points_assignment(f"part_{number}", part.points))
        lines.append("")
    return "\n".join(lines)


def make_python(name, parts):
    # Builds the program line by line. One part becomes a polygon shape;
    # several parts become a compound shape where each keeps its colours.
    lines = [
        f'"""Starter program for the turtle shape "{name}".',
        "",
        f"Made with {APP_NAME}. Run this file to see the shape, then use",
        "the arrow keys to move it. Build your own program or game from here.",
        '"""',
        "",
        "import turtle",
        "",
        f'SHAPE_NAME = "{name}"',
        f"SIZE = {EXPORT_SIZE}  # how many times bigger than the drawing",
        f"STEP = {EXPORT_STEP}  # how far the turtle moves per key press",
        f"TURN = {EXPORT_TURN}  # how many degrees it turns per key press",
        "",
        "# The (x, y) points of each part. The top of the drawing is the",
        "# front of the shape, which is the way the turtle moves.",
    ]
    for number, part in enumerate(parts, start=1):
        lines.append(points_assignment(f"PART_{number}", part.points))

    lines += ["", "", "def make_shape():"]
    if len(parts) == 1:
        lines.append('    """Register the shape so turtles can use it."""')
        lines.append("    turtle.register_shape(SHAPE_NAME, PART_1)")
    else:
        lines.append('    """Join the parts into one shape and register '
                     'it."""')
        lines.append('    shape = turtle.Shape("compound")')
        for number, part in enumerate(parts, start=1):
            lines.append(f'    shape.addcomponent(PART_{number}, '
                         f'"{part.fill}", "{part.outline}")')
        lines.append("    turtle.register_shape(SHAPE_NAME, shape)")

    lines += [
        "",
        "",
        "def move_forward():",
        '    """Move forward one step."""',
        "    player.forward(STEP)",
        "",
        "",
        "def move_back():",
        '    """Move back one step."""',
        "    player.backward(STEP)",
        "",
        "",
        "def turn_left():",
        '    """Turn to the left."""',
        "    player.left(TURN)",
        "",
        "",
        "def turn_right():",
        '    """Turn to the right."""',
        "    player.right(TURN)",
        "",
        "",
        "screen = turtle.Screen()",
        "screen.title(SHAPE_NAME)",
        "make_shape()",
        "",
        "player = turtle.Turtle()",
        "player.shape(SHAPE_NAME)",
    ]
    if len(parts) == 1:
        # A single polygon takes its colours from the turtle.
        lines.append(f'player.color("{parts[0].outline}", '
                     f'"{parts[0].fill}")  # outline, fill')
    lines += [
        "player.shapesize(SIZE)",
        "player.penup()",
        "player.setheading(90)  # face up, so the shape looks as it was drawn",
        "",
        "# The arrow keys drive the turtle. Remove these if you don't need "
        "them.",
        'screen.onkey(move_forward, "Up")',
        'screen.onkey(move_back, "Down")',
        'screen.onkey(turn_left, "Left")',
        'screen.onkey(turn_right, "Right")',
        "screen.listen()",
        "",
        "turtle.done()",
        "",
    ]
    return "\n".join(lines)


def make_drawing_file(name, parts):
    # json writes the tuples of points as lists, e.g. [[0, 10], [8, -6]].
    data = {"name": name, "parts": []}
    for part in parts:
        data["parts"].append({"fill": part.fill, "outline": part.outline,
                              "points": part.points})
    return json.dumps(data, indent=2)


def read_drawing_file(text):
    """Return (name, Drawing) from drawing file text, or raise ShapeError."""
    try:
        data = json.loads(text)
        name = check_shape_name(data["name"])
        if not data["parts"]:
            raise ShapeError("The drawing file has no parts in it.")
        if len(data["parts"]) > MAX_PARTS:
            raise ShapeError(f"The drawing file has more than {MAX_PARTS} "
                             "parts.")
        # The parts are redrawn point by point, so a file has to follow the
        # same rules as drawing by hand.
        drawing = Drawing()
        for number, part in enumerate(data["parts"], start=1):
            add_part_from_file(drawing, number, part)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        # bad JSON, missing keys or wrong types. ShapeError gets through.
        raise ShapeError("That file is not a drawing from "
                         f"{APP_NAME}.") from error
    return name, drawing


def add_part_from_file(drawing, number, part):
    # part is a dictionary from the file. number is only for messages.
    fill, outline, points = part["fill"], part["outline"], part["points"]
    if fill not in COLOURS or outline not in COLOURS:
        raise ShapeError(f"Part {number} in the file uses a colour that is "
                         "not in the palettes.")
    try:
        # The number of points and the grid are checked here, before
        # add_point, so the messages are about the file, not about clicking.
        if not MIN_POINTS <= len(points) <= MAX_POINTS:
            raise ShapeError(f"A part needs {MIN_POINTS} to {MAX_POINTS} "
                             "points.")
        for x, y in points:
            # type() so floats and True/False don't count as ints
            if type(x) is not int or type(y) is not int:
                raise ShapeError("Points must be whole numbers.")
            if not in_grid((x, y)):
                raise ShapeError(f"The point {(x, y)} is outside the grid.")
            drawing.add_point((x, y))
        drawing.finish_part(fill, outline)
    except ShapeError as problem:
        # Add the part number so the user knows which part is wrong.
        raise ShapeError(f"Part {number} in the file has a problem: "
                         f"{problem}") from problem


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

class ColourPalette:
    """A grid of colour squares. Clicking a square picks its colour."""

    def __init__(self, parent, chosen, on_pick):
        self.chosen = chosen
        self.on_pick = on_pick  # called with the colour name when clicked
        rows = math.ceil(len(COLOURS) / PALETTE_COLUMNS)
        self.canvas = tk.Canvas(parent, width=PALETTE_COLUMNS * SWATCH_STEP,
                                height=rows * SWATCH_STEP,
                                highlightthickness=0, cursor="hand2")
        self.canvas.bind("<Button-1>", self.clicked)
        self.draw()

    def show(self, colour):
        # Marks a colour without calling on_pick (used when a part is
        # selected in the list).
        self.chosen = colour
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        offset = SWATCH_GAP // 2  # half a gap around each square
        for index, colour in enumerate(COLOURS):
            # row and column of this square
            row, column = divmod(index, PALETTE_COLUMNS)
            x = column * SWATCH_STEP + offset
            y = row * SWATCH_STEP + offset
            self.canvas.create_rectangle(x, y, x + SWATCH, y + SWATCH,
                                         fill=colour, outline=SWATCH_EDGE)
            if colour == self.chosen:
                # A ring in the gap around the chosen square.
                ring = offset - 1
                self.canvas.create_rectangle(
                    x - ring, y - ring, x + SWATCH + ring, y + SWATCH + ring,
                    outline=HIGHLIGHT, width=LINE_WIDTH)

    def clicked(self, event):
        # which square was clicked?
        column = event.x // SWATCH_STEP
        row = event.y // SWATCH_STEP
        index = row * PALETTE_COLUMNS + column
        if column < PALETTE_COLUMNS and index < len(COLOURS):
            self.show(COLOURS[index])
            self.on_pick(COLOURS[index])


class ShapeMakerApp:
    """The main window: grid, controls and status line."""

    def __init__(self, root):
        self.root = root
        self.drawing = Drawing()
        self.name = tk.StringVar(value=DEFAULT_NAME)
        self.message = tk.StringVar()
        self.mouse_position = tk.StringVar()

        root.title(APP_NAME)
        root.resizable(False, False)  # the grid has a fixed size

        self.build_window()
        self.draw_grid()
        self.bind_events()
        self.say("Click a grid point to start drawing a part.")

    def build_window(self):
        frame = ttk.Frame(self.root, padding=PAD)
        frame.pack()

        self.canvas = tk.Canvas(frame, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                background=CANVAS_BACKGROUND,
                                highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="n")

        panel = ttk.Frame(frame, padding=(PAD, 0, 0, 0))
        panel.grid(row=0, column=1, sticky="n")
        self.build_panel(panel)

        # wraplength makes long messages wrap instead of widening the window.
        self.message_label = ttk.Label(frame, textvariable=self.message,
                                       wraplength=CANVAS_SIZE)
        self.message_label.grid(row=1, column=0, sticky="w", pady=(GAP, 0))
        ttk.Label(frame, textvariable=self.mouse_position).grid(
            row=1, column=1, sticky="e", pady=(GAP, 0))

    def build_panel(self, panel):
        self.add_heading(panel, "Shape name", first=True)
        ttk.Entry(panel, textvariable=self.name).pack(fill="x")

        # The lambdas tell colour_picked which palette was clicked.
        self.add_heading(panel, "Fill colour")
        self.fill_palette = ColourPalette(
            panel, START_FILL,
            lambda colour: self.colour_picked("fill", colour))
        self.fill_palette.canvas.pack(anchor="w")

        self.add_heading(panel, "Outline colour")
        self.outline_palette = ColourPalette(
            panel, START_OUTLINE,
            lambda colour: self.colour_picked("outline", colour))
        self.outline_palette.canvas.pack(anchor="w")

        self.add_heading(panel, "Part being drawn")
        self.add_button_row(panel, [("Finish", self.finish_part),
                                    ("Undo", self.undo_point),
                                    ("Cancel", self.cancel_part)])

        self.add_heading(panel, "Parts (later ones are on top)")
        # The list and its scrollbar share a frame so they sit side by side.
        list_frame = ttk.Frame(panel)
        list_frame.pack(fill="x")
        # exportselection=False keeps the selection when text elsewhere is
        # selected, e.g. in the name box.
        self.part_list = tk.Listbox(list_frame, height=LIST_ROWS,
                                    activestyle="none", exportselection=False)
        scrollbar = ttk.Scrollbar(list_frame, command=self.part_list.yview)
        self.part_list.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.part_list.pack(side="left", fill="x", expand=True)
        self.add_button_row(panel, [("Delete", self.delete_part),
                                    ("Clear all", self.clear_all)])

        self.add_heading(panel, "Import and export")
        self.add_button_row(panel, [("Export .txt", self.export_text),
                                    ("Export .py", self.export_python)])
        self.add_button_row(panel, [("Import drawing", self.import_drawing),
                                    ("Export drawing", self.export_drawing)])

    def add_heading(self, panel, text, first=False):
        top_gap = 0 if first else GAP
        ttk.Label(panel, text=text, font=HEADING_FONT).pack(
            anchor="w", pady=(top_gap, SMALL_GAP))

    def add_button_row(self, panel, buttons):
        # buttons is a list of (text, command) pairs.
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=(SMALL_GAP, 0))
        for column, (text, command) in enumerate(buttons):
            # uniform makes the buttons the same width
            row.columnconfigure(column, weight=1, uniform="buttons")
            left_gap = 0 if column == 0 else SMALL_GAP
            ttk.Button(row, text=text, command=command).grid(
                row=0, column=column, sticky="ew", padx=(left_gap, 0))

    def draw_grid(self):
        # light lines first so the darker ones end up on top
        for value in range(-GRID_RANGE, GRID_RANGE + 1):
            if value % NUMBER_EVERY != 0:
                self.draw_grid_lines(value, MINOR_LINE)
        for value in range(-GRID_RANGE, GRID_RANGE + 1, NUMBER_EVERY):
            self.draw_grid_lines(value, MAJOR_LINE)
            # Numbers along the bottom (x) and the left side (y).
            x, y = point_to_pixel((value, value))
            self.canvas.create_text(x, GRID_HIGH + LABEL_GAP, text=str(value),
                                    anchor="n", fill=QUIET_TEXT,
                                    font=SMALL_FONT)
            self.canvas.create_text(GRID_LOW - LABEL_GAP, y, text=str(value),
                                    anchor="e", fill=QUIET_TEXT,
                                    font=SMALL_FONT)
        self.draw_grid_lines(0, AXIS_LINE)
        self.canvas.create_text(CENTRE, GRID_LOW - LABEL_GAP, anchor="s",
                                text="front of the shape", fill=QUIET_TEXT,
                                font=SMALL_FONT)

    def draw_grid_lines(self, value, colour):
        # vertical and horizontal line
        x, y = point_to_pixel((value, value))
        self.canvas.create_line(x, GRID_LOW, x, GRID_HIGH, fill=colour)
        self.canvas.create_line(GRID_LOW, y, GRID_HIGH, y, fill=colour)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.canvas_clicked)
        # Right-click undoes a point. Macs call the right button Button-2.
        self.canvas.bind("<Button-2>", lambda event: self.undo_point())
        self.canvas.bind("<Button-3>", lambda event: self.undo_point())
        self.canvas.bind("<Motion>", self.mouse_moved)
        self.canvas.bind("<Leave>", self.mouse_left)
        self.part_list.bind("<<ListboxSelect>>", self.part_selected)
        self.part_list.bind("<Delete>", lambda event: self.delete_part())
        # Bound to the whole window, so they work wherever the focus is.
        self.root.bind("<Return>", lambda event: self.finish_part())
        self.root.bind("<Escape>", lambda event: self.cancel_part())

    def say(self, text, problem=False):
        # red for problems, "" = normal colour
        self.message.set(text)
        if problem:
            self.message_label.config(foreground=PROBLEM_TEXT)
        else:
            self.message_label.config(foreground="")

    def selected_index(self):
        # curselection() is a tuple, empty if nothing is selected
        selection = self.part_list.curselection()
        if selection:
            return selection[0]
        return None

    def refresh_list(self, keep=None):
        # Rebuilds the list, then reselects row keep if one is given.
        self.part_list.delete(0, tk.END)
        for number, part in enumerate(self.drawing.parts, start=1):
            self.part_list.insert(
                tk.END, f"{number}. {part.fill} ({len(part.points)} points)")
        if keep is not None:
            # rebuilding loses the scroll and active row, so put them back
            self.part_list.selection_set(keep)
            self.part_list.activate(keep)
            self.part_list.see(keep)

    def redraw(self):
        # Only items tagged SHAPES_TAG are deleted, so the grid stays.
        self.canvas.delete(SHAPES_TAG)
        for part in self.drawing.parts:
            self.canvas.create_polygon(to_pixels(part.points),
                                       fill=part.fill, outline=part.outline,
                                       width=LINE_WIDTH, tags=SHAPES_TAG)

        # dashed outline on top for the selected part
        index = self.selected_index()
        if index is not None:
            self.canvas.create_polygon(
                to_pixels(self.drawing.parts[index].points), fill="",
                outline=HIGHLIGHT, width=LINE_WIDTH, dash=SELECTED_DASH,
                tags=SHAPES_TAG)

        self.draw_unfinished_part()
        self.canvas.tag_raise(MARKER_TAG)  # keep the mouse ring on top

    def draw_unfinished_part(self):
        points = self.drawing.current
        if len(points) >= 2:
            self.canvas.create_line(to_pixels(points), fill=HIGHLIGHT,
                                    width=LINE_WIDTH, tags=SHAPES_TAG)
        # first point is bigger and hollow so you can click it again
        for index, point in enumerate(points):
            x, y = point_to_pixel(point)
            if index == 0:
                radius, fill = START_RADIUS, CANVAS_BACKGROUND
            else:
                radius, fill = DOT_RADIUS, HIGHLIGHT
            self.canvas.create_oval(x - radius, y - radius,
                                    x + radius, y + radius, fill=fill,
                                    outline=HIGHLIGHT, width=LINE_WIDTH,
                                    tags=SHAPES_TAG)

    def canvas_clicked(self, event):
        point = pixel_to_point(event.x, event.y)
        # Clicking the first point again finishes the part.
        if self.drawing.is_start(point):
            self.finish_part()
            return

        # Deselect parts so colour picks apply to the new part.
        self.part_list.selection_clear(0, tk.END)
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
        self.canvas.delete(MARKER_TAG)
        point = pixel_to_point(event.x, event.y)
        if not in_grid(point):
            self.mouse_position.set("")
            return
        x, y = point_to_pixel(point)
        self.canvas.create_oval(x - MARKER_RADIUS, y - MARKER_RADIUS,
                                x + MARKER_RADIUS, y + MARKER_RADIUS,
                                outline=HIGHLIGHT, width=LINE_WIDTH,
                                tags=MARKER_TAG)
        self.mouse_position.set(f"x {point[0]}, y {point[1]}")

    def mouse_left(self, event):
        self.canvas.delete(MARKER_TAG)
        self.mouse_position.set("")

    def finish_part(self):
        try:
            self.drawing.finish_part(self.fill_palette.chosen,
                                     self.outline_palette.chosen)
        except ShapeError as problem:
            self.say(str(problem), problem=True)
            return
        self.refresh_list()
        self.say(f"Part {len(self.drawing.parts)} finished. Draw another "
                 "part, or export your shape.")
        self.redraw()

    def undo_point(self):
        if self.drawing.undo_point():
            self.say("The last point was removed.")
        else:
            self.say("There is no point to undo.", problem=True)
        self.redraw()

    def cancel_part(self):
        if not self.drawing.current:
            self.say("There is no unfinished part to cancel.", problem=True)
            return
        self.drawing.cancel_part()
        self.say("The unfinished part was removed.")
        self.redraw()

    def part_selected(self, event):
        # Show the part's colours in the palettes, so picking a colour now
        # changes this part.
        index = self.selected_index()
        if index is not None:
            part = self.drawing.parts[index]
            self.fill_palette.show(part.fill)
            self.outline_palette.show(part.outline)
            self.say(f"Part {index + 1} selected. Pick a colour to change "
                     "it, or press Delete to remove it.")
        self.redraw()

    def colour_picked(self, kind, colour):
        # With no part selected, the colour is just used for new parts.
        index = self.selected_index()
        if index is None:
            self.say(f"New parts will have a {colour} {kind}.")
            return
        self.drawing.recolour(index, kind, colour)
        self.refresh_list(keep=index)
        self.say(f"Part {index + 1} now has a {colour} {kind}.")
        self.redraw()

    def delete_part(self):
        index = self.selected_index()
        if index is None:
            self.say("Select a part in the list first.", problem=True)
            return
        self.drawing.delete_part(index)
        self.refresh_list()
        self.say(f"Part {index + 1} was deleted.")
        self.redraw()

    def clear_all(self):
        if self.drawing.is_empty():
            self.say("There is nothing to clear.", problem=True)
            return
        if messagebox.askyesno(APP_NAME, "Delete every part and start "
                                         "again?"):
            self.drawing.clear()
            self.refresh_list()
            self.say("Everything was cleared.")
            self.redraw()

    def export_text(self):
        self.export_file(".txt", "Text file", make_text)

    def export_python(self):
        self.export_file(".py", "Python program", make_python)

    def export_drawing(self):
        if self.export_file(".json", "Drawing file", make_drawing_file):
            self.say(self.message.get() + " Use Import drawing to open it "
                     "again.")

    def export_file(self, extension, description, make):
        """Ask for a file name and save make(name, parts) in it.

        Returns True if the file was saved.
        """
        if self.drawing.current:
            self.say("Finish or cancel the part you are drawing first.",
                     problem=True)
            return False
        if not self.drawing.parts:
            self.say("Draw at least one part first.", problem=True)
            return False
        try:
            name = check_shape_name(self.name.get())
        except ShapeError as problem:
            self.say(str(problem), problem=True)
            return False
        self.name.set(name)  # show the name with outer spaces removed

        path = filedialog.asksaveasfilename(
            title=f"Export as {description.lower()}",
            defaultextension=extension,
            filetypes=[(description, "*" + extension)],
            initialfile=suggested_file_name(name) + extension)
        if not path:
            return False  # the user pressed Cancel

        module = blocked_module(path)
        if module:
            messagebox.showwarning(
                APP_NAME,
                f"Please choose another name. A program called {module}.py "
                f"stops Python from finding its own {module} module.")
            return False

        # saving can fail (no permission, disk full etc)
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(make(name, self.drawing.parts))
        except OSError as error:
            messagebox.showerror(APP_NAME,
                                 f"The file could not be saved.\n\n{error}")
            return False
        self.say(f"Saved {os.path.basename(path)}.")
        return True

    def import_drawing(self):
        path = filedialog.askopenfilename(
            title="Import a drawing",
            filetypes=[("Drawing file", "*.json")])
        if not path:
            return  # the user pressed Cancel

        # The file is read and checked before anything changes, so a bad
        # file leaves the current drawing untouched.
        try:
            # utf-8-sig copes with the BOM that Notepad adds
            with open(path, encoding="utf-8-sig") as file:
                name, drawing = read_drawing_file(file.read())
        except (OSError, UnicodeDecodeError) as error:
            # The file is missing, locked, or not a text file.
            messagebox.showerror(APP_NAME,
                                 f"The file could not be opened.\n\n{error}")
            return
        except ShapeError as problem:
            messagebox.showerror(APP_NAME, str(problem))
            return

        if not self.drawing.is_empty() and not messagebox.askyesno(
                APP_NAME, "Replace your current drawing with this one?"):
            return
        self.drawing = drawing
        self.name.set(name)
        self.refresh_list()
        self.say(f"Imported {os.path.basename(path)}.")
        self.redraw()


def main():
    root = tk.Tk()
    ShapeMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
