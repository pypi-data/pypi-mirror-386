import json, base64, os
from PIL import Image
from datetime import datetime

def export_png(grid, filename):
    img = Image.fromarray(grid)
    img.save(filename)

def export_json(metadata, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def make_html_preview(png_file, json_file, html_file):
    # Load metadata JSON
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except Exception:
        meta = {"error": "missing metadata"}

    # Load image as base64
    try:
        with open(png_file, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        img_data = None

    # Timestamp
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build HTML
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Elveirdor Preview - {ts}</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; }}
    img {{ max-width: 600px; display: block; margin-bottom: 1em; }}
    pre {{ background: #f4f4f4; padding: 1em; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>Elveirdor Preview</h1>
  <p><em>Generated at {ts}</em></p>
"""

    if img_data:
        html += f'<img src="data:image/png;base64,{img_data}" alt="Mosaic preview">\n'
        html += f'<a href="{png_file}" download>Download PNG</a><br>\n'
    else:
        html += "<p>No image available.</p>\n"

    html += f'<a href="{json_file}" download>Download JSON</a>\n'
    html += f"<pre>{json.dumps(meta, indent=2)}</pre>\n"

    html += """</body>
</html>
"""

    # Write to file
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)
