# API Reference

## Class: Himpunan

The `Himpunan` class is the core class of Set_Function, providing a complete implementation of mathematical set operations.

### Constructor

#### `Himpunan(iterable=None)`

Creates a new Himpunan (set) object.

**Parameters:**
- `iterable` (optional): Any iterable object (list, tuple, string, etc.) to initialize the set. Duplicates will be automatically removed.

**Examples:**
```python
# Empty set
h1 = Himpunan()

# From list
h2 = Himpunan([1, 2, 3])

# From string
h3 = Himpunan("hello")  # {'h', 'e', 'l', 'o'}

# Duplicates removed
h4 = Himpunan([1, 1, 2, 2])  # {1, 2}
```

### Properties

#### `elems`
The underlying set of elements. Direct access to Python's built-in set object.

### Magic Methods

#### `__repr__()`
Returns a string representation of the set.

**Returns:** String in format `Himpunan({element1, element2, ...})`

#### `__len__()`
Returns the number of elements in the set.

**Returns:** Integer representing set cardinality

**Example:**
```python
h = Himpunan([1, 2, 3])
print(len(h))  # 3
```

#### `__contains__(item)`
Tests membership of an element in the set.

**Parameters:**
- `item`: Element to test for membership

**Returns:** Boolean indicating if item is in the set

**Example:**
```python
h = Himpunan([1, 2, 3])
print(3 in h)  # True
print(4 in h)  # False
```

#### `__eq__(other)`
Tests equality between two sets.

**Parameters:**
- `other`: Another Himpunan object to compare with

**Returns:** Boolean indicating if sets contain the same elements

#### `__hash__()`
Returns a hash value for the set, making it hashable and usable in other sets or as dictionary keys.

### Set Relationship Operations

#### `__le__(other)` (<=)
Tests if this set is a subset of another set.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** Boolean - True if all elements of this set are in the other set

#### `__lt__(other)` (<)
Tests if this set is a proper subset of another set.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** Boolean - True if this set is a subset and not equal to the other set

#### `__ge__(other)` (>=)
Tests if this set is a superset of another set.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** Boolean - True if this set contains all elements of the other set

#### `__gt__(other)` (>)
Tests if this set is a proper superset of another set.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** Boolean - True if this set is a superset and not equal to the other set

#### `__floordiv__(other)` (//)
Alternative equality test.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** Boolean indicating if sets are equal

### Set Operations

#### `__add__(other)` (+)
Union operation - returns a new set containing all elements from both sets.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** New Himpunan containing union of both sets

**Raises:** `TypeError` if other is not a Himpunan object

**Example:**
```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])
union = h1 + h2  # Himpunan({1, 2, 3, 4, 5})
```

#### `__truediv__(other)` (/)
Intersection operation - returns a new set containing only elements present in both sets.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** New Himpunan containing intersection of both sets

**Raises:** `TypeError` if other is not a Himpunan object

**Example:**
```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5])
intersection = h1 / h2  # Himpunan({3, 4})
```

#### `__sub__(other)` (-)
Difference operation - returns a new set containing elements in this set but not in the other.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** New Himpunan containing difference

**Raises:** `TypeError` if other is not a Himpunan object

**Example:**
```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5])
difference = h1 - h2  # Himpunan({1, 2})
```

#### `__mul__(other)` (*)
Symmetric difference operation - returns elements in either set but not in both.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** New Himpunan containing symmetric difference

**Raises:** `TypeError` if other is not a Himpunan object

**Example:**
```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])
sym_diff = h1 * h2  # Himpunan({1, 2, 4, 5})
```

#### `__pow__(other)` (**)
Cartesian product operation - returns all ordered pairs between the two sets.

**Parameters:**
- `other`: Another Himpunan object

**Returns:** New Himpunan containing tuples representing cartesian product

**Raises:** `TypeError` if other is not a Himpunan object

**Example:**
```python
h1 = Himpunan([1, 2])
h2 = Himpunan(['a', 'b'])
cartesian = h1 ** h2  # Himpunan({(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')})
```

### Element Operations

#### `__iadd__(item)` (+=)
Adds a single element to the set (in-place operation).

**Parameters:**
- `item`: Element to add to the set

**Returns:** Self (for method chaining)

**Example:**
```python
h = Himpunan([1, 2, 3])
h += 4  # h is now Himpunan({1, 2, 3, 4})
```

### Advanced Operations

#### `komplement(semesta)`
Returns the complement of this set with respect to a universal set.

**Parameters:**
- `semesta`: A Himpunan object representing the universal set

**Returns:** New Himpunan containing elements in the universal set but not in this set

**Example:**
```python
universal = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])
subset = Himpunan([1, 2, 3, 4])
complement = subset.komplement(universal)  # Himpunan({5, 6, 7, 8, 9})
```

#### `__abs__()` (abs())
Returns the power set - a set containing all possible subsets.

**Returns:** Himpunan containing all subsets as Himpunan objects

**Example:**
```python
h = Himpunan([1, 2, 3])
power_set = abs(h)  # Contains 8 subsets (2^3)
```

#### `ListKuasa()`
Helper method that returns the power set as a list of Himpunan objects.

**Returns:** List of Himpunan objects representing all subsets

**Example:**
```python
h = Himpunan([1, 2])
subsets = h.ListKuasa()  # [Himpunan({}), Himpunan({1}), Himpunan({2}), Himpunan({1, 2})]
```

## Operator Summary Table

| Python Operator | Mathematical Operation | Method | Description |
|------------------|------------------------|---------|-------------|
| `+` | ∪ (Union) | `__add__` | A ∪ B - elements in A or B |
| `/` | ∩ (Intersection) | `__truediv__` | A ∩ B - elements in both A and B |
| `-` | \ (Difference) | `__sub__` | A \ B - elements in A but not B |
| `*` | △ (Symmetric Difference) | `__mul__` | A △ B - elements in A or B but not both |
| `**` | × (Cartesian Product) | `__pow__` | A × B - all ordered pairs (a,b) |
| `<=` | ⊆ (Subset) | `__le__` | A ⊆ B - A is subset of B |
| `<` | ⊂ (Proper Subset) | `__lt__` | A ⊂ B - A is proper subset of B |
| `>=` | ⊇ (Superset) | `__ge__` | A ⊇ B - A is superset of B |
| `>` | ⊃ (Proper Superset) | `__gt__` | A ⊃ B - A is proper superset of B |
| `==` | = (Equality) | `__eq__` | A = B - A equals B |
| `//` | = (Equality) | `__floordiv__` | A = B - alternative equality |
| `+=` | Add Element | `__iadd__` | Add single element to set |
| `abs()` | 𝒫 (Power Set) | `__abs__` | 𝒫(A) - all subsets of A |
| `in` | ∈ (Membership) | `__contains__` | a ∈ A - a is element of A |
| `len()` | \|A\| (Cardinality) | `__len__` | \|A\| - number of elements in A |

## Error Handling

All binary operations (`+`, `/`, `-`, `*`, `**`) will raise a `TypeError` with the message "Operasi hanya bisa dilakukan antar Himpunan" if the operand is not a Himpunan object.

## Type Hints

For better IDE support and type checking, consider using type hints:

```python
from typing import Any, Iterator
from set_function.set_function import Himpunan

def process_sets(set1: Himpunan, set2: Himpunan) -> Himpunan:
    return set1 + set2

def create_set_from_list(items: list[Any]) -> Himpunan:
    return Himpunan(items)
```