from simulation_config import SimulationConfig
from particle_system import ParticleSystem
import time

# Time step for visualization
dt = 0.1
config = SimulationConfig()

# Random interactions for testing
config.randomize_interactions()

# Simulation area
system = ParticleSystem(
    particles=[],
    config=config,
    width=800,
    height=600,
)

# Particles types [0,1,2,3]
types = list(range(config.num_types))

# Create 100 particles with ramdon types and positions
system.add_particles(count=100, types=types)

print("=== Particle Life Simulation ===")
print(f"Particle types: {config.num_types}")
print(f"Interaction radius: {config.interaction_radius}")
print(f"Friction: {config.friction}")
print(f"Max velocity: {config.max_velocity}")
print(f"Random motion: {config.random_motion}")

print("\nInteraction matrix (type i → type j):")
for i in range(config.num_types):
    row = []
    for j in range(config.num_types):
        row.append(f"{config.get_interaction(i, j):.2f}")
    print(f"Type {i}: {row}")

print("\nSimulation running... (Ctrl+C to stop)")
frame = 0
try:
    while True:
        system.update_system(dt)
        frame += 1
        
        if frame % 10 == 0:  # 10 FPS
            data = system.get_particles_data()
            print(f"\n--- Frame {frame} ---")
            print(f"Total particles: {len(data)}")
            # Statistics by types
            type_count = {}
            for p in data:
                t = p['type']
                type_count[t] = type_count.get(t, 0) + 1
            print(f"Particles per type: {type_count}")
            
            # First two particles for an example
            for i, p in enumerate(data[:2]):
                print(f"Particle {i}: Type={p['type']}, Pos=({p['x']:.1f}, {p['y']:.1f}), Vel=({p['vx']:.2f}, {p['vy']:.2f})")
        
        time.sleep(0.05)  # Speed of output

except KeyboardInterrupt:
    print("\n\nSimulation stopped.")