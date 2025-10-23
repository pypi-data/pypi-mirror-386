"""
PyAnsys V23 - Instance Module
Instance, component, and occurrence management
"""

from typing import Optional, List, Any, Dict
from .geometry import Point, Matrix


class Instance:
    """Represents an instance of a component"""
    
    def __init__(self, name: str = "Instance"):
        self.name = name
        self._id = id(self)
        self.transformation = Matrix.identity()
        self.is_visible = True
    
    @property
    def id(self) -> int:
        """Get the instance ID"""
        return self._id


class Component:
    """Represents a component in an assembly"""
    
    def __init__(self, name: str = "Component", master: Optional[Any] = None):
        self.name = name
        self.master = master
        self._id = id(self)
        self.occurrences: List['Occurrence'] = []
        self.instances: List[Instance] = []
        self.is_suppressed = False
        self.transformation = Matrix.identity()
    
    @property
    def id(self) -> int:
        """Get the component ID"""
        return self._id
    
    def add_occurrence(self, occurrence: 'Occurrence') -> None:
        """Add an occurrence"""
        if occurrence not in self.occurrences:
            self.occurrences.append(occurrence)
    
    def add_instance(self, instance: Instance) -> None:
        """Add an instance"""
        if instance not in self.instances:
            self.instances.append(instance)


class Occurrence:
    """Represents an occurrence (instance placement) of a component"""
    
    def __init__(self, component: Component, name: str = "Occurrence"):
        self.name = name
        self.component = component
        self._id = id(self)
        self.transformation = Matrix.identity()
        self.is_visible = True
        self.parent: Optional['Occurrence'] = None
        self.children: List['Occurrence'] = []
    
    @property
    def id(self) -> int:
        """Get the occurrence ID"""
        return self._id
    
    def add_child(self, child: 'Occurrence') -> None:
        """Add a child occurrence"""
        if child not in self.children and child.parent is None:
            self.children.append(child)
            child.parent = self
    
    def remove_child(self, child: 'Occurrence') -> bool:
        """Remove a child occurrence"""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            return True
        return False
    
    def get_occurrence(self, path: List['Occurrence']) -> Optional['Occurrence']:
        """Get an occurrence by path
        
        Parameters
        ----------
        path : List[Occurrence]
            The path to follow
            
        Returns
        -------
        Occurrence
            The found occurrence, or None
        """
        current = self
        for occurrence in path:
            found = False
            for child in current.children:
                if child == occurrence:
                    current = child
                    found = True
                    break
            if not found:
                return None
        return current


# Maintain global occurrences registry for lookups
_occurrences_registry: Dict[int, Occurrence] = {}


def register_occurrence(occurrence: Occurrence) -> None:
    """Register an occurrence globally"""
    _occurrences_registry[occurrence.id] = occurrence


def get_occurrence(occurrence_id: int) -> Optional[Occurrence]:
    """Get an occurrence by ID"""
    return _occurrences_registry.get(occurrence_id)
