#!/usr/bin/env python
"""Generate station map for README

Run this script to update the station map image in images/station_map.png
"""
import dwd_opendata as dwd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path

# Get project root directory
project_root = Path(__file__).parent.parent
images_dir = project_root / "images"
images_dir.mkdir(exist_ok=True)

start = datetime(1980, 1, 1)
end = datetime(2016, 12, 31)
variables = ("wind", "air_temperature", "sun", "precipitation")

print("Generating station map...")
fig, ax = dwd.map_stations(
    variables,
    lon_min=7,
    lat_min=47.4,
    lon_max=12.0,
    lat_max=49.0,
    start=start,
    end=end,
)

output_path = images_dir / "station_map.png"
fig.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Station map saved to {output_path}")
print("\nDon't forget to commit the updated image:")
print("  git add images/station_map.png")
print("  git commit -m 'Update station map'")
