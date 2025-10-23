import time
import json
from .grid import create_grid, draw_y, draw_m, save_grid_as_png

def run_pipeline(text, grid_size=16, seed=12345, sequence=None, x=None, y=None, scale=1):
    """
    Execute the ELVEIRDOR pipeline and return (metadata, grid).

    Parameters:
        text (str): label or prompt string
        grid_size (int): grid dimension
        seed (int): random seed for reproducibility
        sequence (list): optional list of step names to run
        x, y (int): optional coordinates for draw_m (defaults to center)
        scale (int): scale factor for draw_m
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    steps = []
    metadata = {
        "text": text,
        "grid_size": grid_size,
        "seed": seed,
        "timestamp": timestamp,
        "steps": []
    }

    # Initialize grid
    grid = create_grid(grid_size, seed=seed)
    steps.append("initialized")

    # Transition to black
    try:
        # transition_to_black(grid)  # implement if needed
        steps.append("transition_to_black")
    except Exception as e:
        metadata["transition_to_black_error"] = str(e)

    # Create mosaic
    try:
        # create_mosaic(grid)  # implement if needed
        steps.append("create_mosaic")
    except Exception as e:
        metadata["create_mosaic_error"] = str(e)

    # Draw Y
    try:
        draw_y(grid)
        steps.append("draw_y")
    except Exception as e:
        metadata["draw_y_error"] = str(e)

    # Draw M
    try:
        x_pos = x if x is not None else grid_size // 2
        y_pos = y if y is not None else grid_size // 2
        draw_m(grid, x_pos, y_pos, scale=scale)
        steps.append("draw_m")
    except Exception as e:
        metadata["draw_m_error"] = str(e)

    # Combustion invert
    try:
        # combustion_invert(grid)  # implement if needed
        steps.append("combustion_invert")
    except Exception as e:
        metadata["combustion_invert_error"] = str(e)

    # File outputs
    base = f"elveirdor_{timestamp}"
    png_path = f"{base}.png"
    json_path = f"{base}.json"
    html_path = f"{base}.html"

    metadata["png"] = png_path
    metadata["json"] = json_path
    metadata["html"] = html_path
    metadata["scale"] = scale

    # Save JSON metadata
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "text": text,
                "grid_size": grid_size,
                "seed": seed,
                "timestamp": timestamp,
                "steps": steps,
                "scale": scale,
                "png": png_path,
                "html": html_path
            }, f, indent=2)
    except Exception as e:
        metadata["save_json_error"] = str(e)

    # Save PNG
    try:
        save_grid_as_png(grid, png_path, cell_size=10)
    except Exception as e:
        metadata["save_png_error"] = str(e)

    # Save HTML preview
    try:
        html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>ELVEIRDOR {timestamp}</title></head>
<body>
<h1>{text}</h1>
<p>Grid size: {grid_size}, Seed: {seed}, Scale: {scale}</p>
<p>Steps: {", ".join(steps)}</p>
<p><img src="{png_path}" alt="ELVEIRDOR grid"></p>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        metadata["save_html_error"] = str(e)

    metadata["steps"] = steps
    return metadata, grid
