# Particle Life Simulation

A real-time particle simulation demonstrating emergent behavior based on simple interaction rules between particle types.  
Developed for the course **Data Science & AI Infrastructures (WS 2025/2026)**.

## Overview

This project implements a dynamic particle system in Python where multiple particle types interact via attraction and repulsion forces defined in an interaction matrix.  
From simple local rules, complex global movement patterns emerge in real time.

The project focuses on clean architecture, configurability, and performance-aware simulation design.

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/lisa-vdoviuk/particle-life.git
cd particle-life
pip install -r requirements.txt
````

---

## Running the Simulation

Start the application:

```bash
python src/main.py
```

At launch you can:

* Load an existing JSON preset, or
* Enter a custom interaction matrix via console.

After configuration, the visualization window opens automatically.

---

## Features

* Multiple particle types with different behaviors
* Attraction/repulsion defined by an interaction matrix
* Real-time visualization using Pygame
* Adjustable simulation parameters (radius, chaos, size)
* Save/load configuration presets

---

## Project Structure

```
main.py                 # Entry point and setup
particle_class.py       # Particle data model and movement logic
particle_system.py      # Core simulation and force calculations
interaction_matrix.py   # Interaction rules between particle types
simulation_config.py    # Central configuration + JSON presets
visualizer.py           # Rendering and interactive UI
requirements.txt        # Dependencies
```

---

## Software Architecture (Developer Documentation)

The system is modular and split into clearly defined responsibilities:

**Particle**

* Stores position, velocity, type, and color
* Updates movement and applies forces

**ParticleSystem**

* Manages all particles
* Calculates forces between nearby particles
* Updates positions each frame
* Uses a grid-based approach to reduce computation cost

**InteractionMatrix**

* Defines attraction/repulsion values between particle types
* Can be randomized or configured manually

**SimulationConfig**

* Central storage for all parameters:

  * friction
  * max velocity
  * interaction radius
  * random motion
* Supports saving/loading presets as JSON

**Visualizer**

* Handles real-time rendering using Pygame
* Provides UI controls and sliders
* Allows particle inspection and system reset

---

## Simulation Logic

Each frame:

1. Forces between particles are computed based on:

   * Distance
   * Particle types
   * Interaction matrix

2. Forces update particle velocities

3. Positions are updated with:

   * Friction
   * Random motion
   * Velocity limits

4. Particles are rendered in real time

This results in emergent clustering and dynamic patterns.

---

## Developer Guide

To work on the project:

1. Create a new branch for your feature or fix
2. Keep code modular and readable
3. Add docstrings to new classes/functions
4. Test changes by running the simulation

Main extension points:

...

The configuration system allows easy experimentation by saving/loading presets.

---

## Controls

* **Space** → Pause / Resume simulation
* **Mouse click** → Select particle
* **UI panel** → Adjust parameters, reset or randomize system

---

## Team

* Yelyzaveta Vdoviuk
* Oleksii Zvirkovskyi
* Thorben Linzmaier
* Emen Fouda

---

## License

For academic use only.
