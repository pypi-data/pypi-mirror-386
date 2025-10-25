# Usage Guide

## Basic Usage

To use Set_Function in a project, import the `Himpunan` class:

```python
from set_function.set_function import Himpunan
```

## Creating Sets

### Empty Set
```python
empty_set = Himpunan()
print(empty_set)  # Himpunan({})
```

### Set with Elements
```python
# From a list
h1 = Himpunan([1, 2, 3, 4])
print(h1)  # Himpunan({1, 2, 3, 4})

# From any iterable
h2 = Himpunan("hello")
print(h2)  # Himpunan({'e', 'h', 'l', 'o'})

# Duplicates are automatically removed
h3 = Himpunan([1, 1, 2, 2, 3])
print(h3)  # Himpunan({1, 2, 3})
```

## Basic Operations

### Length and Membership
```python
h = Himpunan([1, 2, 3, 4, 5])

# Length
print(len(h))  # 5

# Membership testing
print(3 in h)   # True
print(10 in h)  # False
```

### Adding Elements
```python
h = Himpunan([1, 2, 3])
h += 4  # Add element 4
print(h)  # Himpunan({1, 2, 3, 4})

h += 3  # Adding existing element has no effect
print(h)  # Himpunan({1, 2, 3, 4})
```

### Set Equality
```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 2, 1])  # Order doesn't matter
h3 = Himpunan([1, 2, 4])

print(h1 == h2)  # True
print(h1 == h3)  # False

# Alternative equality check
print(h1 // h2)  # True
```

## Set Operations

### Union (Addition: +)
The union of two sets contains all elements from both sets.

```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])
union = h1 + h2
print(union)  # Himpunan({1, 2, 3, 4, 5})
```

### Intersection (Division: /)
The intersection contains only elements present in both sets.

```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5, 6])
intersection = h1 / h2
print(intersection)  # Himpunan({3, 4})
```

### Difference (Subtraction: -)
The difference contains elements in the first set but not in the second.

```python
h1 = Himpunan([1, 2, 3, 4])
h2 = Himpunan([3, 4, 5])
difference = h1 - h2
print(difference)  # Himpunan({1, 2})
```

### Symmetric Difference (Multiplication: *)
The symmetric difference contains elements in either set but not in both.

```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])
sym_diff = h1 * h2
print(sym_diff)  # Himpunan({1, 2, 4, 5})
```

## Advanced Operations

### Cartesian Product (Power: **)
The cartesian product creates all possible ordered pairs between two sets.

```python
h1 = Himpunan([1, 2])
h2 = Himpunan(['a', 'b'])
cartesian = h1 ** h2
print(cartesian)  # Himpunan({(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')})
```

### Complement
The complement contains all elements in the universal set that are not in the current set.

```python
universal = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])
subset = Himpunan([1, 2, 3, 4])
complement = subset.komplement(universal)
print(complement)  # Himpunan({5, 6, 7, 8, 9})
```

### Power Set
The power set contains all possible subsets of a set.

```python
h = Himpunan([1, 2, 3])
power_set = abs(h)
print(f"Power set has {len(power_set)} subsets")  # 8 subsets (2^3)

# The power set includes empty set and the set itself
print(Himpunan() in power_set.elems)  # True (empty set)
print(h in power_set.elems)           # True (the set itself)
```

## Set Relations

### Subset Operations
```python
h1 = Himpunan([1, 2])
h2 = Himpunan([1, 2, 3, 4])

# Subset (<=) - all elements of h1 are in h2
print(h1 <= h2)  # True

# Proper subset (<) - h1 is subset of h2 and h1 ≠ h2
print(h1 < h2)   # True

# Superset (>=) - h2 contains all elements of h1
print(h2 >= h1)  # True

# Proper superset (>) - h2 is superset of h1 and h2 ≠ h1
print(h2 > h1)   # True
```

### Equal Sets
```python
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([1, 2])
h3 = Himpunan([1, 2])

print(h1 <= h1)  # True (every set is subset of itself)
print(h1 < h1)   # False (a set is not a proper subset of itself)
print(h2 <= h3)  # True
print(h2 < h3)   # False (equal sets are not proper subsets)
```

## Complete Example: Working with Student Groups

```python
from set_function.set_function import Himpunan

# Define sets of students
all_students = Himpunan(['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'])
math_club = Himpunan(['Alice', 'Bob', 'Charlie'])
science_club = Himpunan(['Bob', 'Diana', 'Eve'])
drama_club = Himpunan(['Charlie', 'Diana', 'Frank'])

# Students in both math and science clubs
math_and_science = math_club / science_club
print(f"In both math and science: {math_and_science}")  # {Bob}

# Students in any club
any_club = math_club + science_club + drama_club
print(f"In any club: {any_club}")  # {Alice, Bob, Charlie, Diana, Eve, Frank}

# Students only in math club
only_math = math_club - science_club - drama_club
print(f"Only in math club: {only_math}")  # {Alice}

# Students not in any club
no_clubs = all_students - any_club
print(f"Not in any club: {no_clubs}")  # {}

# Students in exactly one club
math_only = math_club - science_club - drama_club
science_only = science_club - math_club - drama_club  
drama_only = drama_club - math_club - science_club
exactly_one_club = math_only + science_only + drama_only
print(f"In exactly one club: {exactly_one_club}")  # {Alice, Eve, Frank}
```

## Error Handling

Set_Function includes comprehensive error handling for type safety:

```python
h = Himpunan([1, 2, 3])

# These operations will raise TypeError
try:
    invalid_union = h + 5  # Cannot union with non-Himpunan
except TypeError as e:
    print(e)  # "Operasi hanya bisa dilakukan antar Himpunan"

try:
    invalid_intersection = h / [1, 2]  # Cannot intersect with list
except TypeError as e:
    print(e)  # "Operasi hanya bisa dilakukan antar Himpunan"
```

## Performance Tips

1. **Use appropriate operations**: Choose the most direct operation for your needs
2. **Avoid unnecessary conversions**: Work with Himpunan objects directly
3. **Consider set size**: Large sets may benefit from streaming operations for very large datasets

## Next Steps

- Explore the [API Reference](api.md) for complete method documentation
- Check out the test suite for more advanced usage examples
- Consider contributing to the project on GitHub
