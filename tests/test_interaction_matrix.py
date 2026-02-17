import pytest
from src.interaction_matrix import InteractionMatrix

@pytest.fixture
def matrix():
    """Returns a basic 3x3 InteractionMatrix instance for testing."""
    return InteractionMatrix(3)

def test_matrix_starts_at_zero(matrix):
    """Verifies that a new matrix is initialized with all interaction values at 0.0."""
    assert matrix.num_types == 3
    for i in range(3):
        for j in range(3):
            assert matrix.get_interaction(i, j) == 0.0

def test_set_and_get_values(matrix):
    """Tests if manually set interaction forces can be read back correctly."""
    matrix.set_interaction(0, 1, 0.5)
    matrix.set_interaction(2, 2, -0.8)
    
    assert matrix.get_interaction(0, 1) == 0.5
    assert matrix.get_interaction(2, 2) == -0.8

def test_invalid_index_safety(matrix):
    """Checks that the matrix safely ignores indices that are too high."""
    # This shouldn't crash or change anything
    matrix.set_interaction(50, 50, 1.0) 
    assert matrix.get_interaction(50, 50) == 0.0

def test_negative_index_safety(matrix):
    """Ensures that negative indices are treated as invalid instead of list-wrapping."""
    matrix.set_interaction(-1, 0, 0.5)
    assert matrix.get_interaction(-1, 0) == 0.0

def test_randomize_logic(matrix):
    """Verifies that randomize() generates values within the valid [-1.0, 1.0] range."""
    matrix.randomize()
    
    has_changed = False
    for i in range(matrix.num_types):
        for j in range(matrix.num_types):
            val = matrix.get_interaction(i, j)
            
            # Must be in the valid force range
            assert -1.0 <= val <= 1.0
            
            # If at least one value isn't 0 it means it actually randomized
            if val != 0.0:
                has_changed = True
                
    assert has_changed is True