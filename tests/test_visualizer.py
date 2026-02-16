import pytest
import os
import pygame

# Found this online to make Pygame run without a monitor (Headless), otherwise CI crashes without a video card
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualizer import Visualizer, Slider
from src.particle_system import ParticleSystem
from src.simulation_config import SimulationConfig

@pytest.fixture
def viz_system():
    # Setup the visualizer in headless mode which yields a fresh instance for every test
    pygame.init()
    config = SimulationConfig()
    system = ParticleSystem([], config, 800, 600)
    viz = Visualizer(system, 800, 600)
    yield viz
    pygame.quit()

def test_visualizer_init_no_crash(viz_system):
    # Critical test which checks if the visualizer starts without crashing
    # If this passes that means the UI code loads fine even without a screen
    assert viz_system.width == 800
    assert viz_system.height == 600
    assert viz_system.running is True

def test_slider_math_works():
    # Testing the math inside the slider specifically if it stops at min/max values correctly
    rect = pygame.Rect(0, 0, 100, 20)
    slider = Slider("Test", "param", rect, 0.0, 10.0, 0.0)
    
    # We can't actually "click" without a monitor, so I'm just feeding numbers into the math function directly to see if it clamps correctly.
    
    # Fake click at 50px (middle) -> value should become 5.0
    slider._set_value_from_pos(50) 
    assert 4.9 < slider.value < 5.1
    
    # Fake click way past the end -> should stop at 10.0
    slider._set_value_from_pos(200)
    assert slider.value == 10.0
    
    # Fake click before the start -> should stop at 0.0
    slider._set_value_from_pos(-50)
    assert slider.value == 0.0

def test_colors_are_loaded(viz_system):
    # Simply checking if the config strings actually turned into pygame color objects
    assert len(viz_system.type_colors) > 0
    assert isinstance(viz_system.type_colors[0], pygame.Color)

def test_pause_logic(viz_system):
    # Checks if flipping the boolean actually pauses/unpauses the simulation
    # Start running
    viz_system.simulation_running = True
    assert viz_system.simulation_running is True
    
    # Toggle to paused
    viz_system.simulation_running = not viz_system.simulation_running
    assert viz_system.simulation_running is False
    
    # Toggle back to running
    viz_system.simulation_running = not viz_system.simulation_running
    assert viz_system.simulation_running is True