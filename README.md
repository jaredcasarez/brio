
<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="readme/brio_white.png">
  <source media="(prefers-color-scheme: light)" srcset="readme/brio_black.png">
  <img alt="Brio" src="readme/brio_white.png">
</picture>
</p>

# Brio [![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/) [![Panda3D](https://img.shields.io/badge/Panda3D-1.10.9-blue)](https://www.panda3d.org/) ![GitHub Repo Size](https://img.shields.io/github/repo-size/jaredcasarez/brio) ![GitHub Last Commit](https://img.shields.io/github/last-commit/jaredcasarez/brio)

A Python module for brio-style railway track design and management with 3D visualization, built with the <img alt="Panda3D" src="readme/panda3d_logo.png" width="20" height="20"> Panda3D Framework

> Track models supplied by [Michal Fanta on Printables](https://www.printables.com/model/117903-extended-set-of-wooden-train-track-with-50-unique) (under the [Creative Commons Attribution-NonCommercial License](https://creativecommons.org/licenses/by-nc/4.0/))

![Demo](readme/main_demo_1.png)


## Features

- **Track Management**: Create, edit, and manage railway tracks with various types (straight, curved, elevated, switches, crossings)
- **3D Visualization**: Interactive 3D editor with camera controls
- **Collision Detection**: Robust collision detection for automatic linking
- **GUI Interface**: User-friendly graphical interface for track design
- **State Management**: Save and load track configurations
- **Export Functionality**: Export BOM for 3D printing

## Project Structure

```
brio/
├── controls/          # Camera and selection controls
├── gui/              # GUI components (file browser, gallery, properties)
├── models/           # Data models (track, table)
├── state/            # State management and export
├── tools/            # Specialized tools (collision editor)
├── assets/           # Track models, textures, fonts, icons
│   └── models/
│       ├── Straight/    # Straight track pieces
│       ├── Curved/      # Curved track pieces
│       ├── Elevated/    # Elevated/bridge tracks
│       ├── Crossing/    # Track crossings
│       └── Switches/    # Track switches
└── main.py           # Main application entry point
```

## Installation

```bash
git clone https://github.com/jaredcasarez/brio
pip install .
```

## Usage

In the terminal, run:
```bash
brio
```

## Requirements

- Python 3.7+
- Panda3D (for 3D graphics and physics)
- panda3d-simplepbr (lighting and rendering)