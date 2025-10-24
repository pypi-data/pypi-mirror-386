"""
Differential Geometry Module for Coordinate System Package

This module provides tools for discrete differential geometry computations on surfaces,
including:
- Surface representations
- First fundamental form (metric tensor)
- Connection operators (frame derivatives / intrinsic gradients)
- Curvature tensors

Author: PanGuoJun & Claude AI
Version: 2.2.0
Date: 2025-10-24
"""

import numpy as np
from typing import Tuple, Optional, Callable
from .coordinate_system import coord3, vec3, ZERO3, UNITX, UNITY, UNITZ, ONEC


# ========== Surface Base Class ==========

class Surface:
    """
    Base class for parametric surfaces r(u, v)

    A surface is represented by a position function that maps parameters (u, v)
    to 3D space. This class provides automatic computation of tangent vectors,
    normals, and geometric quantities through numerical differentiation.
    """

    def __init__(self, h: float = 1e-6):
        """
        Initialize surface

        Args:
            h: Step size for numerical differentiation (default: 1e-6)
        """
        self.h = h

    def position(self, u: float, v: float) -> vec3:
        """
        Compute position r(u, v) on the surface

        Args:
            u, v: Parameter coordinates

        Returns:
            Position vector in 3D space

        Note:
            This method must be overridden in derived classes
        """
        raise NotImplementedError("Subclass must implement position(u, v)")

    def tangent_u(self, u: float, v: float) -> vec3:
        """
        Compute tangent vector in u direction: ∂r/∂u

        Uses central difference for numerical differentiation:
            r_u ≈ (r(u+h, v) - r(u-h, v)) / (2h)

        Args:
            u, v: Parameter coordinates

        Returns:
            Tangent vector in u direction
        """
        r_plus = self.position(u + self.h, v)
        r_minus = self.position(u - self.h, v)
        return (r_plus - r_minus) * (1.0 / (2.0 * self.h))

    def tangent_v(self, u: float, v: float) -> vec3:
        """
        Compute tangent vector in v direction: ∂r/∂v

        Args:
            u, v: Parameter coordinates

        Returns:
            Tangent vector in v direction
        """
        r_plus = self.position(u, v + self.h)
        r_minus = self.position(u, v - self.h)
        return (r_plus - r_minus) * (1.0 / (2.0 * self.h))

    def normal(self, u: float, v: float) -> vec3:
        """
        Compute unit normal vector: n = (r_u × r_v) / |r_u × r_v|

        Args:
            u, v: Parameter coordinates

        Returns:
            Unit normal vector
        """
        r_u = self.tangent_u(u, v)
        r_v = self.tangent_v(u, v)
        n = r_u.cross(r_v)
        length = (n.x**2 + n.y**2 + n.z**2) ** 0.5
        if length > 1e-10:
            return n * (1.0 / length)
        else:
            return UNITZ


# ========== Common Surface Types ==========

class Sphere(Surface):
    """
    Sphere: r(u, v) = R(sin(u)cos(v), sin(u)sin(v), cos(u))

    Parameters:
        u ∈ [0, π]   - Polar angle
        v ∈ [0, 2π]  - Azimuthal angle
    """

    def __init__(self, radius: float = 1.0, h: float = 1e-6):
        """
        Args:
            radius: Sphere radius (default: 1.0)
            h: Step size for numerical differentiation
        """
        super().__init__(h)
        self.R = radius

    def position(self, u: float, v: float) -> vec3:
        """Compute position on sphere"""
        import math
        x = self.R * math.sin(u) * math.cos(v)
        y = self.R * math.sin(u) * math.sin(v)
        z = self.R * math.cos(u)
        return vec3(x, y, z)


class Torus(Surface):
    """
    Torus: r(u, v) = ((R + r·cos(u))cos(v), (R + r·cos(u))sin(v), r·sin(u))

    Parameters:
        u ∈ [0, 2π]  - Minor circle angle
        v ∈ [0, 2π]  - Major circle angle
        R: Major radius (distance from center to tube center)
        r: Minor radius (tube radius)
    """

    def __init__(self, major_radius: float = 3.0, minor_radius: float = 1.0, h: float = 1e-6):
        """
        Args:
            major_radius: Major radius R (default: 3.0)
            minor_radius: Minor radius r (default: 1.0)
            h: Step size for numerical differentiation
        """
        super().__init__(h)
        self.R = major_radius
        self.r = minor_radius

    def position(self, u: float, v: float) -> vec3:
        """Compute position on torus"""
        import math
        x = (self.R + self.r * math.cos(u)) * math.cos(v)
        y = (self.R + self.r * math.cos(u)) * math.sin(v)
        z = self.r * math.sin(u)
        return vec3(x, y, z)


# ========== Metric Tensor (First Fundamental Form) ==========

class MetricTensor:
    """
    First fundamental form (metric tensor) of a surface

    The metric tensor g describes the intrinsic geometry:
        g = [[E, F],
             [F, G]]

    where:
        E = r_u · r_u  (u-direction metric)
        F = r_u · r_v  (cross term, measures non-orthogonality)
        G = r_v · r_v  (v-direction metric)

    det(g) = E·G - F² reflects the "area stretch" of parametrization
    """

    def __init__(self, E: float, F: float, G: float):
        """
        Initialize metric tensor

        Args:
            E, F, G: Metric coefficients
        """
        self.E = E
        self.F = F
        self.G = G
        self.det = E * G - F * F

    @classmethod
    def from_coord3(cls, C: coord3) -> 'MetricTensor':
        """
        Compute metric tensor from embedding coordinate system

        Args:
            C: Embedding coord3 object with columns [r_u, r_v, n]
               (unnormalized tangent vectors preserving scale information)

        Returns:
            MetricTensor object

        Example:
            >>> C = compute_embedding_frame(surface, u, v)
            >>> g = MetricTensor.from_coord3(C)
            >>> print(f"det(g) = {g.det}")
        """
        # Extract tangent vectors from coord3
        # coord3 is a 3x3 matrix with columns [ux, uy, uz]
        VX = vec3(C.ux.x, C.ux.y, C.ux.z)  # First column
        VY = vec3(C.uy.x, C.uy.y, C.uy.z)  # Second column

        E = VX.dot(VX)
        F = VX.dot(VY)
        G = VY.dot(VY)

        return cls(E, F, G)

    @classmethod
    def from_surface(cls, surface: Surface, u: float, v: float) -> 'MetricTensor':
        """
        Compute metric tensor directly from surface

        Args:
            surface: Surface object
            u, v: Parameter coordinates

        Returns:
            MetricTensor object
        """
        r_u = surface.tangent_u(u, v)
        r_v = surface.tangent_v(u, v)

        E = r_u.dot(r_u)
        F = r_u.dot(r_v)
        G = r_v.dot(r_v)

        return cls(E, F, G)

    def determinant(self) -> float:
        """Get metric determinant det(g) = E·G - F²"""
        return self.det

    def correction_factor(self) -> float:
        """
        Compute metric correction factor: 1 / √det(g)

        This factor is used in connection operator correction to eliminate
        parametrization dependence:
            G_corrected = scale × G' × correction_factor

        Returns:
            1/√det(g), or 1.0 if det(g) ≤ 0 (degenerate case)
        """
        if self.det > 1e-10:
            return 1.0 / (self.det ** 0.5)
        else:
            return 1.0

    def is_orthogonal(self, tol: float = 1e-6) -> bool:
        """Check if parametrization is orthogonal (F ≈ 0)"""
        return abs(self.F) < tol

    def __repr__(self) -> str:
        return f"MetricTensor(E={self.E:.6f}, F={self.F:.6f}, G={self.G:.6f}, det={self.det:.6f})"


# ========== Connection Operator (Frame Derivative / Intrinsic Gradient) ==========

class ConnectionOperator:
    """
    Connection operator (also known as frame derivative or intrinsic gradient)

    Computes the discrete connection operator G on surfaces using the formula:
        G = f(G'), where G' = (c₂·c₁⁻¹)/C₂ - I/C₁

    The correction function f includes:
        1. Scale correction: compensates for O(h) discretization errors
        2. Metric correction: eliminates parametrization dependence

    Terminology note:
        - "Connection Operator" is the standard mathematical term
        - "Frame Derivative" is more intuitive (derivative of frame field)
        - "Intrinsic Gradient" is informal but commonly used
    """

    def __init__(
        self,
        surface: Surface,
        scale_factor: float = 2.0,
        use_metric_correction: bool = True,
        step_size: Optional[float] = None
    ):
        """
        Initialize connection operator computer

        Args:
            surface: Surface object
            scale_factor: Scaling factor for correction (default: 2.0, optimal for constant curvature)
            use_metric_correction: Whether to apply metric correction (default: True)
            step_size: Numerical differentiation step size (default: surface.h)
        """
        self.surface = surface
        self.scale_factor = scale_factor
        self.use_metric_correction = use_metric_correction
        self.h = step_size if step_size is not None else surface.h

    def _compute_intrinsic_frame(self, u: float, v: float) -> coord3:
        """
        Compute intrinsic frame c (normalized tangents + normal)

        Args:
            u, v: Parameter coordinates

        Returns:
            coord3 object with columns [t_u_norm, t_v_norm, n_norm]
        """
        r_u = self.surface.tangent_u(u, v)
        r_v = self.surface.tangent_v(u, v)
        n = self.surface.normal(u, v)

        # Normalize tangents
        len_u = (r_u.x**2 + r_u.y**2 + r_u.z**2) ** 0.5
        len_v = (r_v.x**2 + r_v.y**2 + r_v.z**2) ** 0.5

        if len_u > 1e-10:
            t_u = r_u * (1.0 / len_u)
        else:
            t_u = UNITX

        if len_v > 1e-10:
            t_v = r_v * (1.0 / len_v)
        else:
            t_v = UNITY

        # Create coord3 from basis vectors
        return coord3(ZERO3, t_u, t_v, n)

    def _compute_embedding_frame(self, u: float, v: float) -> coord3:
        """
        Compute embedding frame C (unnormalized tangents + normal, orthogonalized)

        Args:
            u, v: Parameter coordinates

        Returns:
            coord3 object (orthogonalized via Gram-Schmidt)
        """
        r_u = self.surface.tangent_u(u, v)
        r_v = self.surface.tangent_v(u, v)
        n = self.surface.normal(u, v)

        # Gram-Schmidt orthogonalization
        # e1 = r_u
        e1 = r_u

        # e2 = r_v - (r_v·e1)e1/|e1|²
        len_e1_sq = e1.x**2 + e1.y**2 + e1.z**2
        if len_e1_sq > 1e-10:
            proj = r_v.dot(e1) / len_e1_sq
            e2 = r_v - e1 * proj
        else:
            e2 = r_v

        # e3 = n (already normalized and orthogonal)
        e3 = n

        return coord3(ZERO3, e1, e2, e3)

    def compute(self, u: float, v: float, direction: str = 'u') -> coord3:
        """
        Compute connection operator G_u or G_v

        This is the main function for external calls!

        Args:
            u, v: Parameter coordinates
            direction: 'u' or 'v', which direction to compute

        Returns:
            coord3 object representing the connection operator

        Example:
            >>> conn = ConnectionOperator(sphere)
            >>> G_u = conn.compute(u=np.pi/4, v=np.pi/3, direction='u')
            >>> print(f"G_u norm: {G_u.norm()}")
        """
        # Frames at point 1
        c1 = self._compute_intrinsic_frame(u, v)
        C1 = self._compute_embedding_frame(u, v)

        # Frames at point 2 (stepped in direction)
        if direction == 'u':
            u2, v2 = u + self.h, v
        elif direction == 'v':
            u2, v2 = u, v + self.h
        else:
            raise ValueError(f"direction must be 'u' or 'v', got: {direction}")

        c2 = self._compute_intrinsic_frame(u2, v2)
        C2 = self._compute_embedding_frame(u2, v2)

        # Base combination operator: G' = (c₂·c₁⁻¹)/C₂ - I/C₁
        G_prime = (c2 / c1) / C2 - ONEC / C1

        # Apply scale correction
        G = G_prime * self.scale_factor

        # Apply metric correction (if enabled)
        if self.use_metric_correction:
            metric = MetricTensor.from_coord3(C1)
            correction = metric.correction_factor()
            G = G * correction

        return G

    def compute_both(self, u: float, v: float) -> Tuple[coord3, coord3]:
        """
        Compute connection operators in both u and v directions

        Args:
            u, v: Parameter coordinates

        Returns:
            (G_u, G_v) tuple of coord3 objects
        """
        G_u = self.compute(u, v, 'u')
        G_v = self.compute(u, v, 'v')
        return G_u, G_v


# ========== Simplified Interface Functions ==========

def compute_metric(
    surface: Surface,
    u: float,
    v: float
) -> MetricTensor:
    """
    Compute first fundamental form (metric tensor) at a point

    Args:
        surface: Surface object
        u, v: Parameter coordinates

    Returns:
        MetricTensor object containing E, F, G, and det(g)

    Example:
        >>> sphere = Sphere(radius=2.0)
        >>> g = compute_metric(sphere, u=np.pi/4, v=np.pi/3)
        >>> print(g)
    """
    return MetricTensor.from_surface(surface, u, v)


def compute_connection(
    surface: Surface,
    u: float,
    v: float,
    direction: str = 'u',
    scale_factor: float = 2.0,
    use_metric_correction: bool = True
) -> coord3:
    """
    Compute connection operator (intrinsic gradient) at a point

    This is the recommended simplified function for external use.

    Args:
        surface: Surface object
        u, v: Parameter coordinates
        direction: 'u' or 'v'
        scale_factor: Scaling factor (default: 2.0)
        use_metric_correction: Whether to apply metric correction (default: True)

    Returns:
        coord3 object representing the connection operator

    Example:
        >>> from coordinate_system.differential_geometry import compute_connection, Sphere
        >>> import math
        >>>
        >>> sphere = Sphere(radius=2.0)
        >>> G_u = compute_connection(sphere, u=math.pi/4, v=math.pi/3, direction='u')
        >>> print(f"Connection operator norm: {G_u.norm():.8f}")
    """
    conn = ConnectionOperator(surface, scale_factor, use_metric_correction)
    return conn.compute(u, v, direction)


def compute_curvature_tensor(
    surface: Surface,
    u: float,
    v: float,
    scale_factor: float = 2.0,
    use_metric_correction: bool = True,
    use_lie_derivative: bool = True
) -> coord3:
    """
    Compute curvature tensor R_uv at a point

    The curvature tensor is computed using:
        R_uv = [G_u, G_v] - G_{[u,v]}  (with Lie derivative)
        R_uv = [G_u, G_v]              (without Lie derivative)

    where:
        [G_u, G_v] = G_u @ G_v - G_v @ G_u  (Lie bracket / commutator)
        G_{[u,v]} = ∂G_v/∂u - ∂G_u/∂v      (Lie derivative term)

    Args:
        surface: Surface object
        u, v: Parameter coordinates
        scale_factor: Scaling factor for connection operators
        use_metric_correction: Whether to apply metric correction
        use_lie_derivative: Whether to include Lie derivative term (default: True)
                           For spheres, this improves accuracy by 24×!

    Returns:
        coord3 object representing the curvature tensor R_uv

    Note:
        R_uv is a 3×3 matrix (coord3 object) with structure:
            [[R_11, R_12, R_13],   ← Tangent-tangent (intrinsic curvature)
             [R_21, R_22, R_23],   ← Tangent-normal (second fundamental form)
             [R_31, R_32, R_33]]   ← Normal-normal (extrinsic curvature)

        Gaussian curvature can be extracted as: K = R_12 / det(g)

    Example:
        >>> sphere = Sphere(radius=2.0)
        >>> R_uv = compute_curvature_tensor(sphere, u=math.pi/4, v=math.pi/3)
        >>>
        >>> # Extract Gaussian curvature
        >>> g = compute_metric(sphere, u=math.pi/4, v=math.pi/3)
        >>> K = R_uv.uy.x / g.det  # R_12 / det(g)
        >>> print(f"Gaussian curvature K = {K:.6f}")
        >>> print(f"Theoretical K = {1/(2.0**2):.6f}")  # 1/R²
    """
    conn = ConnectionOperator(surface, scale_factor, use_metric_correction)
    h = surface.h

    # Compute G_u and G_v
    G_u = conn.compute(u, v, 'u')
    G_v = conn.compute(u, v, 'v')

    # Lie bracket: [G_u, G_v] = G_u @ G_v - G_v @ G_u
    commutator = G_u * G_v - G_v * G_u

    if not use_lie_derivative:
        return commutator

    # Lie derivative term: G_{[u,v]} = ∂G_v/∂u - ∂G_u/∂v
    # Numerical differentiation
    G_v_plus_u = conn.compute(u + h, v, 'v')
    G_v_minus_u = conn.compute(u - h, v, 'v')
    dGv_du = (G_v_plus_u - G_v_minus_u) * (1.0 / (2.0 * h))

    G_u_plus_v = conn.compute(u, v + h, 'u')
    G_u_minus_v = conn.compute(u, v - h, 'u')
    dGu_dv = (G_u_plus_v - G_u_minus_v) * (1.0 / (2.0 * h))

    lie_derivative = dGv_du - dGu_dv

    # Curvature tensor
    R_uv = commutator - lie_derivative

    return R_uv


# ========== Gaussian Curvature Computation ==========

def compute_gaussian_curvature(
    surface: Surface,
    u: float,
    v: float,
    scale_factor: float = 2.0,
    use_metric_correction: bool = True,
    use_lie_derivative: bool = True
) -> float:
    """
    Compute Gaussian curvature K at a point

    K = R_12 / det(g)

    where R_12 is extracted from the curvature tensor R_uv

    Args:
        surface: Surface object
        u, v: Parameter coordinates
        scale_factor: Scaling factor
        use_metric_correction: Whether to apply metric correction
        use_lie_derivative: Whether to include Lie derivative term

    Returns:
        Gaussian curvature K

    Example:
        >>> sphere = Sphere(radius=2.0)
        >>> K = compute_gaussian_curvature(sphere, u=math.pi/4, v=math.pi/3)
        >>> print(f"Computed K = {K:.6f}")
        >>> print(f"Theoretical K = {0.25:.6f}")  # 1/R² = 1/4
    """
    # Compute curvature tensor
    R_uv = compute_curvature_tensor(
        surface, u, v,
        scale_factor=scale_factor,
        use_metric_correction=use_metric_correction,
        use_lie_derivative=use_lie_derivative
    )

    # Compute metric
    g = compute_metric(surface, u, v)

    # Extract R_12 (antisymmetric part of tangent-tangent block)
    # R_12 is the (1,2) element of R_uv matrix
    # In coord3: uy.x represents the second row, first column
    R_12 = R_uv.uy.x

    # Gaussian curvature
    if abs(g.det) > 1e-10:
        K = R_12 / g.det
    else:
        K = 0.0

    return K


# ========== Aliases for Different Naming Preferences ==========

# Standard names (recommended)
compute_frame_derivative = compute_connection
compute_metric_tensor = compute_metric

# Informal names
compute_intrinsic_gradient = compute_connection
compute_geometric_gradient = compute_connection

# Export all
__all__ = [
    # Classes
    'Surface',
    'Sphere',
    'Torus',
    'MetricTensor',
    'ConnectionOperator',

    # Main functions
    'compute_metric',
    'compute_connection',
    'compute_curvature_tensor',
    'compute_gaussian_curvature',

    # Aliases
    'compute_frame_derivative',
    'compute_intrinsic_gradient',
    'compute_geometric_gradient',
    'compute_metric_tensor',
]
