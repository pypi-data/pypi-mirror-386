# Welcome to Set_Function's documentation!

Set_Function is a comprehensive Python package for mathematical set operations. It provides an intuitive interface for working with sets, including all standard mathematical operations like union, intersection, difference, and advanced operations like power sets and cartesian products.

## Key Features

- **Complete Set Operations**: All standard mathematical set operations
- **Pythonic Interface**: Uses familiar Python operators (`+`, `-`, `*`, `/`, etc.)
- **Type Safety**: Built-in error handling and type checking
- **Performance Optimized**: Efficient algorithms for all operations
- **Well Tested**: Comprehensive test suite ensuring reliability

## Quick Example

```python
from set_function.set_function import Himpunan

# Create sets
h1 = Himpunan([1, 2, 3])
h2 = Himpunan([3, 4, 5])

# Perform operations
union = h1 + h2        # {1, 2, 3, 4, 5}
intersection = h1 / h2  # {3}
difference = h1 - h2    # {1, 2}
```

## Contents

- [Installation](installation.md) - How to install the package
- [Usage](usage.md) - Detailed usage examples and API reference
- [API Reference](api.md) - Complete API documentation

## Support

If you encounter any issues or have questions, please:
- Check the [Usage Guide](usage.md) for common examples
- Review the [API Reference](api.md) for detailed method documentation
- Submit issues on our GitHub repository
