from dataclasses import dataclass
import random

@dataclass
class Particle:
    position_x: float
    position_y: float
    velocity_x: float
    velocity_y: float
    particle_type: int
    color: str
    
    def get_position(self) -> tuple[float, float]:
        return self.position_x, self.position_y
    
    def apply_force(self, force_x: float, force_y: float):
        """Changes it's velocity depending on the distance"""
        self.velocity_x += force_x
        self.velocity_y += force_y
    
    def update_position(self, dt: float, friction: float, max_velocity: float, random_motion: float):
        """Updates the position"""
        # Applying friction
        self.velocity_x *= (1.0 - friction)
        self.velocity_y *= (1.0 - friction)
        
        # Edding randomness
        uniform = random.uniform
        self.velocity_x += uniform(-random_motion, random_motion)
        self.velocity_y += uniform(-random_motion, random_motion)
        
        # Limit or maximum speed
        speed_squared = self.velocity_x**2 + self.velocity_y**2
        if speed_squared > max_velocity**2:
            scale = max_velocity / (speed_squared**0.5)
            self.velocity_x *= scale
            self.velocity_y *= scale
        
        # Update the position
        self.position_x += self.velocity_x * dt
        self.position_y += self.velocity_y * dt