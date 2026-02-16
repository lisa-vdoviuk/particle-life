import pytest
from src.simulation_config import SimulationConfig


@pytest.mark.parametrize("value", [100,5,-1,-5,-100]) ###Tests for various numbers out of range if it does raise the error its supposed to
def test_validate_type_index_error(value):
    simconfig = SimulationConfig()
    with pytest.raises(IndexError):
        simconfig._validate_type_index(value)



@pytest.mark.parametrize("value1,value2", [             
    (2, 3),
    (1, 2),])                           
def test_get_interaction(value1, value2):           ###Tests if actually a Float is returned from get_interaction with different types
    simconfig = SimulationConfig()
    value = simconfig.get_interaction(value1, value2)
    assert isinstance(value, float)


def test_set_interaction_valid_input():
    simconfig = SimulationConfig()
    simconfig.set_interaction(1,2,0.75)
    assert simconfig.get_interaction(1,2) == pytest.approx(0.75)

def test_set_interaction_invalid_input():
    simconfig = SimulationConfig()              ###Test if Index Error is raised when invalid type is entered
    with pytest.raises(IndexError):
        simconfig.set_interaction(-2,-5,0.75)


@pytest.mark.parametrize("type1,type2,value",
                         [(0,0,3),
                          (1,3,3),
                          (1,0,3)  
                         ])
def test_set_interaction_limit_testing(type1,type2,value):
    simconfig = SimulationConfig()
    simconfig.set_interaction(type1,type2, value)
    assert simconfig.get_interaction(type1,type2) == pytest.approx(value) ##Tests Index Limits and if the Function behaves the same with limit situations

def test_update_parameter_error_raising():
    simconfig = SimulationConfig()
    with pytest.raises(ValueError):
         simconfig.update_parameter("num_types", 2)       ##Tests if Value Error works correctly in these sitatuions
    with pytest.raises(ValueError):
        simconfig.update_parameter("lalala", 3)

# Adding valid and successful cases for testing to increage coverage percentage
def test_update_parameter_success():
    simconfig = SimulationConfig()

    simconfig.update_parameter("friction", 0.05)
    assert simconfig.friction == pytest.approx(0.05)

    simconfig.update_parameter("interaction_radius", 123.0)
    assert simconfig.interaction_radius == pytest.approx(123.0)

    simconfig.update_parameter("random_motion", 0.12)
    assert simconfig.random_motion == pytest.approx(0.12)

    simconfig.update_parameter("max_velocity", 9.0)
    assert simconfig.max_velocity == pytest.approx(9.0)

@pytest.mark.parametrize("idx", [0, 1, 2, 3])
def test_validate_type_index_ok(idx):
    simconfig = SimulationConfig()
    simconfig._validate_type_index(idx)  # no exception

def test_randomize_interactions_changes_values(monkeypatch):
    simconfig = SimulationConfig()

    import random
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.42)

    simconfig.randomize_interactions()

    assert simconfig.get_interaction(0, 0) == pytest.approx(0.42)
    assert simconfig.get_interaction(1, 2) == pytest.approx(0.42)

# Cover safe_config() / load_config() using temporary path
def test_save_and_load_config_roundtrip(tmp_path):
    cfg = SimulationConfig()
    cfg.friction = 0.07
    cfg.random_motion = 0.11
    cfg.set_interaction(1, 2, 0.9)

    path = tmp_path / "preset.json"
    cfg.save_config(str(path))

    loaded = SimulationConfig.load_config(str(path))

    assert loaded.friction == pytest.approx(0.07)
    assert loaded.random_motion == pytest.approx(0.11)
    assert loaded.get_interaction(1, 2) == pytest.approx(0.9)
    assert loaded.num_types == cfg.num_types

# Invalid configuration file
def test_load_config_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")

    with pytest.raises(Exception):
        SimulationConfig.load_config(str(bad))



