import pytest
from src.interaction_matrix import InteractionMatrix

@pytest.fixture
def matrix():
    # Just a basic 3x3 matrix for testing
    return InteractionMatrix(3)

def test_matrix_starts_at_zero(matrix):
    # Checking if the matrix is actually empty (all 0.0) when it's first created
    assert matrix.num_types == 3
    for i in range(3):
        for j in range(3):
            assert matrix.get_interaction(i, j) == 0.0

def test_set_and_get_values(matrix):
    # Testing if we can manually set forces and read them back correctly
    matrix.set_interaction(0, 1, 0.5)
    matrix.set_interaction(2, 2, -0.8)
    
    assert matrix.get_interaction(0, 1) == 0.5
    assert matrix.get_interaction(2, 2) == -0.8

def test_invalid_index_safety(matrix):
    # Testing if it safely ignores indexes that are too high
    # This shouldn't crash or change anything
    matrix.set_interaction(50, 50, 1.0) 
    assert matrix.get_interaction(50, 50) == 0.0

def test_negative_index_safety(matrix):
    # Testing that -1 is treated as an invalid index instead of wrapping
    matrix.set_interaction(-1, 0, 0.5)
    assert matrix.get_interaction(-1, 0) == 0.0

def test_randomize_logic(matrix):
    # Checking if randomize() actually puts numbers between -1 and 1
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