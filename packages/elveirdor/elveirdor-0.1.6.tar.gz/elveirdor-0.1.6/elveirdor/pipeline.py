"""Pipeline entrypoints for elveirdor."""
from .grid import init_grid
from .export import export_png
from .decode import decode_standard, decode_elveirdor

# create a simple pipeline wrapper (replace with your full logic)
def run_elveirdor_pipeline(grid_size=20, output_filename="output.png", text="ELVEIRDOR", sequence=None):
    grid = init_grid(grid_size)
    # placeholder: paint a diagonal for demo
    for i in range(grid_size):
        grid[i,i] = (0,0,0)
    export_png(grid, output_filename)
    if sequence:
        print("Standard:", decode_standard(sequence))
    print("Saved:", output_filename)
