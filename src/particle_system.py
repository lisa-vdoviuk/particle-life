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

            # keep particles inside the simulation area (wrap-around)
            particle.position_x %= self.width
            particle.position_y %= self.height

    
    def calculate_forces(self):
        """Calculates the forces between all the particles (optimized)."""
        particles = self.particles
        get_interaction = self.config.get_interaction
        interaction_radius = self.config.interaction_radius
        radius_squared = interaction_radius * interaction_radius

        for i in particles:
            # локальні змінні для меншої кількості звернень до атрибутів
            xi = i.position_x
            yi = i.position_y
            ti = i.particle_type

            force_x = 0.0
            force_y = 0.0

            for j in particles:
                if j is i:
                    continue

                k = get_interaction(ti, j.particle_type)
                if abs(k) < 0.001:
                    continue

                dx = j.position_x - xi
                dy = j.position_y - yi
                dist_squared = dx * dx + dy * dy

                # відсікаємо дуже близькі та занадто далекі пари без sqrt
                if dist_squared < 1e-6 or dist_squared > radius_squared:
                    continue

                dist = math.sqrt(dist_squared)

                dir_x = dx / dist
                dir_y = dy / dist

                linear_decay = 1.0 - (dist / interaction_radius)
                strength = k * linear_decay

                force_x += dir_x * strength
                force_y += dir_y * strength

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