# PyAnsys V23 - SpaceClaim API Virtual Library

**PyAnsysV23** is a virtual/mock Python library that provides a comprehensive API for working with ANSYS SpaceClaim V23. This library enables developers to write and test SpaceClaim automation scripts without having SpaceClaim installed, and serves as an excellent learning resource for the SpaceClaim API.

## Features

### Core Modules

- **`geometry`** - 3D geometric primitives (Point, Vector, Plane, Matrix transformations)
- **`modeler`** - 3D body creation and manipulation (boxes, spheres, cylinders, cones)
- **`document`** - Document, part, and assembly management
- **`annotation`** - Annotations including notes, symbols, and barcodes
- **`analysis`** - FEA mesh and analysis functionality
- **`instance`** - Component instances and occurrences
- **`extensibility`** - Add-in development framework
- **`core`** - Command system, write blocks, and application control

### Key Classes

#### Geometry (`pyansysv23.geometry`)
```python
Point              # 3D point representation
Vector             # 3D vector with operations (dot, cross, normalize)
Plane              # Infinite plane in 3D space
Matrix             # 4x4 transformation matrices
Geometry           # Utility class for geometric operations
```

#### Modeler (`pyansysv23.modeler`)
```python
Body               # CAD body (solid or surface)
DesignBody         # High-level body abstraction
Face, Edge, Vertex # Topological elements
Modeler            # Factory for creating primitives
```

#### Document (`pyansysv23.document`)
```python
Document           # SpaceClaim document
Part               # CAD part
Assembly           # Component assembly
DrawingSheet       # Drawing/annotation sheet
DatumPlane         # Reference plane
```

#### Annotation (`pyansysv23.annotation`)
```python
Note               # Text annotations
Barcode            # Barcode annotations (supports multiple types)
Symbol             # Symbol annotations
Table              # Table annotations
BarcodeType        # Enum: Code39, EAN13, QRCode, DataMatrix, etc.
```

#### Analysis (`pyansysv23.analysis`)
```python
BodyMesh           # Mesh on a body
PartMesh           # Mesh on a part
AssemblyMesh       # Mesh on an assembly
MeshNode           # Individual mesh node
VolumeElement      # Volume mesh element
FaceElement        # Face mesh element
EdgeElement        # Edge mesh element
HexaBlocking       # Hexahedral mesh blocking
AnalysisAspect     # Analysis tools
```

#### Extensibility (`pyansysv23.extensibility`)
```python
AddIn              # Base class for all add-ins
CommandCapsule     # Base class for command implementations
IExtensibility     # Add-in interface
ICommandExtensibility    # Command extension interface
IRibbonExtensibility     # Ribbon customization interface
```

#### Core (`pyansysv23.core`)
```python
Command            # SpaceClaim command
WriteBlock         # Transaction/write operation
Application        # Application singleton
Window             # Application window
```

## Installation

```bash
pip install -e .
```

Or simply copy the `pyansysv23` directory to your Python project.

## Quick Start

### 1. Create Geometric Primitives

```python
from pyansysv23.geometry import Point, Vector
from pyansysv23.modeler import Modeler

# Create a box
box = Modeler.create_box(Point(0, 0, 0), length=1, width=1, height=1)
print(f"Box volume: {box.master.volume}")

# Create a sphere
sphere = Modeler.create_sphere(Point(2, 0, 0), radius=0.5)

# Create vectors and perform operations
v1 = Vector(1, 0, 0)
v2 = Vector(0, 1, 0)
cross_product = v1.cross(v2)
```

### 2. Work with Documents and Parts

```python
from pyansysv23.document import Document, Part

# Create a document
doc = Document("MyDesign.scdoc")

# Create a part
part = Part("Part1")

# Add bodies
part.add_design_body(box)
part.add_design_body(sphere)

# Add to document and save
doc.add_part(part)
doc.save("C:\\designs\\MyDesign.scdoc")
```

### 3. Create Annotations

```python
from pyansysv23.annotation import Note, Barcode, BarcodeType
from pyansysv23.geometry import PointUV
from pyansysv23.document import DrawingSheet

# Create a drawing sheet
sheet = DrawingSheet("Drawing1")

# Add a note
note = Note(sheet, "Important Note", PointUV(0.1, 0.1))

# Add a QR code barcode
qr = Barcode.create(sheet, PointUV(0.2, 0.2), BarcodeType.QRCode, "https://example.com")
```

### 4. Create Commands

```python
from pyansysv23.core import Command, WriteBlock

# Create a command
cmd = Command.create("MyAddIn.MyCommand", "My Command", "Execute my command")

# Add event handlers
def on_execute(context):
    print("Command executed!")

cmd.add_executing_handler(on_execute)

# Execute within a write block
def my_operation():
    print("Performing modifications...")

WriteBlock.ExecuteTask("My Operation", my_operation)
```

### 5. Develop an Add-in

```python
from pyansysv23.extensibility import AddIn, ICommandExtensibility, IRibbonExtensibility
from pyansysv23.core import Command

class MySpaceClaimAddIn(AddIn, ICommandExtensibility, IRibbonExtensibility):
    def connect(self) -> bool:
        print("Add-in loaded")
        return True
    
    def disconnect(self) -> None:
        print("Add-in unloaded")
    
    def initialize(self) -> None:
        cmd = Command.create("MyAddIn.CreateBox")
        cmd.text = "Create Box"
    
    def get_custom_ui(self) -> str:
        return '''<?xml version="1.0"?>
<customUI xmlns="http://schemas.spaceclaim.com/customui">
    <ribbon>
        <tabs>
            <tab id="MyAddIn.Tab" label="My Add-In">
                <group id="MyAddIn.Group" label="Geometry">
                    <button id="MyAddIn.CreateBox" command="MyAddIn.CreateBox"/>
                </group>
            </tab>
        </tabs>
    </ribbon>
</customUI>'''

# Use the add-in
addin = MySpaceClaimAddIn()
addin.connect()
addin.initialize()
```

### 6. Mesh Operations

```python
from pyansysv23.analysis import MeshBodySettings, BodyMesh, MeshNode, HexaBlocking

# Create mesh settings
mesh_settings = MeshBodySettings.create(box)
mesh_settings.element_size = 0.01

# Create and populate body mesh
body_mesh = BodyMesh(box)
node = MeshNode(0, Point(0, 0, 0))
body_mesh.nodes.append(node)

# Use hexahedral blocking
hexa = HexaBlocking()
success, error = hexa.process_command_with_error("HEXA QUADS 100")
```

## API Structure

```
pyansysv23/
├── __init__.py           # Package initialization and exports
├── geometry.py           # Geometric primitives
├── modeler.py            # 3D modeling operations
├── document.py           # Document management
├── annotation.py         # Annotations
├── analysis.py           # Analysis and meshing
├── instance.py           # Instances and components
├── extensibility.py      # Add-in framework
└── core.py              # Core commands and application
```

## Usage Examples

See `examples.py` for comprehensive examples including:
- Creating geometric primitives
- Document and part management
- Command creation and execution
- Annotation operations
- Mesh operations
- Add-in development

Run examples:
```bash
python examples.py
```

## Documentation

This library is designed to closely match the official SpaceClaim API. Reference documentation:
- `API_Class_Library.chm` - Complete API reference
- `Developers Guide.pdf` - Development guide
- `Building Sample Add-Ins.pdf` - Add-in examples

## Testing

```python
# Test geometry operations
from pyansysv23.geometry import Point, Vector

p1 = Point(0, 0, 0)
p2 = Point(1, 1, 1)
distance = p1.distance_to(p2)
assert abs(distance - 1.732050808) < 0.0001

# Test vector operations
v = Vector(3, 4, 0)
assert abs(v.magnitude() - 5.0) < 0.0001
```

## Supported Barcode Types

- Code25, Code25Interleaved
- Code39, Code93, Code11
- Code128 (A, B, C variants)
- EAN (8, 13, 14, 128)
- UPC (A, E)
- ISBN, ISMN, ISSN
- LOGMARS, VIN
- QR Code, Data Matrix, PDF417, Aztec

## Notes

This is a **virtual/mock library** intended for:
- Learning the SpaceClaim API
- Offline development and testing
- Script validation and preview
- Documentation reference

For production SpaceClaim automation, use the actual SpaceClaim API available through:
- SpaceClaim SDK (includes `SpaceClaim.Api.V23.dll`)
- Official Python add-in examples
- SpaceClaim IronPython scripting environment

## License

This is a learning/reference implementation. SpaceClaim is a product of ANSYS.

## Compatibility

- **Python**: 3.7+
- **Platform**: Windows (reflects SpaceClaim platform)
- **API Version**: V23

## Contributing

Feel free to extend this library with additional functionality based on the SpaceClaim API documentation.

## See Also

- SpaceClaim API Documentation
- ANSYS SpaceClaim Official Website
- PyAnsys Project

---

**Disclaimer**: This is a virtual/educational library. It does not interface with actual SpaceClaim installations. For real SpaceClaim automation, use the official SpaceClaim SDK.
