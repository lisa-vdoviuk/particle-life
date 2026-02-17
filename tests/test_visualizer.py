import pytest
import os
import pygame

# Found this fix online: headless mode prevents CI crash (no video device)
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.visualizer import Visualizer, Slider
from src.particle_system import ParticleSystem
from src.simulation_config import SimulationConfig
from src.particle_class import Particle

@pytest.fixture
def viz_system():
    """Sets up a headless Visualizer instance for each test."""
    pygame.init()
    config = SimulationConfig()
    system = ParticleSystem([], config, 800, 600)
    viz = Visualizer(system, 800, 600)
    yield viz
    pygame.quit()

def test_visualizer_init_no_crash(viz_system):
    """Checks if the UI loads without errors in a headless environment."""
    assert viz_system.width == 800
    assert viz_system.height == 600
    assert viz_system.running is True

def test_slider_math_works():
    """Verifies the min/max clamping logic inside the Slider class."""
    rect = pygame.Rect(0, 0, 100, 20)
    slider = Slider("Test", "param", rect, 0.0, 10.0, 0.0)
    
    # Manually calling the internal function to test clamping logic
    slider._set_value_from_pos(50) 
    assert 4.9 < slider.value < 5.1
    
    slider._set_value_from_pos(200)
    assert slider.value == 10.0
    
    slider._set_value_from_pos(-50)
    assert slider.value == 0.0

def test_colors_are_loaded(viz_system):
    """Ensures that string color names are converted to Pygame Color objects."""
    assert len(viz_system.type_colors) > 0
    assert isinstance(viz_system.type_colors[0], pygame.Color)

def test_pause_logic(viz_system):
    """Tests that the simulation_running boolean can be toggled correctly."""
    viz_system.simulation_running = True
    
    viz_system.simulation_running = not viz_system.simulation_running
    assert viz_system.simulation_running is False
    
    viz_system.simulation_running = not viz_system.simulation_running
    assert viz_system.simulation_running is True

def test_particle_selection(viz_system):
    """Tests the math that identifies which particle is closest to a mouse click."""
    p = Particle(100.0, 100.0, 0.0, 0.0, 0, "red")
    viz_system.system.particles.append(p)
    
    viz_system._select_particle_at((105, 105))
    assert viz_system.selected_particle == p

def test_reset_logic(viz_system):
    """Ensures that the reset function restores the initial particle count."""
    viz_system.initial_particle_count = 5
    viz_system.system.add_particles(5, [0])
    
    # Add extra particles to mess up count
    viz_system.system.add_particles(15, [0])
    assert len(viz_system.system.particles) == 20
    
    viz_system._reset_particles()
    assert len(viz_system.system.particles) == 5

def test_matrix_cell_selection(viz_system):
    """Tests the coordinate mapping logic for the heatmap."""
    viz_system.heatmap_open = True
    start_x, start_y = viz_system.matrix_origin
    
    # Simulate a click inside the first cell (0,0)
    click_x = viz_system.panel_rect.x + start_x + 10
    click_y = viz_system.panel_rect.y + start_y + 10
    
    viz_system._handle_mouse_click((click_x, click_y))
    assert viz_system.selected_cell == (0, 0)

def test_draw_methods(viz_system, monkeypatch):
    """Smoke test to ensure draw methods run without crashing in all UI states."""
    
    # We replace Pygame's drawing tools with fakes that do nothing.
    monkeypatch.setattr(pygame.draw, "circle", lambda *args, **kwargs: None)
    monkeypatch.setattr(pygame.draw, "rect", lambda *args, **kwargs: None)
    monkeypatch.setattr(pygame.display, "flip", lambda *args, **kwargs: None)
    
    # I tried patching blit but Pygame says it's read only. 
    # It seems to work fine without the patch anyway.

    try:
        # 1. Test normal drawing
        viz_system._draw()
        
        # 2. Test drawing with a particl selected
        viz_system.selected_particle = Particle(100, 100, 0, 0, 0, "red")
        viz_system._draw()
        
        # 3. Test drawing with the matrix heatmap open
        viz_system.heatmap_open = True
        viz_system._draw()
        
        # 4. Test drawing when the panel is collapsed
        viz_system.panel_collapsed = True
        viz_system._draw()
        
    except Exception as e:
        pytest.fail(f"Draw logic crashed: {e}")

def test_resize_event(viz_system):
    """Verifies that surfaces are recreated when the window is resized."""
    new_w, new_h = 1000, 800
    event = pygame.event.Event(pygame.VIDEORESIZE, size=(new_w, new_h), w=new_w, h=new_h)
    pygame.event.post(event)
    
    viz_system._handle_events()
    
    assert viz_system.width == 1000
    assert viz_system.height == 800