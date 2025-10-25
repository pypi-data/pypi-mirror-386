# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-24

### Added
- Initial implementation of `Himpunan` class for mathematical set operations
- Complete set operations: union (+), intersection (/), difference (-), symmetric difference (*)
- Advanced operations: cartesian product (**), power set (abs()), complement
- Set relationship operations: subset (<=), superset (>=), proper subset (<), proper superset (>)
- Element operations: membership testing (in), adding elements (+=)
- Type safety with comprehensive error handling
- Complete test suite with pytest
- Comprehensive documentation with usage examples
- CLI interface with typer integration
- Python 3.10+ support
- MIT License

### Features
- **Intuitive Python operators** for mathematical set operations
- **Type-safe operations** with automatic error checking
- **Memory efficient** implementation using Python's built-in set
- **Hashable sets** allowing sets to contain other sets
- **Power set generation** with efficient algorithms
- **Comprehensive documentation** with examples and API reference

### Documentation
- Complete README with usage examples
- Detailed API reference documentation
- Installation guide with multiple methods
- Usage guide with real-world examples
- Error handling documentation

### Testing
- 100% test coverage with pytest
- Comprehensive test cases covering all operations
- Type error testing
- Edge case handling tests

## [Unreleased]

### Planned Features
- Performance optimizations for large sets
- Additional mathematical operations (e.g., disjoint union)
- Serialization support (JSON, pickle)
- Integration with NumPy arrays
- Command-line utilities for set operations
- Interactive set calculator

### Development
- Continuous integration setup
- Documentation hosting
- PyPI package distribution
- Type hint annotations
