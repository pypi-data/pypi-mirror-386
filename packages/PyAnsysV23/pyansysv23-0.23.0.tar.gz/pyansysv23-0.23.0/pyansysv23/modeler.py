"""
PyAnsys V23 - Modeler Module
3D modeling primitives and operations
"""

from typing import Optional, List, Any, Dict
from abc import ABC, abstractmethod
from enum import Enum
from .geometry import Point, Vector, Plane, Geometry


class IDocObject(ABC):
    """Base interface for document objects"""
    
    @property
    @abstractmethod
    def id(self) -> int:
        """Get the object ID"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the object name"""
        pass


class IDesignBody(IDocObject):
    """Interface for design bodies"""
    
    @property
    @abstractmethod
    def master(self) -> 'DesignBody':
        """Get the master body"""
        pass
    
    @property
    @abstractmethod
    def bodies(self) -> List['Body']:
        """Get the bodies"""
        pass
    
    @property
    @abstractmethod
    def is_solid(self) -> bool:
        """Get whether the body is solid"""
        pass
    
    @property
    @abstractmethod
    def is_surface(self) -> bool:
        """Get whether the body is a surface"""
        pass


class Body(IDocObject):
    """Represents a CAD body (solid or surface)"""
    
    def __init__(self, name: str = "Body"):
        self._id = id(self)
        self._name = name
        self._faces: List['Face'] = []
        self._edges: List['Edge'] = []
        self._vertices: List['Vertex'] = []
        self._is_solid = True
        self.mass = 0.0
        self.volume = 0.0
        self.surface_area = 0.0
        self.center_of_mass = Point(0, 0, 0)
    
    @property
    def id(self) -> int:
        """Get the body ID"""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the body name"""
        return self._name
    
    @name.setter
    def name(self, value: str):
        """Set the body name"""
        self._name = value
    
    @property
    def faces(self) -> List['Face']:
        """Get all faces"""
        return self._faces
    
    @property
    def edges(self) -> List['Edge']:
        """Get all edges"""
        return self._edges
    
    @property
    def vertices(self) -> List['Vertex']:
        """Get all vertices"""
        return self._vertices
    
    @property
    def is_solid(self) -> bool:
        """Get whether this is a solid body"""
        return self._is_solid
    
    @property
    def is_surface(self) -> bool:
        """Get whether this is a surface body"""
        return not self._is_solid
    
    def get_face(self, index: int) -> Optional['Face']:
        """Get a face by index"""
        if 0 <= index < len(self._faces):
            return self._faces[index]
        return None
    
    def add_face(self, face: 'Face') -> None:
        """Add a face to the body"""
        if face not in self._faces:
            self._faces.append(face)
    
    def add_edge(self, edge: 'Edge') -> None:
        """Add an edge to the body"""
        if edge not in self._edges:
            self._edges.append(edge)
    
    def add_vertex(self, vertex: 'Vertex') -> None:
        """Add a vertex to the body"""
        if vertex not in self._vertices:
            self._vertices.append(vertex)


class DesignBody(Body, IDesignBody):
    """Represents a design body (higher-level abstraction)"""
    
    def __init__(self, body: Optional[Body] = None, name: str = "DesignBody"):
        super().__init__(name)
        self._master_body = body or Body(name)
        self.color = (128, 128, 128)  # Default gray
        self.opacity = 1.0
        self.is_visible = True
    
    @property
    def master(self) -> Body:
        """Get the master body"""
        return self._master_body
    
    @master.setter
    def master(self, value: Body) -> None:
        """Set the master body"""
        self._master_body = value
    
    @property
    def bodies(self) -> List[Body]:
        """Get the bodies"""
        return [self._master_body]
    
    def copy(self) -> 'DesignBody':
        """Create a copy of this design body"""
        copy = DesignBody(name=self._name + "_Copy")
        copy.color = self.color
        copy.opacity = self.opacity
        return copy


class Vertex:
    """Represents a vertex in a body"""
    
    def __init__(self, point: Point):
        self.point = point
        self._id = id(self)
    
    @property
    def id(self) -> int:
        """Get the vertex ID"""
        return self._id
    
    @property
    def location(self) -> Point:
        """Get the vertex location"""
        return self.point


class Edge:
    """Represents an edge in a body"""
    
    def __init__(self, vertex1: Vertex, vertex2: Vertex):
        self.vertex1 = vertex1
        self.vertex2 = vertex2
        self._id = id(self)
        self.length = vertex1.point.distance_to(vertex2.point)
    
    @property
    def id(self) -> int:
        """Get the edge ID"""
        return self._id
    
    @property
    def vertices(self) -> List[Vertex]:
        """Get the vertices"""
        return [self.vertex1, self.vertex2]


class Face:
    """Represents a face in a body"""
    
    def __init__(self, normal: Vector, area: float = 0.0):
        self.normal = normal.normalize()
        self.area = area
        self._id = id(self)
        self.edges: List[Edge] = []
        self.vertices: List[Vertex] = []
    
    @property
    def id(self) -> int:
        """Get the face ID"""
        return self._id
    
    def get_area(self) -> float:
        """Get the face area"""
        return self.area
    
    def get_normal(self) -> Vector:
        """Get the normal vector"""
        return self.normal


class Modeler:
    """Modeler class for creating geometric primitives"""
    
    @staticmethod
    def create_box(point: Point, length: float, width: float, height: float) -> DesignBody:
        """Create a box (rectangular prism)
        
        Parameters
        ----------
        point : Point
            The origin point
        length : float
            The length of the box
        width : float
            The width of the box
        height : float
            The height of the box
            
        Returns
        -------
        DesignBody
            The created box design body
        """
        body = Body("Box")
        body._is_solid = True
        body.volume = length * width * height
        body.surface_area = 2 * (length * width + length * height + width * height)
        body.center_of_mass = Point(
            point.x + length / 2,
            point.y + width / 2,
            point.z + height / 2
        )
        
        design_body = DesignBody(body, "Box")
        return design_body
    
    @staticmethod
    def create_sphere(center: Point, radius: float) -> DesignBody:
        """Create a sphere
        
        Parameters
        ----------
        center : Point
            The center point
        radius : float
            The radius
            
        Returns
        -------
        DesignBody
            The created sphere design body
        """
        body = Body("Sphere")
        body._is_solid = True
        body.volume = (4/3) * 3.14159265359 * (radius ** 3)
        body.surface_area = 4 * 3.14159265359 * (radius ** 2)
        body.center_of_mass = center
        
        design_body = DesignBody(body, "Sphere")
        return design_body
    
    @staticmethod
    def create_cylinder(base: Point, height: float, radius: float) -> DesignBody:
        """Create a cylinder
        
        Parameters
        ----------
        base : Point
            The base point
        height : float
            The height
        radius : float
            The radius
            
        Returns
        -------
        DesignBody
            The created cylinder design body
        """
        body = Body("Cylinder")
        body._is_solid = True
        body.volume = 3.14159265359 * (radius ** 2) * height
        body.surface_area = 2 * 3.14159265359 * radius * (height + radius)
        body.center_of_mass = Point(base.x, base.y, base.z + height / 2)
        
        design_body = DesignBody(body, "Cylinder")
        return design_body
    
    @staticmethod
    def create_cone(base: Point, height: float, radius: float) -> DesignBody:
        """Create a cone
        
        Parameters
        ----------
        base : Point
            The base point
        height : float
            The height
        radius : float
            The base radius
            
        Returns
        -------
        DesignBody
            The created cone design body
        """
        body = Body("Cone")
        body._is_solid = True
        body.volume = (1/3) * 3.14159265359 * (radius ** 2) * height
        slant_height = (height**2 + radius**2) ** 0.5
        body.surface_area = 3.14159265359 * radius * (radius + slant_height)
        body.center_of_mass = Point(base.x, base.y, base.z + height / 4)
        
        design_body = DesignBody(body, "Cone")
        return design_body


# Make Modeler accessible as a singleton-like class
Modeler = Modeler()
