# Set_Function

![PyPI version](https://img.shields.io/pypi/v/himpunan-discrete-sets-afl2.svg)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PyPI downloads](https://img.shields.io/pypi/dm/himpunan-discrete-sets-afl2.svg)

A comprehensive Python package for mathematical set operations including union, intersection, difference, symmetric difference, complement, cartesian product, and power set operations.

* PyPI package: https://pypi.org/project/himpunan-discrete-sets-afl2/
* GitHub Repository: https://github.com/1nnocentia/set_function
* Free software: MIT License

## Features

* **Complete Set Operations**: Union, intersection, difference, symmetric difference
* **Advanced Operations**: Complement, cartesian product, power set
* **Set Relationships**: Subset, superset, equality checking
* **Element Operations**: Add elements, membership testing
* **Intuitive Syntax**: Uses Python operators for natural mathematical notation
* **Type Safety**: Built-in type checking and error handling
* **Comprehensive Testing**: Full test suite with 100% coverage

## Installation

```bash
pip install himpunan-discrete-sets-afl2
```

## Quick Start

```python
from set_function.set_function import Himpunan

# Create sets
S = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])  # Universal set
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])

# Basic operations
print(len(h1))      # Output: 3
print(3 in h1)      # Output: True
print(h1 == h2)     # Output: False
```

## Usage Examples

### Basic Set Properties

```python
from set_function.set_function import Himpunan

# Creating sets
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])

# Length and membership
print(len(h1))      # 3
print(3 in h1)      # True
print(6 in h1)      # False

# Set equality
print(h1 == h2)     # False
print(h1 == Himpunan([1, 2, 3]))  # True
```

### Adding Elements

```python
h1 = Himpunan([1, 2, 3])
h1 += 4  # Add element 4 to h1
print(h1)  # Himpunan({1, 2, 3, 4})
```

### Set Operations

#### Union (Addition: +)
```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5])
h_union = h1 + h2  # Union
print(h_union)  # Himpunan({1, 2, 3, 4, 5})
```

#### Intersection (Division: /)
```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5])
h_intersection = h1 / h2  # Intersection
print(h_intersection)  # Himpunan({3, 4})
```

#### Difference (Subtraction: -)
```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5])
h_difference = h1 - h2  # Difference
print(h_difference)  # Himpunan({1, 2})
```

#### Symmetric Difference (Multiplication: *)
```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])
h_sym_diff = h1 * h2  # Symmetric difference
print(h_sym_diff)  # Himpunan({1, 2, 4, 5})
```

### Advanced Operations

#### Complement
```python
S = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])  # Universal set
h1 = Himpunan([1, 2, 3, 4])
h_complement = h1.komplement(S)  # Complement
print(h_complement)  # Himpunan({5, 6, 7, 8, 9})
```

#### Power Set
```python
h1 = Himpunan([1, 2, 3, 4])
power_set = abs(h1)  # Power set (all subsets)
print(len(power_set))  # 16 (2^4 subsets)
```

#### Cartesian Product
```python
h1 = Himpunan([1, 2])
h2 = Himpunan(['a', 'b'])
cartesian = h1 ** h2  # Cartesian product
print(cartesian)  # Himpunan({(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')})
```

### Set Relationships

#### Subset and Superset
```python
h1 = Himpunan([1, 2])
h2 = Himpunan([1, 2, 3, 4])

print(h1 <= h2)  # True (h1 is subset of h2)
print(h1 < h2)   # True (h1 is proper subset of h2)
print(h2 >= h1)  # True (h2 is superset of h1)
print(h2 > h1)   # True (h2 is proper superset of h1)
```

#### Set Equality
```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 2, 1])  # Order doesn't matter
print(h1 // h2)  # True (sets are equal)
print(h1 == h2)  # True (alternative equality check)
```

## Complete Example

```python
from set_function.set_function import Himpunan

# Define universal set and subsets
S = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])

# Basic properties
print(f"Length of h1: {len(h1)}")        # 3
print(f"3 in h1: {3 in h1}")             # True
print(f"h1 equals h2: {h1 == h2}")       # False

# Add element
h1 += 4
print(f"h1 after adding 4: {h1}")        # {1, 2, 3, 4}

# Set operations
intersection = h1 / h2
union = h1 + h2
difference = h1 - h2
complement = h1.komplement(S)
power_set = abs(h1)

print(f"Intersection: {intersection}")     # {3, 4}
print(f"Union: {union}")                  # {1, 2, 3, 4, 5}
print(f"Difference: {difference}")        # {1, 2}
print(f"Complement: {complement}")        # {5, 6, 7, 8, 9}
print(f"Power set size: {len(power_set)}")  # 16
```

## Operator Reference

| Operation | Operator | Method | Description |
|-----------|----------|--------|-------------|
| Union | `+` | `__add__` | Elements in either set |
| Intersection | `/` | `__truediv__` | Elements in both sets |
| Difference | `-` | `__sub__` | Elements in first but not second |
| Symmetric Difference | `*` | `__mul__` | Elements in either set but not both |
| Cartesian Product | `**` | `__pow__` | All ordered pairs between sets |
| Subset | `<=` | `__le__` | First set is subset of second |
| Proper Subset | `<` | `__lt__` | First set is proper subset of second |
| Superset | `>=` | `__ge__` | First set is superset of second |
| Proper Superset | `>` | `__gt__` | First set is proper superset of second |
| Equality | `==` | `__eq__` | Sets contain same elements |
| Set Equality | `//` | `__floordiv__` | Alternative equality check |
| Add Element | `+=` | `__iadd__` | Add single element to set |
| Power Set | `abs()` | `__abs__` | All possible subsets |
| Complement | `.komplement()` | `komplement` | Elements in universal set but not in this set |

## Error Handling

The package includes comprehensive error handling:

```python
h = Himpunan([1, 2, 3])

# These will raise TypeError
try:
    result = h + 5  # Cannot union with non-Himpunan
except TypeError as e:
    print(e)  # "Operasi hanya bisa dilakukan antar Himpunan"
```

## Credits

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
