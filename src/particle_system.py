from particle_class import Particle
from simulation_config import SimulationConfig
from typing import List, Dict, Any, Sequence
import random
import math
from dataclasses import dataclass

@dataclass
class ParticleSystem:
    particles: List[Particle]
    config: SimulationConfig
    width: int
    height: int
    
    def add_particles(self, count: int, types: List[int]):
        for i in range(count):
           #random position inside simulation bounds
           particle_type = random.choice(types)
           #random height and width
           x = random.randint(0,self.width)
           y = random.randint(0,self.height)
           #starting velocity (set to 1 for visible movement in console)
           vx = 1
           vy = 1
           #color 
           color = self.config.particle_colors[particle_type]
           #creates the particle
           p = Particle(
               particle_type = particle_type,
               position_x = x,
               position_y = y,
               velocity_x = vx,
               velocity_y = vy,
               color = color
           )
           #adds the particle to the list
           self.particles.append(p)

    def update_system(self, dt:float):
        #calculate forces for all particles and update their velocities
        self.calculate_forces()
        #updates the positions
        for particle in self.particles:
            particle.update_position(dt)

        
    def calculate_forces(self):
        for i in self.particles:
            force_x = 0.0
            force_y = 0.0
            for j in self.particles:
                if j == i:
                    continue
                type_i = i.particle_type
                type_j = j.particle_type
                #calculates the vectors (x -> left or right, y -> up or down)
                dx = j.position_x- i.position_x
                dy = j.position_y - i.position_y
                #calculates the distance between the particles
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 0.001:
                    continue
                #calculates the direction vectors
                dir_x = dx / dist
                dir_y = dy / dist
                #coefficient from the interaction matrix
                k = self.config.get_interaction(type_i, type_j)
                #no actions -> continue
                if k == 0:
                    continue
                #calculates the strenght(without the direction)
                strength = k / dist
                #calculates the general force
                force_x += dir_x * strength
                force_y += dir_y * strength
            i.apply_force(force_x, force_y)   

    def get_particles_data(self) -> List[dict]:
        #creates the empty list for the parictles data
        result = []
        for i in self.particles:
            #creates the dict for every particle
            particle_data = {
                "x": i.position_x,
                "y": i.position_y,
                "vx": i.velocity_x,
                "vy": i.velocity_y,
                "type": i.particle_type,
                "color": i.color
            }
            #adds the particle data to the list
            result.append(particle_data)
        return result
        
    def reset_system(self):
        #clears all particles from the system
        self.particles.clear()