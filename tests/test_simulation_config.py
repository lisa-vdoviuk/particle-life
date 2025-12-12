import pytest
from simulation_config import SimulationConfig

def test_validate_type_index_negative():
    simconfig = SimulationConfig()
    with pytest.raises(IndexError):
        simconfig._validate_type_index(-1)

