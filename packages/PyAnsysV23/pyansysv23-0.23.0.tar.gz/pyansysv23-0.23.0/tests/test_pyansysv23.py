"""
Unit tests for PyAnsysV23 library
"""

import unittest
from pyansysv23.geometry import Point, Vector, Plane, Matrix, PointUV
from pyansysv23.modeler import Body, DesignBody, Modeler, Face, Edge, Vertex
from pyansysv23.document import Document, Part, Assembly, DrawingSheet
from pyansysv23.annotation import Note, Barcode, BarcodeType, Symbol
from pyansysv23.analysis import BodyMesh, MeshNode, AnalysisAspect, HexaBlocking
from pyansysv23.instance import Component, Occurrence, Instance
from pyansysv23.core import Command, WriteBlock, ExecutionContext
from pyansysv23.extensibility import AddIn, CommandCapsule
import math


class TestGeometry(unittest.TestCase):
    """Test geometric operations"""
    
    def test_point_creation(self):
        """Test point creation"""
        p = Point(1, 2, 3)
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 2)
        self.assertEqual(p.z, 3)
    
    def test_point_distance(self):
        """Test distance calculation"""
        p1 = Point(0, 0, 0)
        p2 = Point(1, 0, 0)
        self.assertEqual(p1.distance_to(p2), 1)
        
        p3 = Point(3, 4, 0)
        p4 = Point(0, 0, 0)
        self.assertEqual(p3.distance_to(p4), 5)
    
    def test_vector_magnitude(self):
        """Test vector magnitude"""
        v = Vector(3, 4, 0)
        self.assertEqual(v.magnitude(), 5)
    
    def test_vector_normalize(self):
        """Test vector normalization"""
        v = Vector(3, 4, 0)
        normalized = v.normalize()
        self.assertAlmostEqual(normalized.magnitude(), 1.0)
    
    def test_vector_dot_product(self):
        """Test dot product"""
        v1 = Vector(1, 0, 0)
        v2 = Vector(1, 0, 0)
        self.assertEqual(v1.dot(v2), 1)
    
    def test_vector_cross_product(self):
        """Test cross product"""
        v1 = Vector(1, 0, 0)
        v2 = Vector(0, 1, 0)
        cross = v1.cross(v2)
        self.assertEqual(cross.z, 1)
    
    def test_plane_xy(self):
        """Test XY plane creation"""
        plane = Plane.xy()
        self.assertIsNotNone(plane)
        self.assertEqual(plane.normal.z, 1)
    
    def test_matrix_identity(self):
        """Test identity matrix"""
        m = Matrix.identity()
        p = Point(1, 2, 3)
        p_transformed = m.transform_point(p)
        self.assertEqual(p_transformed.x, 1)
        self.assertEqual(p_transformed.y, 2)
        self.assertEqual(p_transformed.z, 3)
    
    def test_matrix_translation(self):
        """Test translation matrix"""
        m = Matrix.translation(1, 2, 3)
        p = Point(0, 0, 0)
        p_translated = m.transform_point(p)
        self.assertEqual(p_translated.x, 1)
        self.assertEqual(p_translated.y, 2)
        self.assertEqual(p_translated.z, 3)


class TestModeler(unittest.TestCase):
    """Test 3D modeling operations"""
    
    def test_body_creation(self):
        """Test body creation"""
        body = Body("TestBody")
        self.assertEqual(body.name, "TestBody")
        self.assertTrue(body.is_solid)
    
    def test_design_body_creation(self):
        """Test design body creation"""
        design_body = DesignBody(name="TestDesignBody")
        self.assertEqual(design_body.name, "TestDesignBody")
        self.assertIsNotNone(design_body.master)
    
    def test_box_creation(self):
        """Test box creation"""
        box = Modeler.create_box(Point(0, 0, 0), 1, 2, 3)
        self.assertEqual(box.master.volume, 6.0)
    
    def test_sphere_creation(self):
        """Test sphere creation"""
        sphere = Modeler.create_sphere(Point(0, 0, 0), 1)
        expected_volume = (4/3) * math.pi
        self.assertAlmostEqual(sphere.master.volume, expected_volume, places=5)
    
    def test_cylinder_creation(self):
        """Test cylinder creation"""
        cylinder = Modeler.create_cylinder(Point(0, 0, 0), 2, 1)
        expected_volume = math.pi * 2
        self.assertAlmostEqual(cylinder.master.volume, expected_volume, places=5)
    
    def test_vertex_creation(self):
        """Test vertex creation"""
        v = Vertex(Point(1, 2, 3))
        self.assertEqual(v.location.x, 1)
    
    def test_edge_creation(self):
        """Test edge creation"""
        v1 = Vertex(Point(0, 0, 0))
        v2 = Vertex(Point(1, 0, 0))
        edge = Edge(v1, v2)
        self.assertEqual(edge.length, 1)


class TestDocument(unittest.TestCase):
    """Test document operations"""
    
    def test_document_creation(self):
        """Test document creation"""
        doc = Document("TestDoc")
        self.assertEqual(doc.name, "TestDoc")
    
    def test_part_creation(self):
        """Test part creation"""
        part = Part("TestPart")
        self.assertEqual(part.name, "TestPart")
    
    def test_part_body_management(self):
        """Test adding bodies to part"""
        part = Part("TestPart")
        body = Modeler.create_box(Point(0, 0, 0), 1, 1, 1)
        part.add_design_body(body)
        self.assertEqual(len(part.design_bodies), 1)
    
    def test_assembly_creation(self):
        """Test assembly creation"""
        assembly = Assembly("TestAssembly")
        self.assertEqual(assembly.name, "TestAssembly")
    
    def test_drawing_sheet_creation(self):
        """Test drawing sheet creation"""
        sheet = DrawingSheet("TestSheet")
        self.assertEqual(sheet.name, "TestSheet")


class TestAnnotation(unittest.TestCase):
    """Test annotation operations"""
    
    def test_note_creation(self):
        """Test note creation"""
        sheet = DrawingSheet()
        note = Note(sheet, "Test Note", PointUV(0.1, 0.1))
        self.assertEqual(note.text, "Test Note")
    
    def test_barcode_creation(self):
        """Test barcode creation"""
        sheet = DrawingSheet()
        barcode = Barcode.create(
            sheet,
            PointUV(0.1, 0.1),
            BarcodeType.Code39,
            "TESTDATA"
        )
        self.assertEqual(barcode.data, "TESTDATA")
    
    def test_barcode_validation(self):
        """Test barcode validation"""
        sheet = DrawingSheet()
        barcode = Barcode.create(
            sheet,
            PointUV(0.1, 0.1),
            BarcodeType.Ean13,
            "1234567890128"
        )
        self.assertTrue(barcode.is_valid)


class TestAnalysis(unittest.TestCase):
    """Test analysis and meshing operations"""
    
    def test_mesh_node_creation(self):
        """Test mesh node creation"""
        node = MeshNode(1, Point(0, 0, 0))
        self.assertEqual(node.id, 1)
        self.assertEqual(node.Point.x, 0)
    
    def test_body_mesh_creation(self):
        """Test body mesh creation"""
        box = Modeler.create_box(Point(0, 0, 0), 1, 1, 1)
        mesh = BodyMesh(box)
        self.assertEqual(mesh.node_count, 0)
    
    def test_body_mesh_nodes(self):
        """Test adding nodes to body mesh"""
        box = Modeler.create_box(Point(0, 0, 0), 1, 1, 1)
        mesh = BodyMesh(box)
        
        for i in range(5):
            node = MeshNode(i, Point(i * 0.25, 0, 0))
            mesh.nodes.append(node)
        
        self.assertEqual(mesh.node_count, 5)
    
    def test_hexa_blocking(self):
        """Test hexa blocking"""
        hexa = HexaBlocking()
        success, error = hexa.process_command_with_error("TEST COMMAND")
        self.assertTrue(success)
    
    def test_analysis_aspect(self):
        """Test analysis aspect"""
        aspect = AnalysisAspect()
        self.assertIsNotNone(aspect.shared_face_groups)


class TestCommands(unittest.TestCase):
    """Test command operations"""
    
    def test_command_creation(self):
        """Test command creation"""
        cmd = Command.create("TestCommand", "Test Command", "Test hint")
        self.assertEqual(cmd.name, "TestCommand")
        self.assertEqual(cmd.text, "Test Command")
    
    def test_command_retrieval(self):
        """Test command retrieval"""
        cmd1 = Command.create("TestCommand2")
        cmd2 = Command.get_command("TestCommand2")
        self.assertEqual(cmd1, cmd2)
    
    def test_write_block(self):
        """Test write block"""
        executed = False
        
        def task():
            nonlocal executed
            executed = True
        
        result = WriteBlock.ExecuteTask("Test Task", task)
        self.assertTrue(executed)
        self.assertTrue(result)


class TestExtensibility(unittest.TestCase):
    """Test add-in extensibility"""
    
    def test_addin_creation(self):
        """Test add-in creation"""
        class TestAddIn(AddIn):
            def connect(self):
                return True
            
            def disconnect(self):
                pass
        
        addin = TestAddIn()
        self.assertIsNotNone(addin)
        self.assertTrue(addin.connect())
    
    def test_command_capsule(self):
        """Test command capsule"""
        capsule = CommandCapsule("TestCapsule", "Test", None, "Test Capsule")
        capsule.initialize()
        self.assertIsNotNone(capsule.command)


class TestInstance(unittest.TestCase):
    """Test instance and component operations"""
    
    def test_component_creation(self):
        """Test component creation"""
        comp = Component("TestComponent")
        self.assertEqual(comp.name, "TestComponent")
    
    def test_occurrence_creation(self):
        """Test occurrence creation"""
        comp = Component("TestComponent")
        occ = Occurrence(comp, "TestOccurrence")
        self.assertEqual(occ.component, comp)
    
    def test_occurrence_hierarchy(self):
        """Test occurrence hierarchy"""
        comp = Component("TestComponent")
        parent = Occurrence(comp, "Parent")
        child = Occurrence(comp, "Child")
        
        parent.add_child(child)
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(child.parent, parent)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_complete_workflow(self):
        """Test complete design workflow"""
        # Create document and part
        doc = Document("DesignDoc")
        part = Part("MainPart")
        
        # Create bodies
        box = Modeler.create_box(Point(0, 0, 0), 1, 1, 1)
        sphere = Modeler.create_sphere(Point(2, 0, 0), 0.5)
        
        # Add to part
        part.add_design_body(box)
        part.add_design_body(sphere)
        
        # Add to document
        doc.add_part(part)
        
        # Verify
        self.assertEqual(len(doc.parts), 1)
        self.assertEqual(len(part.design_bodies), 2)
        self.assertAlmostEqual(box.master.volume, 1.0)


if __name__ == "__main__":
    unittest.main()
