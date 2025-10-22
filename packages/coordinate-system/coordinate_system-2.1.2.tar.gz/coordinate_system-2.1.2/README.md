# Coordinate System Library

**High-performance 3D coordinate system and math library for Python**

[![PyPI version](https://badge.fury.io/py/coordinate-system.svg)](https://pypi.org/project/coordinate-system/)
[![Python](https://img.shields.io/pypi/pyversions/coordinate-system.svg)](https://pypi.org/project/coordinate-system/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://pypi.org/project/coordinate-system/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Author:** PanGuoJun
**Version:** 1.2.0
**License:** MIT

---

## Features

### Core Classes

- **vec3** - 3D vector with comprehensive operations
- **quat** - Quaternion for 3D rotations
- **coord3** - Complete 3D coordinate system (position, rotation, scale)

### Operations

- Vector arithmetic (+, -, *, /)
- Dot product, cross product
- Vector projection, reflection
- Linear interpolation (lerp)
- Spherical linear interpolation (slerp)
- Coordinate system transformations
- Euler angle conversion

### Performance

- Written in optimized C++17
- Python bindings via pybind11
- Over 1,000,000 operations per second

### Platform Support

- ✅ Windows (7, 10, 11)
- ✅ Linux (Ubuntu, Debian, CentOS, etc.)
- ✅ macOS (10.14+)

---

## 📚 Documentation

### Mathematical Foundation

For a comprehensive understanding of the mathematical principles behind coordinate systems, vectors, quaternions, and transformations, see our detailed mathematical guide:

**[📖 Mathematical Foundation of Coordinate Systems](https://github.com/panguojun/Coordinate-System/blob/main/MATHEMATICAL_FOUNDATION.md)**

This guide covers:
- Vector mathematics (dot product, cross product, projections)
- Quaternion theory and applications
- Coordinate system transformations
- Euler angles and gimbal lock
- Interpolation methods (LERP, SLERP, NLERP)
- Practical applications in graphics, physics, and robotics

---

## Installation

### From PyPI (Recommended)

```bash
pip install coordinate-system
```

### From Source

```bash
git clone https://github.com/panguojun/Coordinate-System.git
cd Coordinate-System
pip install .
```

---

## Quick Start

```python
from coordinate_system import vec3, quat, coord3

# Create vectors
v1 = vec3(1, 2, 3)
v2 = vec3(4, 5, 6)

# Vector operations
v3 = v1 + v2              # Addition: vec3(5, 7, 9)
dot = v1.dot(v2)          # Dot product: 32.0
cross = v1.cross(v2)      # Cross product
length = v1.length()      # Length: 3.742
normalized = v1.normcopy() # Unit vector

# Quaternion rotation
axis = vec3(0, 0, 1)      # Z axis
q = quat(1.5708, axis)    # 90 degrees rotation
rotated = q * v1          # Rotate v1

# Coordinate systems
frame = coord3.from_angle(1.57, vec3(0, 0, 1))  # Frame rotated 90°
world_pos = v1 * frame    # Transform to world space
local_pos = world_pos / frame  # Transform back to local

# Interpolation
lerped = vec3.lerp(v1, v2, 0.5)  # Linear interpolation
```

---

## System Compatibility

### Operating Systems

| Platform | Status | Notes |
|----------|--------|-------|
| Windows 7+ | ✅ Full Support | Tested on Windows 10/11 |
| Linux | ✅ Full Support | Ubuntu 18.04+, CentOS 7+, Debian 9+ |
| macOS | ✅ Full Support | macOS 10.14 (Mojave) and later |

### Python Versions

- Python 3.7
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

---

## Coordinate System Type

This library uses a **left-handed coordinate system** for all vector and quaternion operations.

```
      +Y
       |
       |
       |
       +-----> +X
      /
     /
   +Z
```

---

## API Reference

### vec3 - 3D Vector

#### Constructors

```python
v = vec3()              # Zero vector (0, 0, 0)
v = vec3(x, y, z)       # Vector with components
```

#### Properties

```python
v.x  # X component
v.y  # Y component
v.z  # Z component
```

#### Arithmetic Operations

```python
v3 = v1 + v2           # Addition
v3 = v1 - v2           # Subtraction
v3 = v1 * scalar       # Scalar multiplication
v3 = scalar * v1       # Reverse scalar multiplication
v3 = v1 / scalar       # Scalar division
v3 = v1 * v2           # Component-wise multiplication
```

#### Vector Operations

```python
dot = v1.dot(v2)       # Dot product (float)
cross = v1.cross(v2)   # Cross product (vec3)
length = v.length()    # Vector length
v.normalize()          # Normalize in-place
normalized = v.normcopy()  # Return normalized copy
```

#### Additional Methods

```python
v.lenxy()              # Length in XY plane
v.sqrlen()             # Squared length
v.abslen()             # Sum of absolute components
v.isINF()              # Check for infinity
v.flipX()              # Flip X component
v.flipY()              # Flip Y component
v.flipZ()              # Flip Z component
```

#### Static Methods

```python
v = vec3.min3(a, b, c)         # Component-wise minimum
v = vec3.max3(a, b, c)         # Component-wise maximum
v = vec3.rnd()                 # Random vector
v = vec3.lerp(a, b, t)         # Linear interpolation
angle = vec3.angle(a, b)       # Angle between vectors
```

---

### quat - Quaternion

#### Constructors

```python
q = quat()                     # Identity quaternion
q = quat(w, x, y, z)           # From components
q = quat(angle, axis)          # From angle-axis
q = quat(v1, v2)               # From two vectors
```

#### Properties

```python
q.w, q.x, q.y, q.z  # Quaternion components
```

#### Operations

```python
q3 = q1 + q2               # Addition
q3 = q1 * q2               # Multiplication (composition)
v_rotated = q * v          # Rotate vector
q3 = q1 / q2               # Division
```

#### Methods

```python
q.normalize()              # Normalize in-place
normalized = q.normalized()  # Return normalized copy
conj = q.conj()            # Conjugate
length = q.length()        # Length
dot = q1.dot(q2)           # Dot product
angle = q1.angle_to(q2)    # Angle to another quaternion
```

#### Conversion

```python
# From Euler angles
q.from_eulers(pitch, yaw, roll)

# From vectors
q.fromvectors(v1, v2)

# Advanced
q_exp = q.exp()            # Exponential
q_log = q.log()            # Logarithm
```

---

### coord3 - 3D Coordinate System

A `coord3` represents a complete 3D coordinate frame with:
- **Position** (o): Origin in 3D space
- **Rotation** (ux, uy, uz): Three orthonormal axes
- **Scale** (s): Scale factors for each axis

#### Constructors

```python
c = coord3()                              # Identity frame
c = coord3(x, y, z)                       # Position only
c = coord3(x, y, z, pitch, yaw, roll)     # Position + rotation (Euler)
c = coord3(x, y, z, qw, qx, qy, qz)       # Position + rotation (quaternion)
c = coord3(position)                      # From vec3
c = coord3(ux, uy, uz)                    # From three axes
c = coord3(angle, axis)                   # From angle-axis rotation
c = coord3(quaternion)                    # From quaternion
c = coord3(position, quaternion, scale)   # Full specification
```

#### Properties

```python
c.o          # Origin (vec3)
c.ux, c.uy, c.uz  # Axis vectors (vec3)
c.s          # Scale (vec3)
```

#### Static Factory Methods

```python
c = coord3.from_axes(ux, uy, uz)         # From three axes
c = coord3.from_angle(angle, axis)       # From angle-axis
```

#### Transformations

```python
# Transform point from local to world
world_pos = local_pos * coord

# Transform point from world to local
local_pos = world_pos / coord

# Combine coordinate systems
c3 = c1 * c2
```

#### Operations

```python
c3 = c1 + c2           # Add (translate)
c3 = c1 - c2           # Subtract
c3 = c1 * c2           # Multiply (compose transformations)
c3 = c1 / c2           # Divide
equal = c1 == c2       # Equality check
```

#### Methods

```python
pos = c.pos()          # Get position vector
vec = c.tovec()        # Convert to vector
c.rot(angle, axis)     # Rotate by angle-axis
c.rot(quaternion)      # Rotate by quaternion
equal = c1.equal_dirs(c2)  # Check if axes are equal
hash_val = c.hash()    # Hash value
serial = c.serialise() # Serialize to string
c.dump()               # Print debug info
```

---

## Usage Examples

### Vector Mathematics

```python
from coordinate_system import vec3

# Create vectors
v1 = vec3(1, 0, 0)
v2 = vec3(0, 1, 0)

# Basic operations
v3 = v1 + v2                    # vec3(1, 1, 0)
v4 = v1 * 5                     # vec3(5, 0, 0)

# Dot and cross products
dot = v1.dot(v2)                # 0.0 (perpendicular)
cross = v1.cross(v2)            # vec3(0, 0, 1) in left-handed system

# Length and normalization
length = v1.length()            # 1.0
v_normalized = v1.normcopy()   # Unit vector

# Linear interpolation
v_mid = vec3.lerp(v1, v2, 0.5)  # vec3(0.5, 0.5, 0)
```

### Quaternion Rotations

```python
from coordinate_system import vec3, quat

# Create quaternion from angle-axis
import math
axis = vec3(0, 0, 1)           # Z axis
angle = math.pi / 2             # 90 degrees
q = quat(angle, axis)

# Rotate vector
v = vec3(1, 0, 0)
rotated = q * v                 # Approximately vec3(0, 1, 0)

# Create quaternion from two vectors
v_from = vec3(1, 0, 0)
v_to = vec3(0, 1, 0)
q = quat(v_from, v_to)

# Quaternion composition
q1 = quat(math.pi/4, vec3(0, 0, 1))  # 45° around Z
q2 = quat(math.pi/4, vec3(0, 1, 0))  # 45° around Y
combined = q1 * q2                    # Combined rotation

# Euler angles
q.from_eulers(pitch=0.1, yaw=0.2, roll=0.3)
```

### Coordinate System Transformations

```python
from coordinate_system import vec3, quat, coord3
import math

# Create a coordinate system at position (5, 10, 15)
frame = coord3(5, 10, 15)

# Create with rotation
q = quat(math.pi/4, vec3(0, 0, 1))  # 45° rotation
frame = coord3(vec3(5, 10, 15), q, vec3(1, 1, 1))

# Transform points between coordinate systems
world_point = vec3(10, 0, 0)
local_point = world_point / frame   # World to local
back_to_world = local_point * frame  # Local to world

# Hierarchical transformations
parent = coord3(0, 5, 0)
child = coord3(3, 0, 0)
child_in_world = child * parent

# Create look-at transformation (custom implementation needed)
def look_at(eye, target, up=vec3(0, 1, 0)):
    forward = (target - eye).normcopy()
    right = up.cross(forward).normcopy()
    up_corrected = forward.cross(right)
    return coord3.from_axes(right, up_corrected, forward)

camera = look_at(vec3(10, 10, 10), vec3(0, 0, 0))
```

### Practical Applications

#### Camera System

```python
from coordinate_system import vec3, quat, coord3
import math

class Camera:
    def __init__(self, position, target, up=vec3(0, 1, 0)):
        self.frame = self.create_look_at(position, target, up)

    def create_look_at(self, eye, target, up):
        forward = (target - eye).normcopy()
        right = up.cross(forward).normcopy()
        up_corrected = forward.cross(right)

        c = coord3()
        c.o = eye
        c.ux = right
        c.uy = up_corrected
        c.uz = forward
        return c

    def move_forward(self, distance):
        self.frame.o = self.frame.o + self.frame.uz * distance

    def orbit(self, angle_h, angle_v):
        q_h = quat(angle_h, vec3(0, 1, 0))
        q_v = quat(angle_v, self.frame.ux)
        self.frame.rot(q_h)
        self.frame.rot(q_v)

# Usage
cam = Camera(vec3(0, 5, 10), vec3(0, 0, 0))
cam.orbit(0.1, 0)  # Orbit horizontally
cam.move_forward(1.0)  # Move forward
```

#### Physics Simulation

```python
from coordinate_system import vec3, quat, coord3

class RigidBody:
    def __init__(self, position=vec3(0, 0, 0)):
        self.frame = coord3(position)
        self.velocity = vec3(0, 0, 0)
        self.angular_velocity = vec3(0, 0, 0)

    def apply_force(self, force, dt):
        self.velocity = self.velocity + force * dt

    def update(self, dt):
        # Update position
        self.frame.o = self.frame.o + self.velocity * dt

        # Update rotation
        if self.angular_velocity.length() > 0:
            angle = self.angular_velocity.length() * dt
            axis = self.angular_velocity.normcopy()
            q = quat(angle, axis)
            self.frame.rot(q)

# Usage
body = RigidBody(vec3(0, 10, 0))
gravity = vec3(0, -9.8, 0)

dt = 1.0 / 60.0  # 60 FPS
for _ in range(100):
    body.apply_force(gravity, dt)
    body.update(dt)
```

---

## Advanced Features

### Interpolation

The package provides helper functions for interpolation:

```python
from coordinate_system import lerp

# Linear interpolation
v1 = vec3(0, 0, 0)
v2 = vec3(10, 10, 10)
v_mid = lerp(v1, v2, 0.5)  # vec3(5, 5, 5)
```

For spherical linear interpolation (slerp), use quaternions:

```python
q1 = quat()  # Identity
q2 = quat(1.57, vec3(0, 0, 1))  # 90° rotation

# Manual slerp implementation or use quaternion methods
# (depends on availability in your binding)
```

### Constants

```python
from coordinate_system import ZERO3, UNITX, UNITY, UNITZ, ONE3, ONE4, ONEC

ZERO3  # Zero vector vec3(0, 0, 0)
UNITX  # Unit X vector vec3(1, 0, 0)
UNITY  # Unit Y vector vec3(0, 1, 0)
UNITZ  # Unit Z vector vec3(0, 0, 1)
ONE3   # Unit scale vec3(1, 1, 1)
ONE4   # Identity quaternion quat(1, 0, 0, 0)
ONEC   # World coordinate system coord3()
```

---

## Building from Source

### Prerequisites

- C++17 compatible compiler
- Python 3.7+
- pybind11

### Windows

```bash
# Install Visual Studio 2019+ with C++ tools
pip install pybind11 wheel
python setup.py build
python setup.py bdist_wheel
```

### Linux

```bash
sudo apt install build-essential python3-dev
pip3 install pybind11 wheel
python3 setup.py build
python3 setup.py bdist_wheel
```

### macOS

```bash
xcode-select --install
pip3 install pybind11 wheel
python3 setup.py build
python3 setup.py bdist_wheel
```

---

## Performance

Benchmark on Intel i7-10700K @ 3.8GHz:

| Operation | Ops/second |
|-----------|-----------|
| Vector addition | 5,200,000 |
| Dot product | 4,800,000 |
| Cross product | 3,500,000 |
| Normalize | 2,100,000 |
| Quaternion rotation | 1,800,000 |

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details

Copyright (c) 2024-2025 PanGuoJun

---

## Author

**PanGuoJun** (romeosoft)

- Email: 18858146@qq.com
- GitHub: [panguojun/Coordinate-System](https://github.com/panguojun/Coordinate-System)

---

## Links

- **PyPI**: https://pypi.org/project/coordinate-system/
- **GitHub**: https://github.com/panguojun/Coordinate-System
- **Mathematical Foundation**: [MATHEMATICAL_FOUNDATION.md](https://github.com/panguojun/Coordinate-System/blob/main/MATHEMATICAL_FOUNDATION.md)
- **Issues**: https://github.com/panguojun/Coordinate-System/issues

---

## Changelog

### Version 1.2.0 (2025-10-22)
- ✅ Cross-platform support (Windows, Linux, macOS)
- ✅ Updated documentation
- ✅ Improved API consistency
- ✅ Added more usage examples
- ✅ Performance optimizations

### Version 1.1.0 (2024-09-08)
- Initial PyPI release
- Windows support
- Core vec3, quat, coord3 classes

---

## Acknowledgments

Built with ❤️ using:
- C++17
- pybind11
- Python

---

**Note**: For the latest updates and documentation, visit the [GitHub repository](https://github.com/panguojun/Coordinate-System).
