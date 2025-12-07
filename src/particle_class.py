##particle class
from dataclasses import dataclass
@dataclass
class Particle:
    position_x: float
    position_y: float
    velocity_x: float
    velocity_y: float
    particle_type: int
    color: str
    mass : float
    ###Returns current position as tuple from called particle
    def get_position(self) -> tuple[float,float]:
        return self.position_x, self.position_y
    ###Need to define actual physics here but I will write a short DUMMY
    def apply_force(self,force_x:float, force_y: float, dt):
        self.velocity_x += (force_x / self.mass) * dt
        self.velocity_y += (force_y/ self.mass) * dt
    ###Updates position based on velocity and time passed
    def update_position(self,dt):
        self.position_x = self.position_x + (self.velocity_x * dt)
        self.position_y = self.position_y + (self.velocity_y * dt)