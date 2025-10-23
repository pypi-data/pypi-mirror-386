import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import argparse
import os
import json
from datetime import datetime

# --- ELVEIRDOR COLOR MAP ---
COLOR_MAP = {
    'A': (255, 0, 0), 'B': (0, 0, 255), 'C': (255, 165, 0),
    'Ch': (0, 0, 0), 'Ck': (0, 255, 0), 'D': (255, 255, 0),
    'E': (0, 128, 128), 'F': (128, 128, 128), 'G': (128, 0, 128),
    'H': (0, 255, 255), 'I': (46, 139, 87), 'J': (173, 216, 230),
    'K': (0, 100, 0), 'L': (255, 255, 255), 'LL': (255, 215, 0),
    'M': (0, 0, 0), 'N': (220, 20, 60), 'O': (165, 42, 42),
    'P': (0, 0, 128), 'Ph': (75, 83, 32), 'Q': (255, 182, 193),
    'R': (255, 255, 255), 'S': (192, 192, 192), 'T': (255, 165, 0),
    'Th': (255, 140, 0), 'U': (200, 162, 200), 'V': (143, 0, 255),
    'W': (70, 130, 180), 'Wh': (160, 82, 45), 'X': (65, 105, 225),
    'Y': (154, 205, 50), 'Z': (255, 69, 0)
}

# --- DECODING FUNCTION ---
def decode_sequence(sequence, cipher='standard'):
    """Decode numeric sequence into letters."""
    if cipher == 'standard':
        mapping = {i: chr(ord('A') + i - 1) for i in range(1, 27)}
    else:
        map_keys = list(COLOR_MAP.keys())
        mapping = {i: map_keys[i-1] for i in range(1, len(map_keys) + 1)}
    return "".join(mapping.get(int(s), '?') for s in sequence.split() if s.isdigit())

# --- CORE FUNCTIONS ---
def initialize_grid(size, seed=12345):
    np.random.seed(seed)
    return np.ones((size, size, 3), dtype=np.uint8) * 255

def draw_m(grid, x, y, scale=1):
    m_coords = [(0,0),(0,1),(0,2),(1,2),(1,1),(2,0),(3,1),(4,2),(4,1),(4,0)]
    for cx, cy in [(x + c[0]*scale, y + c[1]*scale) for c in m_coords]:
        if 0 <= cx < grid.shape[0] and 0 <= cy < grid.shape[1]:
            grid[cx, cy] = COLOR_MAP['M']
    return grid

def draw_y(grid, x, y):
    y_coords = [(2,0),(2,1),(2,2),(3,2),(4,3),(3,3)]
    for cx, cy in [(x + c[0], y + c[1]) for c in y_coords]:
        if 0 <= cx < grid.shape[0] and 0 <= cy < grid.shape[1]:
            grid[cx, cy] = COLOR_MAP['Y']
    return grid

def transition_to_black(grid):
    m_color = COLOR_MAP['M']
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            if not np.array_equal(grid[i, j], m_color):
                grid[i, j] = (0, 0, 0)
    for i in range(1, grid.shape[0]):
        grid[i, :, 1] = 255
    return grid

def create_mosaic(grid):
    return grid

def combustion_invert(grid):
    return 255 - grid

def pixel_fill(grid):
    return grid

# --- MAIN PIPELINE ---
def run_elveirdor_pipeline(grid_size=10, output_filename='output.png', text="DEFAULT", sequence=None):
    print(f"--- Running Elveirdor Pipeline (Grid {grid_size}x{grid_size}) ---")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(output_filename)[0]
    output_png = f"{base_name}_{timestamp}.png"
    output_json = f"{base_name}_{timestamp}.json"
    output_html = f"{base_name}_{timestamp}.html"

    if sequence:
        print(f"Sequence: {sequence}")
        print(f"Standard Decode: {decode_sequence(sequence, 'standard')}")
        print(f"Elveirdor Decode: {decode_sequence(sequence, 'elveirdor')}")
        print("-" * 40)

    grid = initialize_grid(grid_size)
    grid = draw_m(grid, 2, 2)
    grid = transition_to_black(grid)
    grid = create_mosaic(grid)
    grid = draw_y(grid, grid_size // 2, grid_size // 2)
    grid = combustion_invert(grid)
    grid = pixel_fill(grid)

    img = Image.fromarray(grid)
    img.save(output_png)

    metadata = {
        "text": text,
        "grid_size": grid_size,
        "timestamp": timestamp,
        "files": {"png": output_png, "json": output_json, "html": output_html},
        "steps": ["init", "draw_m", "transition", "mosaic", "draw_y", "invert", "pixel_fill"]
    }

    with open(output_json, "w") as f:
        json.dump(metadata, f, indent=2)

    with open(output_html, "w") as f:
        f.write(f"<html><body><h1>Elveirdor Output</h1><img src='{output_png}'><pre>{json.dumps(metadata, indent=2)}</pre></body></html>")

    print("Pipeline complete ✅")
    print(json.dumps(metadata, indent=2))
    plt.imshow(grid)
    plt.title(f"Elveirdor: {text}")
    plt.show()

# --- CLI SUPPORT ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Elveirdor Grok 3 pipeline")
    parser.add_argument("--grid", type=int, default=10, help="Grid size")
    parser.add_argument("--text", type=str, default="ELVEIRDOR", help="Text title")
    parser.add_argument("--export", type=str, default="elveirdor_output.png", help="Output filename")
    parser.add_argument("--sequence", type=str, help="Numeric sequence to decode")
    args = parser.parse_args()

    run_elveirdor_pipeline(grid_size=args.grid, text=args.text, output_filename=args.export, sequence=args.sequence)
