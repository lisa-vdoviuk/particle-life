from simulation_config import SimulationConfig
from particle_system import ParticleSystem
import time
#time step for the simulation
dt = 0.1
config = SimulationConfig()
# creates an 800x600 simulation area without particles
system = ParticleSystem(
    particles=[],
    config=config,
    width=800,
    height=600,
)
types = list(range(config.num_types)) # [0,1,2,3]
# creates 30 particles with random positions and types
system.add_particles(count=30,types=types)
while True:
    system.update_system(dt)
    data = system.get_particles_data()
    print("\n--- FRAME ---")
    for p in data[:5]: 
        print(p)
    time.sleep(0.5)



