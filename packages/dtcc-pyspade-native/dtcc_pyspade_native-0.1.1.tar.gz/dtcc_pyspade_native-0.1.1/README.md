# dtcc-pyspade-native

[![PyPI version](https://badge.fury.io/py/dtcc-pyspade-native.svg)](https://badge.fury.io/py/dtcc-pyspade-native)
[![License](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/dtcc-pyspade-native.svg)](https://pypi.org/project/dtcc-pyspade-native/)

**Ship the Spade C++ triangulation library with your Python package** - no Python bindings, just pure C++ for your C++ extensions.

## What is this?

`dtcc-pyspade-native` packages the [Spade](https://github.com/Stoeoef/spade) C++ Delaunay triangulation library for distribution via PyPI. It's designed for Python projects that have C++ components and need fast, robust 2D triangulation.

**Key Point**: This package provides **C++ libraries only** - no Python API. Use it when your Python project already has C++ extensions (pybind11, Cython, etc.) and you want to use Spade in that C++ code.

## Quick Start

### Install

```bash
pip install dtcc-pyspade-native
```

### Use in Your Python Project

**pyproject.toml:**
```toml
[build-system]
requires = ["scikit-build-core", "pybind11", "dtcc-pyspade-native>=0.1.0"]

[project]
dependencies = ["dtcc-pyspade-native>=0.1.0"]
```

**CMakeLists.txt:**
```cmake
find_package(Python REQUIRED COMPONENTS Interpreter)

execute_process(
    COMMAND ${Python_EXECUTABLE} -c "import pyspade_native; print(pyspade_native.get_cmake_dir())"
    OUTPUT_VARIABLE PYSPADE_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

find_package(pyspade_native REQUIRED PATHS ${PYSPADE_CMAKE_DIR} NO_DEFAULT_PATH)

target_link_libraries(your_module PRIVATE pyspade_native::spade_wrapper)
```

**your_module.cpp:**
```cpp
#include <spade_wrapper.h>

void triangulate() {
    std::vector<spade::Point> polygon = {{0,0,0}, {1,0,0}, {0.5,1,0}};
    auto result = spade::triangulate(polygon, {}, {}, 0.5,
                                     spade::Quality::Moderate, true);
    // Use result.points, result.triangles...
}
```

## Features

- ✅ **Easy Distribution**: Install via pip, no manual C++ library management
- ✅ **Cross-Platform**: Pre-built wheels for Linux, macOS, Windows
- ✅ **CMake Integration**: Clean `find_package()` support
- ✅ **No Rust Required**: Ships pre-built Rust FFI library
- ✅ **C++17**: Modern C++ API with STL containers
- ✅ **Constrained Delaunay**: Full CDT support with mesh refinement

## Use Cases

Perfect for:
- Python packages with pybind11/Cython/cffi extensions
- GIS applications with C++ backends
- Scientific computing tools
- CAD/CAM software with Python interfaces
- Any Python project that needs C++ triangulation

## Documentation

- [Installation Guide](docs/installation.md)
- [CMake Integration](docs/cmake.md)
- [C++ API Reference](docs/api.md)
- [Example Projects](examples/)
- [Troubleshooting](docs/troubleshooting.md)

## Python Helper API

```python
import pyspade_native

# Get paths for your build system
include_dir = pyspade_native.get_include_dir()
library_dir = pyspade_native.get_library_dir()
cmake_dir = pyspade_native.get_cmake_dir()

# Get available libraries
libs = pyspade_native.get_libraries()
# {'spade_wrapper': '/path/to/libspade_wrapper.so',
#  'spade_ffi': '/path/to/libspade_ffi.so'}

# Print installation info
pyspade_native.print_info()
```

## C++ API

The Spade C++ wrapper provides a clean, modern interface:

```cpp
namespace spade {
    // Triangulate a polygon with optional holes and interior constraints
    TriangulationResult triangulate(
        const std::vector<Point>& outer,
        const std::vector<std::vector<Point>>& holes = {},
        const std::vector<std::vector<Point>>& interior_loops = {},
        double maxh = 1.0,
        Quality quality = Quality::Default,
        bool enforce_constraints = true
    );

    enum class Quality {
        Default,   // No angle constraints
        Moderate   // 25-degree minimum angle
    };

    struct TriangulationResult {
        std::vector<Point> points;
        std::vector<Triangle> triangles;
        std::vector<Edge> edges;
        size_t num_vertices() const;
        size_t num_triangles() const;
        size_t num_edges() const;
    };
}
```

## Example Project

See [examples/complete-project](examples/complete-project) for a full working example of a Python package that uses dtcc-pyspade-native.

```bash
cd examples/complete-project
pip install .
python -c "from my_package import triangulate; print(triangulate([[0,0],[1,0],[0.5,1]]))"
```

## Building from Source

```bash
git clone https://github.com/dtcc-platform/dtcc-pyspade-native
cd dtcc-pyspade-native
pip install -e .
```

### Development

```bash
# Install in editable mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Build wheels
python -m build

# Run examples
cd examples/complete-project && pip install . && python test.py
```

## Requirements

### For Installation
- Python 3.8+
- C++ compiler with C++17 support
- CMake 3.15+

### For Building from Source
- All of the above
- Rust toolchain (automatically fetched if not present)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Dual-licensed under MIT OR Apache-2.0, matching the Spade library.

## Acknowledgments

This project packages the [Spade](https://github.com/Stoeoef/spade) library by Stefan Löffler for easy Python distribution. Developed as part of the [DTCC Platform](https://github.com/dtcc-platform).

## Links

- [PyPI Package](https://pypi.org/project/dtcc-pyspade-native/)
- [GitHub Repository](https://github.com/dtcc-platform/dtcc-pyspade-native)
- [Issue Tracker](https://github.com/dtcc-platform/dtcc-pyspade-native/issues)
- [Spade Library](https://github.com/Stoeoef/spade)
- [Documentation](https://dtcc-platform.github.io/dtcc-pyspade-native/)