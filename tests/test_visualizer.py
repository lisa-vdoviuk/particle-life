import pytest
import os
import pygame

# Found this online to make Pygame run without a monitor (Headless), otherwise CI crashes without a video card
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualizer import Visualizer, Slider
from src.particle_system import ParticleSystem
from src.simulation_config import SimulationConfig
from src.particle_class import Particle

@pytest.fixture
def viz_system():
    pygame.init()
    config = SimulationConfig()
    system = ParticleSystem([], config, 800, 600)
    viz = Visualizer(system, 800, 600)
    yield viz
    pygame.quit()

def test_visualizer_init_no_crash(viz_system):
    # Just checks if UI loads without errors
    assert viz_system.width == 800
    assert viz_system.height == 600
    assert viz_system.running is True

def test_slider_math_works():
    rect = pygame.Rect(0, 0, 100, 20)
    slider = Slider("Test", "param", rect, 0.0, 10.0, 0.0)
        
    # Manually calling the internal function to test clamping logic
    
    # Middle click (50px) -> 5.0
    slider._set_value_from_pos(50) 
    assert 4.9 < slider.value < 5.1
    
    # Past max -> 10.0
    slider._set_value_from_pos(200)
    assert slider.value == 10.0
    
    # Below min -> 0.0
    slider._set_value_from_pos(-50)
    assert slider.value == 0.0

def test_colors_are_loaded(viz_system):
    assert len(viz_system.type_colors) > 0
    assert isinstance(viz_system.type_colors[0], pygame.Color)

def test_pause_logic(viz_system):
    viz_system.simulation_running = True
    assert viz_system.simulation_running is True
    
    # Toggle off
    viz_system.simulation_running = not viz_system.simulation_running
    assert viz_system.simulation_running is False
    
    # Toggle on
    viz_system.simulation_running = not viz_system.simulation_running
    assert viz_system.simulation_running is True

def test_particle_selection(viz_system):
    # Tests the closest particle math
    p = Particle(100.0, 100.0, 0.0, 0.0, 0, "red")
    viz_system.system.particles.append(p)
    
    # Clicks near particle (105, 105)
    viz_system._select_particle_at((105, 105))
    assert viz_system.selected_particle == p

def test_reset_logic(viz_system):
    viz_system.initial_particle_count = 5
    viz_system.system.add_particles(5, [0])
    
    # Adds extra particles manually to mess up count
    viz_system.system.add_particles(15, [0])
    assert len(viz_system.system.particles) == 20
    
    # Checks if reset fixes it
    viz_system._reset_particles()
    assert len(viz_system.system.particles) == 5

def test_matrix_cell_selection(viz_system):
    # Tests coordinate mapping for the heatmap
    viz_system.heatmap_open = True
    start_x, start_y = viz_system.matrix_origin
    
    # Simulates click inside first cell (0,0)
    click_x = viz_system.panel_rect.x + start_x + 10
    click_y = viz_system.panel_rect.y + start_y + 10
    
    viz_system._handle_mouse_click((click_x, click_y))
    assert viz_system.selected_cell == (0, 0)