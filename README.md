# *<p align="center"> trax </p>*

# [![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/) [![Panda3D](https://img.shields.io/badge/Panda3D-1.10.9-blue)](https://www.panda3d.org/) ![GitHub Repo Size](https://img.shields.io/github/repo-size/jaredcasarez/trax) ![GitHub Last Commit](https://img.shields.io/github/last-commit/jaredcasarez/trax) ![GitHub](https://img.shields.io/github/license/jaredcasarez/trax)

A Python module for track design and management with 3D visualization, built with the <img alt="Panda3D" src="readme/panda3d_logo.png" width="20" height="20"> Panda3D Framework

> Track models supplied by Michal Fanta on Printables (under the [Creative Commons Attribution-NonCommercial License](https://creativecommons.org/licenses/by-nc/4.0/))
> 
> > [Brio tracks](https://www.printables.com/model/117903-extended-set-of-wooden-train-track-with-50-unique)
> >
> > [City Streets](https://www.printables.com/model/641763-city-streets-build-your-city-network-with-30-uniqu)

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
        ├── brio/         # Brio track pieces
        │   ├── Straight/    # Straight track pieces
        │   ├── Curved/      # Curved track pieces
        │   ├── Elevated/    # Elevated/bridge tracks
        │   ├── Crossing/    # Track crossings
        │   └── Switches/    # Track switches
        └── citystreets/     # City street pieces
            ├── Straight/    # Straight street pieces
            ├── Curved/      # Curved street pieces
            ├── Rail/        # Railway/street pieces
            ├── Crossing/    # Street crossings
            └── Roundabout/  # Street roundabout pieces
└── main.py           # Main application entry point
```

## Installation

```bash
git clone https://github.com/jaredcasarez/trax
pip install ./trax
```

## Usage

In the terminal (in a new session, if just installed), run:
```bash
trax
```

## Requirements

- Python 3.7+
- Panda3D (for 3D graphics and physics)
- panda3d-simplepbr (lighting and rendering)