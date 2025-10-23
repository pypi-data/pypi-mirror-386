"""
PyAnsys V23 - Virtual SpaceClaim API Library
A comprehensive Python wrapper for SpaceClaim API V23
"""

__version__ = "0.23.0"
__author__ = "PyAnsys Contributors"
__license__ = "MIT"

from .extensibility import (
    AddIn,
    CommandCapsule,
    IExtensibility,
    ICommandExtensibility,
    IRibbonExtensibility,
    IScriptExtensibility,
    UndoActionCapsule,
)

from .core import (
    Command,
    NativeCommand,
    WriteBlock,
    Application,
    ExecutionContext,
    Task,
    CommandException,
    ControlState,
    ComboBoxState,
    SliderState,
    SpinBoxState,
    GalleryState,
)

from .modeler import (
    DesignBody,
    Body,
    IDesignBody,
    Face,
    Edge,
    Vertex,
    Geometry,
)

from .document import (
    Document,
    Part,
    Assembly,
    DrawingSheet,
    DatumPlane,
    IDatumPlane,
)

from .annotation import (
    Note,
    Symbol,
    Barcode,
    BarcodeType,
    BarcodeCodePage,
    CheckDigitType,
    QRCodeErrorCorrectionLevel,
    AnnotationSpace,
)

from .analysis import (
    AnalysisAspect,
    BodyMesh,
    PartMesh,
    AssemblyMesh,
    MeshNode,
    VolumeElement,
    FaceElement,
    EdgeElement,
    MeshBodySettings,
    HexaBlocking,
)

from .instance import (
    Instance,
    Component,
    Occurrence,
)

from .geometry import (
    Point,
    Vector,
    Plane,
    Frame,
    Matrix,
)

__version__ = "0.23.0"
__author__ = "PyAnsys Contributors"
__all__ = [
    # Extensibility
    "AddIn",
    "CommandCapsule",
    "IExtensibility",
    "ICommandExtensibility",
    "IRibbonExtensibility",
    "IScriptExtensibility",
    "UndoActionCapsule",
    # Core
    "Command",
    "NativeCommand",
    "WriteBlock",
    "Application",
    "ExecutionContext",
    "Task",
    "CommandException",
    "ControlState",
    "ComboBoxState",
    "SliderState",
    "SpinBoxState",
    "GalleryState",
    # Modeler
    "DesignBody",
    "Body",
    "IDesignBody",
    "Face",
    "Edge",
    "Vertex",
    "Geometry",
    # Document
    "Document",
    "Part",
    "Assembly",
    "DrawingSheet",
    "DatumPlane",
    "IDatumPlane",
    # Annotation
    "Note",
    "Symbol",
    "Barcode",
    "BarcodeType",
    "BarcodeCodePage",
    "CheckDigitType",
    "QRCodeErrorCorrectionLevel",
    "AnnotationSpace",
    # Analysis
    "AnalysisAspect",
    "BodyMesh",
    "PartMesh",
    "AssemblyMesh",
    "MeshNode",
    "VolumeElement",
    "FaceElement",
    "EdgeElement",
    "MeshBodySettings",
    "HexaBlocking",
    # Instance
    "Instance",
    "Component",
    "Occurrence",
    # Geometry
    "Point",
    "Vector",
    "Plane",
    "Frame",
    "Matrix",
]
