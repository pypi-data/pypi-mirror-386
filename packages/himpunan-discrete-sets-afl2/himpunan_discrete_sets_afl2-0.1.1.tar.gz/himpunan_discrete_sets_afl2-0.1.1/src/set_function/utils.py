"""Utility functions for Set_Function package."""

from typing import List, Any, Union
from set_function.set_function import Himpunan


def create_range_set(start: int, end: int, step: int = 1) -> Himpunan:
    """Create a Himpunan from a range of numbers.
    
    Args:
        start: Starting number (inclusive)
        end: Ending number (exclusive)
        step: Step size (default: 1)
        
    Returns:
        Himpunan containing the range of numbers
        
    Example:
        >>> create_range_set(1, 6)  # Creates {1, 2, 3, 4, 5}
        Himpunan({1, 2, 3, 4, 5})
    """
    return Himpunan(range(start, end, step))


def create_alphabet_set(start: str = 'a', end: str = 'z') -> Himpunan:
    """Create a Himpunan of alphabetic characters.
    
    Args:
        start: Starting character (default: 'a')
        end: Ending character (default: 'z')
        
    Returns:
        Himpunan containing alphabetic characters
        
    Example:
        >>> create_alphabet_set('a', 'f')  # Creates {'a', 'b', 'c', 'd', 'e'}
        Himpunan({'a', 'b', 'c', 'd', 'e'})
    """
    start_ord = ord(start.lower())
    end_ord = ord(end.lower())
    chars = [chr(i) for i in range(start_ord, end_ord)]
    return Himpunan(chars)


def partition_set(universal_set: Himpunan, *subsets: Himpunan) -> bool:
    """Check if the given subsets form a partition of the universal set.
    
    A partition means:
    1. All subsets are non-empty
    2. All subsets are pairwise disjoint
    3. Union of all subsets equals the universal set
    
    Args:
        universal_set: The universal set to partition
        *subsets: Variable number of Himpunan objects
        
    Returns:
        True if subsets form a partition, False otherwise
        
    Example:
        >>> universal = Himpunan([1, 2, 3, 4, 5, 6])
        >>> s1 = Himpunan([1, 2])
        >>> s2 = Himpunan([3, 4])  
        >>> s3 = Himpunan([5, 6])
        >>> partition_set(universal, s1, s2, s3)
        True
    """
    if not subsets:
        return False
    
    # Check if all subsets are non-empty
    for subset in subsets:
        if len(subset) == 0:
            return False
    
    # Check if subsets are pairwise disjoint
    for i in range(len(subsets)):
        for j in range(i + 1, len(subsets)):
            intersection = subsets[i] / subsets[j]
            if len(intersection) > 0:
                return False
    
    # Check if union equals universal set
    union = subsets[0]
    for subset in subsets[1:]:
        union = union + subset
    
    return union == universal_set


def is_disjoint(*sets: Himpunan) -> bool:
    """Check if all given sets are pairwise disjoint.
    
    Args:
        *sets: Variable number of Himpunan objects
        
    Returns:
        True if all sets are pairwise disjoint, False otherwise
        
    Example:
        >>> s1 = Himpunan([1, 2])
        >>> s2 = Himpunan([3, 4])
        >>> s3 = Himpunan([5, 6])
        >>> is_disjoint(s1, s2, s3)
        True
    """
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            intersection = sets[i] / sets[j]
            if len(intersection) > 0:
                return False
    return True


def venn_diagram_info(set1: Himpunan, set2: Himpunan) -> dict:
    """Get information for drawing a Venn diagram of two sets.
    
    Args:
        set1: First Himpunan
        set2: Second Himpunan
        
    Returns:
        Dictionary with regions of the Venn diagram
        
    Example:
        >>> s1 = Himpunan([1, 2, 3, 4])
        >>> s2 = Himpunan([3, 4, 5, 6])
        >>> venn_diagram_info(s1, s2)
        {
            'only_set1': Himpunan({1, 2}),
            'intersection': Himpunan({3, 4}),
            'only_set2': Himpunan({5, 6}),
            'union': Himpunan({1, 2, 3, 4, 5, 6})
        }
    """
    intersection = set1 / set2
    only_set1 = set1 - set2
    only_set2 = set2 - set1
    union = set1 + set2
    
    return {
        'only_set1': only_set1,
        'intersection': intersection,
        'only_set2': only_set2,
        'union': union,
        'symmetric_difference': set1 * set2
    }


def jaccard_similarity(set1: Himpunan, set2: Himpunan) -> float:
    """Calculate Jaccard similarity coefficient between two sets.
    
    Jaccard similarity = |A ∩ B| / |A ∪ B|
    
    Args:
        set1: First Himpunan
        set2: Second Himpunan
        
    Returns:
        Jaccard similarity coefficient (0.0 to 1.0)
        
    Example:
        >>> s1 = Himpunan([1, 2, 3, 4])
        >>> s2 = Himpunan([3, 4, 5, 6])
        >>> jaccard_similarity(s1, s2)
        0.3333333333333333
    """
    intersection = set1 / set2
    union = set1 + set2
    
    if len(union) == 0:
        return 1.0 if len(set1) == 0 and len(set2) == 0 else 0.0
    
    return len(intersection) / len(union)


def dice_coefficient(set1: Himpunan, set2: Himpunan) -> float:
    """Calculate Dice coefficient between two sets.
    
    Dice coefficient = 2 * |A ∩ B| / (|A| + |B|)
    
    Args:
        set1: First Himpunan
        set2: Second Himpunan
        
    Returns:
        Dice coefficient (0.0 to 1.0)
        
    Example:
        >>> s1 = Himpunan([1, 2, 3, 4])
        >>> s2 = Himpunan([3, 4, 5, 6])
        >>> dice_coefficient(s1, s2)
        0.5
    """
    intersection = set1 / set2
    
    if len(set1) + len(set2) == 0:
        return 1.0
    
    return (2 * len(intersection)) / (len(set1) + len(set2))


def generate_subsets_of_size(input_set: Himpunan, size: int) -> Himpunan:
    """Generate all subsets of a specific size from a set.
    
    Args:
        input_set: The input Himpunan
        size: Size of subsets to generate
        
    Returns:
        Himpunan containing all subsets of the specified size
        
    Example:
        >>> s = Himpunan([1, 2, 3, 4])
        >>> generate_subsets_of_size(s, 2)
        # Returns Himpunan containing all 2-element subsets
    """
    from itertools import combinations
    
    if size < 0 or size > len(input_set):
        return Himpunan()
    
    subsets = []
    elems_list = list(input_set.elems)
    
    for combo in combinations(elems_list, size):
        subsets.append(Himpunan(combo))
    
    return Himpunan(subsets)


def do_something_useful():
    """Legacy function - displays available utility functions."""
    print("Set_Function Utility Functions:")
    print("- create_range_set(start, end, step=1)")
    print("- create_alphabet_set(start='a', end='z')")
    print("- partition_set(universal_set, *subsets)")
    print("- is_disjoint(*sets)")
    print("- venn_diagram_info(set1, set2)")
    print("- jaccard_similarity(set1, set2)")
    print("- dice_coefficient(set1, set2)")
    print("- generate_subsets_of_size(input_set, size)")
    print("\nSee documentation for detailed usage examples.")
