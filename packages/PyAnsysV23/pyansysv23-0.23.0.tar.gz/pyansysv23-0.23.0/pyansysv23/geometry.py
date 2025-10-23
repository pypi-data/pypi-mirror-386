"""
PyAnsys V23 - Geometry Module
Geometric primitives and transformations
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import math


@dataclass
class Point:
    """Represents a 3D point"""
    x: float
    y: float
    z: float
    
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def __add__(self, other):
        """Add a vector to this point"""
        if isinstance(other, Vector):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented
    
    def __sub__(self, other):
        """Subtract another point or vector"""
        if isinstance(other, Point):
            return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, Vector):
            return Point(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented
    
    def __repr__(self):
        return f"Point({self.x}, {self.y}, {self.z})"


@dataclass
class Vector:
    """Represents a 3D vector"""
    x: float
    y: float
    z: float
    
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z
    
    def magnitude(self) -> float:
        """Calculate the magnitude (length) of the vector"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector':
        """Return a normalized copy of this vector"""
        mag = self.magnitude()
        if mag == 0:
            return Vector(0, 0, 0)
        return Vector(self.x / mag, self.y / mag, self.z / mag)
    
    def dot(self, other: 'Vector') -> float:
        """Calculate dot product with another vector"""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector') -> 'Vector':
        """Calculate cross product with another vector"""
        return Vector(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def __add__(self, other):
        """Add two vectors"""
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented
    
    def __sub__(self, other):
        """Subtract another vector"""
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented
    
    def __mul__(self, scalar):
        """Multiply vector by scalar"""
        if isinstance(scalar, (int, float)):
            return Vector(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented
    
    def __rmul__(self, scalar):
        """Right multiply vector by scalar"""
        return self.__mul__(scalar)
    
    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"


@dataclass
class PointUV:
    """Represents a 2D point in UV space"""
    u: float
    v: float
    
    def __init__(self, u: float = 0, v: float = 0):
        self.u = u
        self.v = v
    
    def distance_to(self, other: 'PointUV') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.u - other.u)**2 + (self.v - other.v)**2)
    
    def __repr__(self):
        return f"PointUV({self.u}, {self.v})"


class Plane:
    """Represents a plane in 3D space"""
    
    def __init__(self, origin: Point, normal: Vector, x_axis: Optional[Vector] = None):
        self.origin = origin
        self.normal = normal.normalize()
        
        if x_axis is None:
            # Create a perpendicular x_axis
            if abs(self.normal.x) < 0.9:
                self.x_axis = Vector(1, 0, 0).cross(self.normal).normalize()
            else:
                self.x_axis = Vector(0, 1, 0).cross(self.normal).normalize()
        else:
            self.x_axis = x_axis.normalize()
        
        self.y_axis = self.normal.cross(self.x_axis).normalize()
    
    @staticmethod
    def xy() -> 'Plane':
        """Create the XY plane (Z=0)"""
        return Plane(Point(0, 0, 0), Vector(0, 0, 1), Vector(1, 0, 0))
    
    @staticmethod
    def yz() -> 'Plane':
        """Create the YZ plane (X=0)"""
        return Plane(Point(0, 0, 0), Vector(1, 0, 0), Vector(0, 1, 0))
    
    @staticmethod
    def xz() -> 'Plane':
        """Create the XZ plane (Y=0)"""
        return Plane(Point(0, 0, 0), Vector(0, 1, 0), Vector(1, 0, 0))
    
    def distance_to_point(self, point: Point) -> float:
        """Calculate perpendicular distance from plane to point"""
        v = point - self.origin
        return abs(v.dot(self.normal))
    
    def project_point(self, point: Point) -> Point:
        """Project a point onto the plane"""
        v = point - self.origin
        distance = v.dot(self.normal)
        return point - (distance * self.normal)
    
    def get_uv_coordinates(self, point: Point) -> PointUV:
        """Get UV coordinates of a point in the plane"""
        v = point - self.origin
        u = v.dot(self.x_axis)
        v_coord = v.dot(self.y_axis)
        return PointUV(u, v_coord)


class Frame:
    """Represents a coordinate frame in 3D space"""
    
    def __init__(self, origin: Point, x_axis: Vector, y_axis: Vector):
        self.origin = origin
        self.x_axis = x_axis.normalize()
        self.y_axis = y_axis.normalize()
        self.z_axis = self.x_axis.cross(self.y_axis).normalize()
    
    @staticmethod
    def identity() -> 'Frame':
        """Create an identity frame at the origin"""
        return Frame(Point(0, 0, 0), Vector(1, 0, 0), Vector(0, 1, 0))


class Matrix:
    """4x4 transformation matrix"""
    
    def __init__(self):
        # Initialize as identity matrix
        self.m = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
    
    @staticmethod
    def identity() -> 'Matrix':
        """Create an identity matrix"""
        return Matrix()
    
    @staticmethod
    def translation(dx: float, dy: float, dz: float) -> 'Matrix':
        """Create a translation matrix"""
        m = Matrix()
        m.m[0][3] = dx
        m.m[1][3] = dy
        m.m[2][3] = dz
        return m
    
    @staticmethod
    def scale(sx: float, sy: float, sz: float) -> 'Matrix':
        """Create a scale matrix"""
        m = Matrix()
        m.m[0][0] = sx
        m.m[1][1] = sy
        m.m[2][2] = sz
        return m
    
    @staticmethod
    def rotation_x(angle: float) -> 'Matrix':
        """Create a rotation matrix around X-axis (angle in radians)"""
        m = Matrix()
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        m.m[1][1] = cos_a
        m.m[1][2] = -sin_a
        m.m[2][1] = sin_a
        m.m[2][2] = cos_a
        return m
    
    @staticmethod
    def rotation_y(angle: float) -> 'Matrix':
        """Create a rotation matrix around Y-axis (angle in radians)"""
        m = Matrix()
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        m.m[0][0] = cos_a
        m.m[0][2] = sin_a
        m.m[2][0] = -sin_a
        m.m[2][2] = cos_a
        return m
    
    @staticmethod
    def rotation_z(angle: float) -> 'Matrix':
        """Create a rotation matrix around Z-axis (angle in radians)"""
        m = Matrix()
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        m.m[0][0] = cos_a
        m.m[0][1] = -sin_a
        m.m[1][0] = sin_a
        m.m[1][1] = cos_a
        return m
    
    def multiply(self, other: 'Matrix') -> 'Matrix':
        """Multiply this matrix with another"""
        result = Matrix()
        for i in range(4):
            for j in range(4):
                result.m[i][j] = sum(self.m[i][k] * other.m[k][j] for k in range(4))
        return result
    
    def transform_point(self, point: Point) -> Point:
        """Transform a point by this matrix"""
        x = self.m[0][0] * point.x + self.m[0][1] * point.y + self.m[0][2] * point.z + self.m[0][3]
        y = self.m[1][0] * point.x + self.m[1][1] * point.y + self.m[1][2] * point.z + self.m[1][3]
        z = self.m[2][0] * point.x + self.m[2][1] * point.y + self.m[2][2] * point.z + self.m[2][3]
        return Point(x, y, z)
    
    def transform_vector(self, vector: Vector) -> Vector:
        """Transform a vector by this matrix (ignoring translation)"""
        x = self.m[0][0] * vector.x + self.m[0][1] * vector.y + self.m[0][2] * vector.z
        y = self.m[1][0] * vector.x + self.m[1][1] * vector.y + self.m[1][2] * vector.z
        z = self.m[2][0] * vector.x + self.m[2][1] * vector.y + self.m[2][2] * vector.z
        return Vector(x, y, z)


class Geometry:
    """Utility class for geometric operations"""
    
    @staticmethod
    def create_point(x: float, y: float, z: float) -> Point:
        """Create a point"""
        return Point(x, y, z)
    
    @staticmethod
    def create_vector(x: float, y: float, z: float) -> Vector:
        """Create a vector"""
        return Vector(x, y, z)
    
    @staticmethod
    def create_plane(origin: Point, normal: Vector, x_axis: Optional[Vector] = None) -> Plane:
        """Create a plane"""
        return Plane(origin, normal, x_axis)
