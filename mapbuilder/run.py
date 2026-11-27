"""Rebuild the whole atlas from the archive:  python3 -m mapbuilder.run

Outlines, region lists, region cells, events, then the page and its data. Region positions come
from map/region_labels.json and control history from map/control_raw/, so nothing here needs
the network.
"""
from __future__ import annotations

import runpy

STEPS = ["mapbuilder.geometry", "mapbuilder.regions", "mapbuilder.partition", "mapbuilder.events", "mapbuilder.build"]

if __name__ == "__main__":
    for step in STEPS:
        print(f"== {step}", flush=True)
        runpy.run_module(step, run_name="__main__")
