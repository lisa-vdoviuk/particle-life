from particle_class import Particle
from simulation_config import SimulationConfig
from typing import List, Dict
import random
import math

class ParticleSystem:
    def __init__(self, particles: List[Particle], config: SimulationConfig, width: int, height: int):
        self.particles = particles
        self.config = config
        self.width = width
        self.height = height
        self._force_frame = 0
        self._grid = {}
    
    def add_particles(self, count: int, types: List[int]):
        """Adds particles with positions and types"""
        for _ in range(count):
            particle_type = random.choice(types)
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            
            # Minimum starting velocity
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(-0.5, 0.5)
            
            color = self.config.particle_colors[particle_type]
            
            p = Particle(
                particle_type=particle_type,
                position_x=x,
                position_y=y,
                velocity_x=vx,
                velocity_y=vy,
                color=color
            )
            self.particles.append(p)
    
    def update_system(self, dt: float):
        """Updated the whole system"""
        self._force_frame += 1
        r = self.config.interaction_radius
        every = 3 if r <= 50 else (5 if r <= 100 else 6)
        if self._force_frame % every == 0:
            self.calculate_forces()
        friction = self.config.friction
        max_v = self.config.max_velocity
        rnd_m = self.config.random_motion
        w = self.width
        h = self.height
        change = 4
        rnd_change = rnd_m if (self._force_frame % change == 0) else 0.0
        for particle in self.particles:
            particle.update_position(
                dt,
                friction,
                max_v,
                rnd_change
            )
            
            # keep particles inside the simulation area (wrap-around)
            particle.position_x %= self.width
            particle.position_y %= self.height

    
    def calculate_forces(self):
        """Calculates the forces between all the particles using a uniform grid (spatial hashing)."""
        particles = self.particles
        config = self.config
        # locals for the faster optimisation
        sqrt = math.sqrt
        interaction_matrix = config.interaction_matrix.matrix
        
        #interaction radius (distance)
        r = float(config.interaction_radius)
        if r <= 0.0:
            return
        
        radius_squared = r * r # compare squared distances to avoid sqrt when possible
        inv_r = 1.0 / r # precompute the inverse of interaction radius for the optimisation

        #we use cell size as r so we only check the currenct cell all the neighbor cells
        cell_size = r
        inv_cell = 1.0 / cell_size # precompute the inverse cell for the optimisation
        cell_range = 1 # checks 1 cell away, -> 3x3 blocks(currecnt cell + 8 neighbor cells)

        # creates the dict with all the particales cells location
        grid = self._grid
        grid.clear()
        # grid keeps particles
        for p in particles:
            cx = int(p.position_x * inv_cell)
            cy = int(p.position_y * inv_cell)
            key = (cx, cy)
            if key not in grid:
                grid[key] = []
            grid[key].append(p)
        
        # computes the forces for all the particles in the cell
        for i in particles:
            xi = i.position_x
            yi = i.position_y
            ti = i.particle_type
            
            # row in the matrix for the particle i type (faster optimisation)
            row = interaction_matrix[ti]

            force_x = 0.0
            force_y = 0.0

            # cell coordinates for particle i
            cxi = int(xi * inv_cell)
            cyi = int(yi * inv_cell)


            # checks current cells and the 8 neighboring cells
            for dx_cells in range(-cell_range, cell_range + 1):
                for dy_cells in range(-cell_range, cell_range + 1):
                    cell = grid.get((cxi + dx_cells, cyi + dy_cells))
                    if not cell:
                        continue
                    
                    # iterate particles in the neighbor cells
                    for j in cell:
                        if j is i:
                            continue # skips self
                        
                        #takes the interaction coefficient from the matrix
                        k = row[j.particle_type]
                        if k == 0.0:
                            continue # skips if no interaction

                        dx = j.position_x - xi
                        dy = j.position_y - yi
                        d_squared = dx * dx + dy * dy

                        # ignores extremly small distances (avoid division by zero)
                        # also ignores particle outside the cutoff radius
                        if d_squared < 1e-6 or d_squared > radius_squared:
                            continue
                        
                        # computes the distance and normalized direction
                        inv_d = 1.0 / sqrt(d_squared)
                        dist = d_squared * inv_d
                        
                        strength = k * (1.0 - dist * inv_r)

                        # calculate the forces(direction * strenght)
                        force_x += dx * inv_d * strength
                        force_y += dy * inv_d * strength

            i.apply_force(force_x, force_y)

    
    def get_particles_data(self) -> List[Dict]:
        """Return the data for visualization"""
        result = []
        for p in self.particles:
            particle_data = {
                "x": p.position_x,
                "y": p.position_y,
                "vx": p.velocity_x,
                "vy": p.velocity_y,
                "type": p.particle_type,
                "color": p.color
                
            }
            result.append(particle_data)
        return result
    
    def reset_system(self):
        """Resets the system"""
        self.particles.clear()