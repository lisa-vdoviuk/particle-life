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