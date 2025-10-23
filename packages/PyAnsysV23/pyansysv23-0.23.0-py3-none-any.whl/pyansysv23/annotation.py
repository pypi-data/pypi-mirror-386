"""
PyAnsys V23 - Annotation Module\nAnnotation objects like notes, symbols, and barcodes
"""

from enum import Enum
from typing import Optional, Any, List, Tuple
from dataclasses import dataclass
from .geometry import PointUV, Point


class AnnotationSpace(Enum):
    """The annotation space of an object"""
    Model = "Model"  # Object size is defined in model-space
    View = "View"    # Object size is defined in view-space


class BarcodeType(Enum):
    """Barcode types"""
    Code25 = "Code25"
    Code25Interleaved = "Code25Interleaved"
    Code39 = "Code39"
    Codabar2 = "Codabar2"
    Code93 = "Code93"
    Code11 = "Code11"
    Code128A = "Code128A"
    Code128B = "Code128B"
    Code128C = "Code128C"
    Ean8 = "Ean8"
    Ean13 = "Ean13"
    Ean14 = "Ean14"
    Ean128 = "Ean128"
    UpcA = "UpcA"
    UpcE = "UpcE"
    Isbn = "Isbn"
    Ismn = "Ismn"
    Issn = "Issn"
    Logmars = "Logmars"
    Vin = "Vin"
    DataMatrix = "DataMatrix"
    Pdf417 = "Pdf417"
    QRCode = "QRCode"
    Aztec = "Aztec"


class BarcodeCodePage(Enum):
    """Barcode code page (character encoding)"""
    Default = "Default"
    ANSI = "ANSI"
    Windows1252 = "Windows1252"
    Latin_I = "Latin_I"
    ASCIIExt_437 = "ASCIIExt_437"
    UTF8 = "UTF8"
    Korean = "Korean"
    Japanese_Shift_JIS = "Japanese_Shift_JIS"
    Simplified_Chinese = "Simplified_Chinese"
    Traditional_Chinese_Big5 = "Traditional_Chinese_Big5"
    ANSI_Cyrillic = "ANSI_Cyrillic"
    KOI8_R = "KOI8_R"


class CheckDigitType(Enum):
    """Barcode check digit types"""
    None_ = "None"
    Standard = "Standard"
    Mod10 = "Mod10"
    Mod43 = "Mod43"
    # ... many more types available


class QRCodeErrorCorrectionLevel(Enum):
    """QR Code error correction level"""
    Low = "Low"          # ~7% recovery
    Medium = "Medium"    # ~15% recovery (default)
    Quartil = "Quartil"  # ~25% recovery
    High = "High"        # ~30% recovery


class DataMatrixBarcodeSize(Enum):
    """Data matrix barcode size"""
    AutomaticSquare = "AutomaticSquare"
    AutomaticRectangular = "AutomaticRectangular"
    # Square sizes
    Square10x10 = "Square10x10"
    Square12x12 = "Square12x12"
    # ... and many more


@dataclass
class BarcodeProperties:
    """Base class for barcode-specific properties"""
    pass


@dataclass
class QRCodeBarcodeProperties(BarcodeProperties):
    """QR Code specific properties"""
    error_correction: QRCodeErrorCorrectionLevel = QRCodeErrorCorrectionLevel.Medium
    code_page: BarcodeCodePage = BarcodeCodePage.UTF8


@dataclass
class DataMatrixBarcodeProperties(BarcodeProperties):
    """Data Matrix specific properties"""
    size: DataMatrixBarcodeSize = DataMatrixBarcodeSize.AutomaticSquare


class BarcodeBar:
    """Represents a bar in a barcode"""
    
    def __init__(self, width: float, is_black: bool):
        self.width = width
        self.is_black = is_black


class Barcode:
    """Represents a barcode annotation"""
    
    def __init__(self, parent: Any, anchor_location: PointUV, barcode_type: BarcodeType, data: str):
        self.parent = parent
        self.anchor_location = anchor_location
        self.type = barcode_type
        self.data = data
        self._is_valid = self._validate_data(data, barcode_type)
        self.annotation_space = AnnotationSpace.Model
        self.show_text = True
        self.module_width = 0.001  # in meters
        self.check_digit_type = CheckDigitType.Standard
        self.width = 0.05  # in meters
        self.height = 0.025  # in meters
        self.angle = 0.0  # in radians
        self.text = ""
        self.plane = None
        self._bars: List[BarcodeBar] = []
        self.bold = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
        self.font_name = "Arial"
        self.font_size = 12
        self._generate_bars()
    
    @classmethod
    def create(cls, parent: Any, anchor_location: PointUV, barcode_type: BarcodeType, data: str) -> 'Barcode':
        """Create a barcode
        
        Parameters
        ----------
        parent : IAnnotationParent
            The parent in which the barcode should be created
        anchor_location : PointUV
            The anchor location in UV space
        barcode_type : BarcodeType
            The barcode type
        data : str
            The barcode data
            
        Returns
        -------
        Barcode
            The created barcode
        """
        return cls(parent, anchor_location, barcode_type, data)
    
    @property
    def is_valid(self) -> bool:
        """Get whether the barcode is valid"""
        return self._is_valid
    
    @property
    def bars(self) -> List[BarcodeBar]:
        """Get the bars of the barcode"""
        return self._bars
    
    @property
    def anchor_point(self) -> PointUV:
        """Get the anchor point"""
        return self.anchor_location
    
    def copy(self) -> 'Barcode':
        """Create a copy of the barcode"""
        return Barcode(self.parent, self.anchor_location, self.type, self.data)
    
    def _validate_data(self, data: str, barcode_type: BarcodeType) -> bool:
        """Validate barcode data for the given type"""
        if not data:
            return False
        
        # Simple validation - can be extended with real rules
        if barcode_type == BarcodeType.Ean13:
            return len(data) == 13 and data.isdigit()
        elif barcode_type == BarcodeType.Code39:
            return all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ -.$/+%" for c in data)
        
        return len(data) > 0
    
    def _generate_bars(self) -> None:
        """Generate bars for the barcode (simplified)"""
        # This is a simplified representation
        self._bars = []
        for i, char in enumerate(self.data):
            width = 0.002 + (ord(char) % 10) * 0.0001
            is_black = i % 2 == 0
            self._bars.append(BarcodeBar(width, is_black))


class Symbol:
    """Represents a symbol annotation"""
    
    def __init__(self, parent: Any, name: str = "Symbol"):
        self.parent = parent
        self.name = name
        self.location = PointUV(0, 0)
        self.is_visible = True
        self.scale = 1.0


class Note:
    """Represents a text note annotation"""
    
    def __init__(self, parent: Any, text: str = "", location: Optional[PointUV] = None):
        self.parent = parent
        self.text = text
        self.location = location or PointUV(0, 0)
        self.is_visible = True
        self.font_name = "Arial"
        self.font_size = 12
        self.bold = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
        self.text_color = (0, 0, 0)  # RGB
        self.background_color = None
    
    @classmethod
    def create(cls, parent: Any, text: str, location: PointUV) -> 'Note':
        """Create a note
        
        Parameters
        ----------
        parent : IAnnotationParent
            The parent annotation object
        text : str
            The note text
        location : PointUV
            The note location in UV space
            
        Returns
        -------
        Note
            The created note
        """
        return cls(parent, text, location)
    
    def copy(self) -> 'Note':
        """Create a copy of the note"""
        note = Note(self.parent, self.text, self.location)
        note.font_name = self.font_name
        note.font_size = self.font_size
        note.bold = self.bold
        note.italic = self.italic
        return note


class DatumFeatureSymbol:
    """Represents a datum feature symbol"""
    
    def __init__(self, parent: Any, name: str = "DatumFeature"):
        self.parent = parent
        self.name = name
        self.location = PointUV(0, 0)
        self.is_visible = True


class Table:
    """Represents a table annotation"""
    
    def __init__(self, parent: Any, name: str = "Table", rows: int = 1, columns: int = 1):
        self.parent = parent
        self.name = name
        self.rows = rows
        self.columns = columns
        self.location = PointUV(0, 0)
        self.is_visible = True
        self.data: List[List[str]] = [[f"Cell({i},{j})" for j in range(columns)] for i in range(rows)]


class SymbolInsert:
    """Represents a symbol insertion"""
    
    def __init__(self, parent: Any, symbol: Symbol, name: str = "SymbolInsert"):
        self.parent = parent
        self.symbol = symbol
        self.name = name
        self.location = PointUV(0, 0)
        self.is_visible = True


# Type definitions for annotation parents
class IAnnotationParent:
    """Interface for objects that can contain annotations"""
    
    @property
    def notes(self) -> List[Note]:
        """Get the notes"""
        pass
    
    @property
    def barcodes(self) -> List[Barcode]:
        """Get the barcodes"""
        pass
    
    @property
    def tables(self) -> List[Table]:
        """Get the tables"""
        pass
    
    @property
    def datum_feature_symbols(self) -> List[DatumFeatureSymbol]:
        """Get the datum feature symbols"""
        pass
    
    @property
    def symbol_inserts(self) -> List[SymbolInsert]:
        """Get the symbol inserts"""
        pass


class IAnnotationParentMaster(IAnnotationParent):
    """Interface for master annotation parents"""
    pass
