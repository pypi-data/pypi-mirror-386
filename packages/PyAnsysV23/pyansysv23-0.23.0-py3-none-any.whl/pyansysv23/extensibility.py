"""
PyAnsys V23 - Extensibility Module
Add-in and command extension functionality
"""

from typing import Callable, Optional, Any, Dict, List
from abc import ABC, abstractmethod
import threading
from .core import Command, ExecutionContext


class IExtensibility(ABC):
    """Interface required for all add-ins"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Called by SpaceClaim to allow initialization
        
        Returns
        -------
        bool
            True if initialization is successful; otherwise False
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Called when SpaceClaim is shut down to allow cleanup"""
        pass


class ICommandExtensibility(ABC):
    """Allows commands to be created or modified when an add-in starts up"""
    
    @abstractmethod
    def initialize(self) -> None:
        """Called during startup to create or modify Commands"""
        pass


class IRibbonExtensibility(ABC):
    """Allows the Ribbon bar to be customized when an add-in starts up"""
    
    @abstractmethod
    def get_custom_ui(self) -> str:
        """Returns XML string for Ribbon customization
        
        Returns
        -------
        str
            The XML string for the add-in's Ribbon customization
        """
        pass


class IScriptExtensibility(ABC):
    """Defines which namespaces/assemblies are automatically imported into SpaceClaim scripting"""
    
    @property
    @abstractmethod
    def command_namespace(self) -> str:
        """Gets the namespace to automatically import"""
        pass
    
    @property
    @abstractmethod
    def addin_script_namespace(self) -> str:
        """Gets the Python alias used when importing the CommandNamespace"""
        pass
    
    @property
    @abstractmethod
    def command_assemblies(self) -> List[str]:
        """Gets the collection of assemblies to reference from the scripting environment"""
        pass


class IVersionedScriptExtensibility(ABC):
    """Versioned script extensibility interface"""
    pass


class IScriptedCommand(ABC):
    """Should be implemented by CommandCapsules to enable script recording"""
    
    @abstractmethod
    def command_started(self, environment: Any) -> None:
        """Called before the command executes
        
        Important to record and store any selections the command may delete
        """
        pass
    
    @abstractmethod
    def command_complete(self, environment: Any) -> str:
        """Called when command finished
        
        Returns
        -------
        str
            Script to record
        """
        pass
    
    @property
    @abstractmethod
    def feature_track_image(self) -> Optional[Any]:
        """Get the image to use in feature tracking. Return None for default"""
        pass
    
    @property
    @abstractmethod
    def feature_track_text(self) -> Optional[str]:
        """Get the text to use in feature tracking. Return None to use command name"""
        pass


class AddIn(IExtensibility):
    """Base class for all add-ins"""
    
    _instances: Dict[type, 'AddIn'] = {}
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.is_connected = False
    
    def connect(self) -> bool:
        """Default connect implementation"""
        self.is_connected = True
        return True
    
    def disconnect(self) -> None:
        """Default disconnect implementation"""
        self.is_connected = False
    
    def on_set_default_tool(self) -> bool:
        """Called when the active tool is being set to the default tool
        
        Returns
        -------
        bool
            True if the default behavior was overridden; otherwise False
        """
        return False
    
    def execute_windows_forms_code(self, task: Callable) -> None:
        """Executes code that uses Windows Forms in a single-threaded apartment
        
        Parameters
        ----------
        task : Callable
            The code to execute
        """
        # In a real implementation, this would use Windows Forms STA
        task()
    
    @classmethod
    def get_instance(cls, addin_type: type) -> Optional['AddIn']:
        """Gets the instance of a specific add-in
        
        Parameters
        ----------
        addin_type : type
            Type of add-in
            
        Returns
        -------
        AddIn
            Add-in instance
        """
        return cls._instances.get(addin_type)
    
    @classmethod
    def register_instance(cls, addin_type: type, instance: 'AddIn') -> None:
        """Registers an add-in instance"""
        cls._instances[addin_type] = instance


class CommandCapsule:
    """A base class for command implementations"""
    
    def __init__(self, name: str, text: str = "", image=None, hint: str = ""):
        self.name = name
        self.text = text
        self.image = image
        self.hint = hint
        self.command: Optional[Command] = None
    
    def initialize(self) -> None:
        """Initializes the command capsule
        
        Creates the command and sets its properties and event handlers
        """
        self.command = Command.create(self.name)
        self.command.text = self.text
        self.command.hint = self.hint
        self.command.image = self.image
        
        # Set up event handlers
        self.command.add_updating_handler(self._on_update_wrapper)
        self.command.add_executing_handler(self._on_execute_wrapper)
        
        self.on_initialize(self.command)
    
    def _on_update_wrapper(self, context: ExecutionContext) -> None:
        """Wrapper for update handler"""
        self.on_update(self.command)
    
    def _on_execute_wrapper(self, context: ExecutionContext) -> None:
        """Wrapper for execute handler"""
        import sys
        from .core import WriteBlock
        
        # Create a dummy rectangle for button_rect
        class Rectangle:
            def __init__(self):
                self.is_empty = True
        
        button_rect = Rectangle()
        self.on_execute(self.command, context, button_rect)
    
    def on_initialize(self, command: Command) -> None:
        """Called after the command has been created
        
        Parameters
        ----------
        command : Command
            The command
        """
        pass
    
    def on_update(self, command: Command) -> None:
        """Called when the command is updating
        
        Parameters
        ----------
        command : Command
            The command
        """
        pass
    
    def on_execute(self, command: Command, context: ExecutionContext, button_rect: Any) -> None:
        """Called when the command is executing
        
        Parameters
        ----------
        command : Command
            The command
        context : ExecutionContext
            The context in which execution is taking place
        button_rect : Rectangle
            The button rectangle (empty if not executed by pressing a button)
        """
        pass


class CustomHelper:
    """Custom helper class (internal use)"""
    pass


class LightweightCustomHelper:
    """Lightweight custom helper class (internal use)"""
    pass


class UndoActionCapsule:
    """Base class for undo action implementations"""
    
    def __init__(self):
        self.redo_action: Optional['UndoActionCapsule'] = None
    
    def get_redo_action(self) -> Optional['UndoActionCapsule']:
        """Gets an action that will reverse the affect of this action
        
        Returns
        -------
        UndoActionCapsule
            The redo action
        """
        return self.redo_action
    
    def apply(self) -> None:
        """Applies the action, performing the undo"""
        pass
    
    def initialize(self) -> None:
        """Initializes the undo action and logs in the current undo step
        
        This method can only be called from within a command
        """
        pass


class ApplyLoop:
    """Provides methods for executing code within an apply loop"""
    
    def __init__(self):
        self.created_undo_step = False
    
    def complete(self) -> bool:
        """Completes an apply loop
        
        Returns
        -------
        bool
            True if the apply loop created an undo step; otherwise False
        """
        return self.created_undo_step
