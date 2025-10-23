"""
PyAnsys V23 - Document Module\nDocument, part, and assembly management
"""

from typing import Optional, List, Any, Dict
from abc import ABC, abstractmethod
from .modeler import IDesignBody, DesignBody, Body


class IDocObject(ABC):
    """Base interface for document objects"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the object name"""
        pass


class IPart(IDocObject):
    """Interface for parts"""
    
    @property
    @abstractmethod
    def design_bodies(self) -> List[DesignBody]:
        """Get all design bodies"""
        pass


class Document:
    """Represents a SpaceClaim document"""
    
    _active_document: Optional['Document'] = None
    
    def __init__(self, name: str = "Untitled"):
        self.name = name
        self.is_saved = False
        self.file_path = ""
        self.parts: List['Part'] = []
        self.assemblies: List['Assembly'] = []
        self.sheets: List['DrawingSheet'] = []
        self._is_modified = False
    
    @classmethod
    def get_active(cls) -> Optional['Document']:
        """Get the active document"""
        return cls._active_document
    
    @classmethod
    def set_active(cls, doc: 'Document') -> None:
        """Set the active document"""
        cls._active_document = doc
    
    def add_part(self, part: 'Part') -> None:
        """Add a part to the document"""
        if part not in self.parts:
            self.parts.append(part)
    
    def add_assembly(self, assembly: 'Assembly') -> None:
        """Add an assembly to the document"""
        if assembly not in self.assemblies:
            self.assemblies.append(assembly)
    
    def add_sheet(self, sheet: 'DrawingSheet') -> None:
        """Add a drawing sheet to the document"""
        if sheet not in self.sheets:
            self.sheets.append(sheet)
    
    def save(self, file_path: Optional[str] = None) -> bool:
        """Save the document
        
        Parameters
        ----------
        file_path : str, optional
            The file path to save to. If None, uses the existing path.
            
        Returns
        -------
        bool
            True if save was successful
        """
        if file_path:
            self.file_path = file_path
        self.is_saved = True
        self._is_modified = False
        return True
    
    def close(self) -> bool:
        """Close the document
        
        Returns
        -------
        bool
            True if close was successful
        """
        if self._is_modified and not self.is_saved:
            return False  # Unsaved changes
        if self == self._active_document:
            self._active_document = None
        return True
    
    def mark_modified(self) -> None:
        """Mark the document as modified"""
        self._is_modified = True
        self.is_saved = False


class Part:
    """Represents a part in a document"""
    
    def __init__(self, name: str = "Part"):
        self._name = name
        self._design_bodies: List[DesignBody] = []
        self.planes: List['DatumPlane'] = []
        self.points: List['DatumPoint'] = []
        self.coordinate_systems: List['CoordinateSystem'] = []
        self.features: List[Any] = []
    
    @property
    def name(self) -> str:
        """Get the part name"""
        return self._name
    
    @property
    def design_bodies(self) -> List[DesignBody]:
        """Get all design bodies"""
        return self._design_bodies
    
    def add_design_body(self, body: DesignBody) -> None:
        """Add a design body to the part"""
        if body not in self._design_bodies:
            self._design_bodies.append(body)
    
    def remove_design_body(self, body: DesignBody) -> bool:
        """Remove a design body from the part
        
        Parameters
        ----------
        body : DesignBody
            The body to remove
            
        Returns
        -------
        bool
            True if the body was removed
        """
        if body in self._design_bodies:
            self._design_bodies.remove(body)
            return True
        return False
    
    def get_body_by_name(self, name: str) -> Optional[DesignBody]:
        """Get a body by name"""
        for body in self._design_bodies:
            if body.name == name:
                return body
        return None


class Assembly:
    """Represents an assembly in a document"""
    
    def __init__(self, name: str = "Assembly"):
        self.name = name
        self.components: List['Component'] = []
        self.is_expanded = True
    
    def add_component(self, component: 'Component') -> None:
        """Add a component to the assembly"""
        if component not in self.components:
            self.components.append(component)
    
    def remove_component(self, component: 'Component') -> bool:
        """Remove a component from the assembly"""
        if component in self.components:
            self.components.remove(component)
            return True
        return False


class DatumPlane:
    """Represents a datum plane (reference plane)"""
    
    def __init__(self, name: str = "Plane"):
        self.name = name
        self.is_visible = True
        self.is_locked = False
        self.annotations: List[Any] = []
    
    @property
    def Master(self) -> 'DatumPlane':
        """Get the master plane"""
        return self


class IDatumPlane:
    """Interface for datum planes"""
    
    @property
    def Master(self) -> DatumPlane:
        """Get the master plane"""
        pass


class DatumPoint:
    """Represents a datum point (reference point)"""
    
    def __init__(self, location: Any, name: str = "Point"):
        self.name = name
        self.location = location
        self.is_visible = True
        self.is_locked = False


class CoordinateSystem:
    """Represents a coordinate system"""
    
    def __init__(self, name: str = "CoordinateSystem"):
        self.name = name
        self.is_visible = True
        self.is_locked = False
        self.origin = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None


class DrawingSheet:
    """Represents a drawing sheet"""
    
    def __init__(self, name: str = "Sheet", width: float = 0.297, height: float = 0.21):
        self.name = name
        self.width = width  # in meters, default A4
        self.height = height
        self.views: List['DrawingView'] = []
        self.annotations: List[Any] = []
    
    @property
    def Master(self) -> 'DrawingSheet':
        """Get the master sheet"""
        return self
    
    def add_view(self, view: 'DrawingView') -> None:
        """Add a drawing view to the sheet"""
        if view not in self.views:
            self.views.append(view)


class DrawingView:
    """Represents a view on a drawing sheet"""
    
    def __init__(self, name: str = "View"):
        self.name = name
        self.scale = 1.0
        self.position = (0, 0)
        self.size = (0.1, 0.1)
        self.is_visible = True


# Container for active instances
class ActiveContext:
    """Manages active document and window context"""
    
    _active_document: Optional[Document] = None
    _active_part: Optional[Part] = None
    _active_assembly: Optional[Assembly] = None
    
    @classmethod
    def get_active_document(cls) -> Optional[Document]:
        """Get the active document"""
        return cls._active_document
    
    @classmethod
    def set_active_document(cls, doc: Document) -> None:
        """Set the active document"""
        cls._active_document = doc
        Document.set_active(doc)
    
    @classmethod
    def get_active_part(cls) -> Optional[Part]:
        """Get the active part"""
        return cls._active_part
    
    @classmethod
    def set_active_part(cls, part: Part) -> None:
        """Set the active part"""
        cls._active_part = part
