#!/usr/bin/env python
import pytest

"""Tests for `set_function` package."""

from set_function.set_function import Himpunan


@pytest.fixture
def sample_sets():
    """Sample pytest fixture with test sets."""
    S = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])
    h1 = Himpunan([1, 2, 3])
    h2 = Himpunan([3, 4, 5])
    return S, h1, h2


def test_himpunan_creation():
    """Test Himpunan creation and basic properties."""
    h = Himpunan([1, 2, 3, 3, 2]) 
    assert len(h) == 3
    assert 1 in h
    assert 2 in h
    assert 3 in h
    assert 4 not in h


def test_himpunan_length(sample_sets):
    """Test length operation."""
    S, h1, h2 = sample_sets
    assert len(h1) == 3
    assert len(h2) == 3
    assert len(S) == 9


def test_himpunan_membership(sample_sets):
    """Test membership operation."""
    S, h1, h2 = sample_sets
    assert 3 in h1
    assert 3 in h2
    assert 1 in h1
    assert 1 not in h2
    assert 5 in h2
    assert 5 not in h1


def test_himpunan_equality(sample_sets):
    """Test equality operation."""
    S, h1, h2 = sample_sets
    assert h1 == h1
    assert h1 != h2
    h3 = Himpunan([1, 2, 3])
    assert h1 == h3


def test_himpunan_add_element(sample_sets):
    """Test adding element to set."""
    S, h1, h2 = sample_sets
    h1_copy = Himpunan([1, 2, 3])
    h1_copy += 4  
    assert 4 in h1_copy
    assert len(h1_copy) == 4
    expected = Himpunan([1, 2, 3, 4])
    assert h1_copy == expected


def test_himpunan_intersection(sample_sets):
    """Test intersection operation (/)."""
    S, h1, h2 = sample_sets
    h1_with_4 = Himpunan([1, 2, 3, 4])
    h3 = h1_with_4 / h2  
    expected = Himpunan([3, 4])
    assert h3 == expected


def test_himpunan_union(sample_sets):
    """Test union operation (+)."""
    S, h1, h2 = sample_sets
    h1_with_4 = Himpunan([1, 2, 3, 4])
    h4 = h1_with_4 + h2  
    expected = Himpunan([1, 2, 3, 4, 5])
    assert h4 == expected


def test_himpunan_difference(sample_sets):
    """Test difference operation (-)."""
    S, h1, h2 = sample_sets
    h1_with_4 = Himpunan([1, 2, 3, 4])
    h5 = h1_with_4 - h2  
    expected = Himpunan([1, 2])
    assert h5 == expected


def test_himpunan_complement(sample_sets):
    """Test complement operation."""
    S, h1, h2 = sample_sets
    h1_with_4 = Himpunan([1, 2, 3, 4])
    h6 = h1_with_4.komplement(S) 
    expected = Himpunan([5, 6, 7, 8, 9])
    assert h6 == expected


def test_himpunan_power_set(sample_sets):
    """Test power set operation (abs)."""
    S, h1, h2 = sample_sets
    h1_with_4 = Himpunan([1, 2, 3, 4])
    power_set = abs(h1_with_4) 
    assert len(power_set) == 16  
    
    empty_set = Himpunan([])
    assert empty_set in power_set.elems
    assert h1_with_4 in power_set.elems


def test_himpunan_symmetric_difference(sample_sets):
    """Test symmetric difference operation (*)."""
    S, h1, h2 = sample_sets
    h_sym = h1 * h2 
    expected = Himpunan([1, 2, 4, 5])  
    assert h_sym == expected


def test_himpunan_cartesian_product(sample_sets):
    """Test cartesian product operation (**)."""
    h1 = Himpunan([1, 2])
    h2 = Himpunan(['a', 'b'])
    h_cart = h1 ** h2  
    expected_tuples = {(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')}
    assert h_cart.elems == expected_tuples


def test_himpunan_subset_operations():
    """Test subset and superset operations."""
    h1 = Himpunan([1, 2])
    h2 = Himpunan([1, 2, 3])
    
    assert h1 <= h2 
    assert h1 < h2   
    assert h2 >= h1  
    assert not (h2 <= h1) 


def test_himpunan_type_errors():
    """Test type error handling."""
    h = Himpunan([1, 2, 3])
    
    with pytest.raises(TypeError):
        h + 5  # Should raise error when trying to union with non-Himpunan
    
    with pytest.raises(TypeError):
        h / 5  # Should raise error when trying to intersect with non-Himpunan
    
    with pytest.raises(TypeError):
        h - 5  # Should raise error when trying to difference with non-Himpunan
    
    with pytest.raises(TypeError):
        h * 5  # Should raise error when trying to symmetric difference with non-Himpunan
