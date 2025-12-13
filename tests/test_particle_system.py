import pytest
import random
from simulation_config import SimulationConfig
from particle_system import ParticleSystem

@pytest.fixture
def system():
    # random.seed is used to generate the same random numbers every time
    random.seed(0)
    config = SimulationConfig()
    return ParticleSystem([], config, 100, 100)

def test_add_particles_creates_count_and_bounds(system):
    system.add_particles(5, types=[0,1])
    assert len(system.particles) == 5
    for p in system.particles:
        assert 0 <= p.position_x <= system.width
        assert 0 <= p.position_y <= system.height

def test_reset_particle_system(system):
    system.add_particles(5, types=[0,1])
    system.reset_system()
    assert len(system.particles) == 0

def test_get_particles_data(system):
    system.add_particles(5, types=[0,1])
    data = system.get_particles_data()
    assert len(data) == 5
    expected_keys = {"x", "y", "vx", "vy", "type", "color"}
    assert expected_keys.issubset(data[0].keys())


def test_update_forces(system):
    system.add_particles(2, types=[0,1])
    system.particles[0].particle_type = 1
    system.particles[1].particle_type = 0

    # place particles within interaction radius to guarantee non-zero force
    r = system.config.interaction_radius
    system.particles[0].position_x, system.particles[0].position_y = 10.0, 10.0
    system.particles[1].position_x, system.particles[1].position_y = 10.0 + 0.5 * r, 10.0
    
    system.particles[0].velocity_x = 0.0
    system.particles[0].velocity_y = 0.0
    system.particles[1].velocity_x = 0.0
    system.particles[1].velocity_y = 0.0

    system.config.set_interaction(1,0,5.0)
    # saves the 'before' velocity
    v_before = [(p.velocity_x, p.velocity_y) for p in system.particles]
    system.update_system(1.0)
    # saves the 'after' velocity
    v_after = [(p.velocity_x, p.velocity_y) for p in system.particles]
    assert v_before != v_after

