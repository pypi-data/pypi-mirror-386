# grid.py

import random

def initialize_grid(size, seed=12345, white=True):
    """
    Create a square grid of given size.
    If white=True, fill with 1s, else 0s.
    """
    if seed is not None:
        random.seed(seed)
    fill = 1 if white else 0
    return [[fill for _ in range(size)] for _ in range(size)]

# Alias for compatibility with pipeline.py
create_grid = initialize_grid

def draw_m(grid, x, y, scale=1):
    # Example placeholder: mark an "M" at (x, y)
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = "M"

def draw_y(grid, x=None, y=None):
    # Example placeholder: mark a "Y" at center if no coords
    gx, gy = len(grid[0]), len(grid)
    cx, cy = gx // 2, gy // 2
    if x is None: x = cx
    if y is None: y = cy
    if 0 <= y < gy and 0 <= x < gx:
        grid[y][x] = "Y"

def transition_to_black(grid):
    # Example: set all cells to 0
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            grid[y][x] = 0

def combustion_invert(grid):
    # Example: flip 0s to 1s and 1s to 0s
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            val = grid[y][x]
            if val == 0:
                grid[y][x] = 1
            elif val == 1:
                grid[y][x] = 0

from PIL import Image

def save_grid_as_png(grid, path, cell_size=10):
    """
    Render the grid as a PNG image.
    - grid: 2D list of values (0, 1, "M", "Y", etc.)
    - path: output filename
    - cell_size: pixel size of each grid cell
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    img = Image.new("RGB", (width * cell_size, height * cell_size), color="white")
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            val = grid[y][x]
            if val == 0:
                color = (0, 0, 0)       # black
            elif val == 1:
                color = (255, 255, 255) # white
            elif val == "M":
                color = (200, 0, 0)     # red for M
            elif val == "Y":
                color = (0, 0, 200)     # blue for Y
            else:
                color = (128, 128, 128) # gray fallback

            # Fill the cell
            for dy in range(cell_size):
                for dx in range(cell_size):
                    pixels[x * cell_size + dx, y * cell_size + dy] = color

    img.save(path)
