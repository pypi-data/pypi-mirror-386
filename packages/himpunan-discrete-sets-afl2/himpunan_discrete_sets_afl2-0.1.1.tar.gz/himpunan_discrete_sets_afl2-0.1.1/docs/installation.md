# Installation

## Requirements

Set_Function requires Python 3.10 or later. It has minimal dependencies:

- Python >= 3.10
- typer (for CLI functionality)

## Stable Release

To install Set_Function, run this command in your terminal:

```bash
pip install Set_Package_AFL
```

This is the preferred method to install Set_Function, as it will always install the most recent stable release.

If you prefer to use `uv`:

```bash
uv add Set_Package_AFL
```

## From Source

The source files for Set_Function can be downloaded from the [Github repo](https://github.com/1nnocentia/set_function).

You can either clone the public repository:

```bash
git clone git://github.com/1nnocentia/set_function
```

Or download the [tarball](https://github.com/1nnocentia/set_function/tarball/master):

```bash
curl -OJL https://github.com/1nnocentia/set_function/tarball/master
```

Once you have a copy of the source, you can install it with:

```bash
cd set_function
pip install -e .
```

## Development Installation

If you're planning to contribute to Set_Function, install it in development mode:

```bash
git clone git://github.com/1nnocentia/set_function
cd set_function
pip install -e ".[test]"
```

This will install the package in editable mode along with testing dependencies.

## Verify Installation

To verify that Set_Function is installed correctly, try importing it:

```python
from set_function.set_function import Himpunan

# Create a simple set
h = Himpunan([1, 2, 3])
print(h)  # Should output: Himpunan({1, 2, 3})
```

If this runs without errors, you have successfully installed Set_Function!

You can either clone the public repository:

```sh
git clone git://github.com/1nnocentia/set_function
```

Or download the [tarball](https://github.com/1nnocentia/set_function/tarball/master):

```sh
curl -OJL https://github.com/1nnocentia/set_function/tarball/master
```

Once you have a copy of the source, you can install it with:

```sh
cd set_function
uv pip install .
```
