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
        self.calculate_forces()
        for particle in self.particles:
            particle.update_position(
                dt,
                self.config.friction,
                self.config.max_velocity,
                self.config.random_motion
            )
    
    def calculate_forces(self):
        """Calculates the forces between all the particles"""
        for i in self.particles:
            force_x = 0.0
            force_y = 0.0
            
            for j in self.particles:
                if j is i: # skip itself
                    continue
                
                # Value from interaction matrix
                k = self.config.get_interaction(i.particle_type, j.particle_type)
                if abs(k) < 0.001:
                    continue
                
                # Calculation of direction and distance
                dx = j.position_x - i.position_x
                dy = j.position_y - i.position_y
                dist_squared = dx*dx + dy*dy
                dist = math.sqrt(dist_squared)
                
                
                if dist > self.config.interaction_radius:
                    continue
                
                if dist < 0.001:  # Avoid dividing by zero
                    continue
                
                
                dir_x = dx / dist
                dir_y = dy / dist
                
                # MY OFFER OF THE FORMULA:
                # Force = interaction_matrix_value × linear_decay_with_distance
                # Linear_decay: 1 - (dist / interaction_radius)
                linear_decay = 1.0 - (dist / self.config.interaction_radius)
                strength = k * linear_decay
                
                # Add the force
                force_x += dir_x * strength
                force_y += dir_y * strength
            
            # Apply the force for a particle
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