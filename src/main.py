from simulation_config import SimulationConfig
from particle_system import ParticleSystem
import time

#time step for the simulation
dt = 0.1
config = SimulationConfig()

# Randomize interactions for testing
config.randomize_interactions()

# creates an 800x600 simulation area without particles
system = ParticleSystem(
    particles=[],
    config=config,
    width=800,
    height=600,
)
types = list(range(config.num_types)) # [0,1,2,3]
# creates 30 particles with random positions and types
system.add_particles(count=30, types=types)

print("Initial interaction matrix:")
for i in range(config.num_types):
    row = []
    for j in range(config.num_types):
        row.append(f"{config.get_interaction(i, j):.2f}")
    print(f"Type {i}: {row}")

while True:
    system.update_system(dt)
    data = system.get_particles_data()
    print("\n--- FRAME ---")
    for p in data[:3]:  # Show only first 3 particles
        print(f"Type: {p['type']}, Pos: ({p['x']:.1f}, {p['y']:.1f})")
    time.sleep(0.5)