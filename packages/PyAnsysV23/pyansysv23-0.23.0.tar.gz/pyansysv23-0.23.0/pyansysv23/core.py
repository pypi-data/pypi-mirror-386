"""
PyAnsys V23 - Core Module
Basic command and application functionality
"""

from enum import Enum
from typing import Callable, Optional, Any, List, Dict
from dataclasses import dataclass
import threading


class CommandException(Exception):
    """Exception raised during command execution"""
    pass


class ControlState:
    """Describes the state of a UI control"""
    pass


@dataclass
class ComboBoxState(ControlState):
    """Describes the state of a combo box control"""
    items: List[str]
    text: str
    selected_index: int
    is_editable: bool = False

    @classmethod
    def create_editable(cls, items: List[str], text: str) -> "ComboBoxState":
        """Creates data for an editable combo box"""
        return cls(items=items, text=text, selected_index=-1, is_editable=True)

    @classmethod
    def create_fixed(cls, items: List[str], selected_index: int) -> "ComboBoxState":
        """Creates data for a fixed combo box"""
        text = items[selected_index] if 0 <= selected_index < len(items) else ""
        return cls(items=items, text=text, selected_index=selected_index, is_editable=False)


@dataclass
class SliderState(ControlState):
    """Describes the state of a slider control"""
    value: int
    min_value: int
    max_value: int
    step_size: int = 1

    @classmethod
    def create(cls, value: int, min_value: int, max_value: int, step_size: int = 1) -> "SliderState":
        """Creates data for a slider"""
        return cls(value=value, min_value=min_value, max_value=max_value, step_size=step_size)


@dataclass
class SpinBoxState(ControlState):
    """Describes the state of a spin box control"""
    value: float
    min_value: float
    max_value: float
    step_size: float = 1.0
    decimal_places: int = 0

    @classmethod
    def create(cls, value: float, min_value: float, max_value: float, 
               step_size: float = 1.0, decimal_places: int = 0) -> "SpinBoxState":
        """Creates data for a spin box"""
        return cls(value=value, min_value=min_value, max_value=max_value, 
                   step_size=step_size, decimal_places=decimal_places)


class GalleryState(ControlState):
    """Describes the state of a gallery control"""
    
    def __init__(self, commands: List['Command']):
        self.commands = commands

    @classmethod
    def create(cls, commands: List['Command']) -> "GalleryState":
        """Creates data for a gallery"""
        return cls(commands=commands)


class NativeCommand(Enum):
    """A native (built-in) command"""
    Delete = "Delete"
    ShowAll = "ShowAll"


class ExecutionContext:
    """Execution context for command execution"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.timestamp = None


# Type alias for command task
Task = Callable[[], None]


class Command:
    """Represents a command in SpaceClaim"""
    
    _registry: Dict[str, 'Command'] = {}
    
    def __init__(self, name: str, text: str = "", hint: str = "", image=None):
        self.name = name
        self.text = text
        self.hint = hint
        self.image = image
        self.is_enabled = True
        self.is_visible = True
        self.updating_handler: Optional[Callable] = None
        self.executing_handler: Optional[Callable] = None
        self.tab_is_active = False
        self._is_write_block = True
        
    @classmethod
    def create(cls, name: str, text: str = "", hint: str = "", image=None) -> "Command":
        """Creates a new command"""
        if name in cls._registry:
            return cls._registry[name]
        
        cmd = cls(name, text, hint, image)
        cls._registry[name] = cmd
        return cmd
    
    @classmethod
    def get_command(cls, name: str) -> Optional["Command"]:
        """Gets an existing command by name"""
        return cls._registry.get(name)
    
    def add_updating_handler(self, handler: Callable) -> None:
        """Adds an updating event handler"""
        self.updating_handler = handler
    
    def add_executing_handler(self, handler: Callable) -> None:
        """Adds an executing event handler"""
        self.executing_handler = handler
    
    @property
    def Updating(self):
        """Event for command updating"""
        return self
    
    @Updating.setter
    def Updating(self, handler):
        self.add_updating_handler(handler)
    
    @property
    def Executing(self):
        """Event for command executing"""
        return self
    
    @Executing.setter
    def Executing(self, handler):
        self.add_executing_handler(handler)
    
    @property
    def IsWriteBlock(self) -> bool:
        """Gets or sets whether command is in a write block"""
        return self._is_write_block
    
    @IsWriteBlock.setter
    def IsWriteBlock(self, value: bool) -> None:
        self._is_write_block = value
    
    @property
    def TabIsActive(self) -> bool:
        """Gets whether the ribbon tab is active"""
        return self.tab_is_active
    
    def execute(self, context: ExecutionContext = None) -> None:
        """Executes the command"""
        if context is None:
            context = ExecutionContext(self.name)
        
        if self.executing_handler:
            self.executing_handler(context)


class CommandFilter:
    """A command filter for native commands"""
    
    def apply(self, objects: List[Any]) -> List[Any]:
        """Applies the command filter
        
        Parameters
        ----------
        objects : List
            Objects to which the command is being applied
            
        Returns
        -------
        List
            Remaining or additional objects to be processed by the native command
        """
        return objects


class WriteBlock:
    """Provides methods for executing code within a write block"""
    
    _active = False
    _interrupted = False
    
    @classmethod
    @property
    def IsAvailable(cls) -> bool:
        """Determines whether SpaceClaim is currently executing an interactive process"""
        return not cls._active
    
    @classmethod
    @property
    def IsActive(cls) -> bool:
        """Gets whether the calling code is currently inside a write block"""
        return cls._active
    
    @classmethod
    @property
    def IsInterrupted(cls) -> bool:
        """Gets whether the current operation has been interrupted"""
        return cls._interrupted
    
    @classmethod
    def ExecuteTask(cls, text: str, task: Task) -> bool:
        """Executes code within a write block
        
        Parameters
        ----------
        text : str
            The text to appear in the undo drop list
        task : Task
            The code to execute
            
        Returns
        -------
        bool
            True if the write block created an undo step
        """
        try:
            cls._active = True
            cls._interrupted = False
            task()
            return True
        except CommandException:
            cls._interrupted = True
            return False
        finally:
            cls._active = False
    
    @classmethod
    def AppendTask(cls, task: Task) -> None:
        """Executes code within a write block, but appends to the last undo step
        
        Parameters
        ----------
        task : Task
            The code to execute
        """
        cls.ExecuteTask("", task)


class Application:
    """The SpaceClaim application"""
    
    _instance = None
    _command_filters: Dict[NativeCommand, CommandFilter] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_active_window(cls) -> Optional[Any]:
        """Gets the active window"""
        return None
    
    @classmethod
    def add_command_filter(cls, native_command: NativeCommand, filter: CommandFilter) -> None:
        """Adds a command filter for a native command
        
        Parameters
        ----------
        native_command : NativeCommand
            The native command to filter
        filter : CommandFilter
            The command filter to apply
        """
        cls._command_filters[native_command] = filter
    
    @classmethod
    def remove_command_filter(cls, native_command: NativeCommand) -> None:
        """Removes a command filter for a native command"""
        if native_command in cls._command_filters:
            del cls._command_filters[native_command]


class Window:
    """Represents a SpaceClaim window"""
    
    _active_window = None
    
    def __init__(self, name: str = "Main"):
        self.name = name
        self.active_tool = None
    
    @classmethod
    @property
    def ActiveWindow(cls) -> Optional["Window"]:
        """Gets the active window"""
        if cls._active_window is None:
            cls._active_window = cls()
        return cls._active_window
    
    def set_tool(self, tool: Any) -> None:
        """Sets the active tool"""
        self.active_tool = tool


# Make Window.ActiveWindow accessible
Window.ActiveWindow = property(lambda self: Window._active_window or Window())
