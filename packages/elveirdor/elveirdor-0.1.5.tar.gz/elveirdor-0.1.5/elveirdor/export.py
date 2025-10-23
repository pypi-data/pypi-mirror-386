"""Export helpers for images and previews."""
import json
from PIL import Image, ImageDraw

def export_png(grid, path="output.png", cell=16):
    rows, cols = len(grid), len(grid[0]) if grid else 0
    img = Image.new("RGB", (cols*cell, rows*cell), "white")
    d = ImageDraw.Draw(img)
    for y,row in enumerate(grid):
        for x,color in enumerate(row):
            d.rectangle([x*cell, y*cell, (x+1)*cell, (y+1)*cell], fill=tuple(color))
    img.save(path)
    return path

def export_json(grid, path="output.json"):
    with open(path,"w") as f:
        json.dump(grid, f)
    return path
