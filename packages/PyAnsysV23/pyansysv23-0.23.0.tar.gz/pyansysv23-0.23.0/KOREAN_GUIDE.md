# PyAnsysV23 라이브러리 - 설치 및 사용 가이드

## 📋 개요

**PyAnsysV23**는 SpaceClaim V23 API의 가상 Python 라이브러리입니다. SpaceClaim이 설치되지 않은 환경에서도 SpaceClaim 자동화 스크립트를 작성, 테스트, 학습할 수 있습니다.

## 🎯 주요 기능

### 8개의 핵심 모듈

| 모듈 | 설명 |
|------|------|
| **geometry** | 3D 기하학 (점, 벡터, 평면, 행렬 변환) |
| **modeler** | 3D 모델링 (상자, 구, 원통, 원뿔 등) |
| **document** | 문서, 부품, 어셈블리 관리 |
| **annotation** | 주석 (텍스트, 기호, 바코드) |
| **analysis** | FEA 메시 및 분석 |
| **instance** | 컴포넌트 인스턴스 및 발생 |
| **extensibility** | 애드인 개발 프레임워크 |
| **core** | 명령 시스템 및 애플리케이션 제어 |

## 📦 설치

### 1. 라이브러리 복사
```bash
# 이미 c:\Users\Public\PythonProject\PyAnsys 경로에 설치됨
```

### 2. Python 경로 설정
```python
import sys
sys.path.insert(0, r'c:\Users\Public\PythonProject\PyAnsys')
```

### 3. 임포트
```python
from pyansysv23.geometry import Point, Vector
from pyansysv23.modeler import Modeler
# ... 등
```

## 🚀 빠른 시작

### 예제 1: 기하학적 프리미티브 생성

```python
from pyansysv23.geometry import Point, Vector, Plane
from pyansysv23.modeler import Modeler

# 점과 벡터 생성
origin = Point(0, 0, 0)
box_center = Point(1, 1, 1)

# 거리 계산
distance = origin.distance_to(box_center)
print(f"거리: {distance:.3f}")

# 3D 모양 생성
box = Modeler.create_box(Point(0, 0, 0), 1, 1, 1)
sphere = Modeler.create_sphere(Point(2, 0, 0), 0.5)
cylinder = Modeler.create_cylinder(Point(0, 2, 0), 1, 0.3)

print(f"상자 부피: {box.master.volume}")
print(f"구 부피: {sphere.master.volume:.4f}")
```

### 예제 2: 문서 및 부품 작업

```python
from pyansysv23.document import Document, Part
from pyansysv23.modeler import Modeler
from pyansysv23.geometry import Point

# 문서 생성
doc = Document("MyDesign.scdoc")

# 부품 생성
part = Part("Part1")

# 모양을 부품에 추가
box = Modeler.create_box(Point(0, 0, 0), 2, 1, 1)
part.add_design_body(box)

# 부품을 문서에 추가
doc.add_part(part)

# 저장
doc.save(r"C:\designs\MyDesign.scdoc")
print(f"문서 저장: {doc.name}")
```

### 예제 3: 명령 및 애드인

```python
from pyansysv23.core import Command, WriteBlock
from pyansysv23.extensibility import AddIn, ICommandExtensibility

# 명령 생성
cmd = Command.create("MyAddIn.MyCommand", "내 명령", "사용자 정의 명령")

def on_execute(context):
    print("명령 실행됨!")

cmd.add_executing_handler(on_execute)

# 쓰기 블록 내에서 실행
def my_task():
    print("수정 작업 수행 중...")

WriteBlock.ExecuteTask("내 작업", my_task)

# 애드인 클래스
class MyAddIn(AddIn, ICommandExtensibility):
    def initialize(self) -> None:
        cmd = Command.create("MyAddIn.CreateBox")
        cmd.text = "박스 생성"
    
    def get_custom_ui(self) -> str:
        return '''<?xml version="1.0"?>
<customUI xmlns="http://schemas.spaceclaim.com/customui">
    <ribbon>
        <tabs>
            <tab id="MyAddIn.Tab" label="내 애드인">
                <group id="MyAddIn.Group" label="기하학">
                    <button id="MyAddIn.CreateBox" command="MyAddIn.CreateBox"/>
                </group>
            </tab>
        </tabs>
    </ribbon>
</customUI>'''

addin = MyAddIn()
addin.connect()
addin.initialize()
```

### 예제 4: 주석 추가

```python
from pyansysv23.annotation import (
    Note, Barcode, BarcodeType, QRCodeErrorCorrectionLevel
)
from pyansysv23.geometry import PointUV
from pyansysv23.document import DrawingSheet

# 도면 시트 생성
sheet = DrawingSheet("Drawing1", 0.297, 0.21)  # A4 크기

# 텍스트 노트 추가
note = Note(sheet, "이것은 테스트 노트입니다", PointUV(0.1, 0.1))
note.font_size = 14
note.bold = True

# QR 코드 추가
qr_code = Barcode.create(
    sheet,
    PointUV(0.2, 0.2),
    BarcodeType.QRCode,
    "https://example.com"
)
print(f"QR 코드 유효: {qr_code.is_valid}")

# 데이터 매트릭스 추가
data_matrix = Barcode.create(
    sheet,
    PointUV(0.3, 0.2),
    BarcodeType.DataMatrix,
    "12345"
)
```

### 예제 5: 메시 작업

```python
from pyansysv23.analysis import (
    BodyMesh, MeshNode, MeshBodySettings, HexaBlocking
)
from pyansysv23.geometry import Point
from pyansysv23.modeler import Modeler

# 박스 생성 및 메시 설정
box = Modeler.create_box(Point(0, 0, 0), 1, 1, 1)
mesh_settings = MeshBodySettings.create(box)
mesh_settings.element_size = 0.01

# 바디 메시 생성
body_mesh = BodyMesh(box)

# 노드 추가
for i in range(10):
    node = MeshNode(i, Point(i * 0.1, 0, 0))
    body_mesh.nodes.append(node)

print(f"메시 노드 수: {body_mesh.node_count}")

# 헥사 블로킹
hexa = HexaBlocking()
success, error = hexa.process_command_with_error("HEXA QUADS 100")
print(f"명령 결과: 성공={success}, 에러='{error}'")
```

## 📚 클래스 및 메서드

### Geometry 모듈

```python
Point(x, y, z)              # 3D 점
Point.distance_to(other)    # 거리 계산

Vector(x, y, z)             # 3D 벡터
Vector.magnitude()          # 크기
Vector.normalize()          # 정규화
Vector.dot(other)           # 내적
Vector.cross(other)         # 외적

Plane.xy(), Plane.yz(), Plane.xz()  # 표준 평면
Plane.distance_to_point()   # 점까지의 거리
Plane.project_point()       # 평면에 점 투영

Matrix.identity()           # 항등 행렬
Matrix.translation(dx, dy, dz)      # 이동 행렬
Matrix.scale(sx, sy, sz)            # 스케일 행렬
Matrix.rotation_x/y/z(angle)        # 회전 행렬
Matrix.transform_point(point)       # 점 변환
```

### Modeler 모듈

```python
Modeler.create_box(origin, length, width, height)
Modeler.create_sphere(center, radius)
Modeler.create_cylinder(base, height, radius)
Modeler.create_cone(base, height, radius)

DesignBody.master           # 마스터 바디
DesignBody.copy()           # 복사
```

### Document 모듈

```python
Document(name)              # 문서 생성
Document.add_part(part)     # 부품 추가
Document.save(file_path)    # 저장

Part(name)                  # 부품 생성
Part.add_design_body(body)  # 바디 추가
Part.design_bodies          # 모든 바디 가져오기

DrawingSheet(name, width, height)  # 도면 시트
```

### Annotation 모듈

```python
Note(parent, text, location)        # 텍스트 노트
Barcode.create(parent, location, type, data)  # 바코드
BarcodeType.QRCode, .DataMatrix, .Code39 등  # 바코드 타입

CheckDigitType.Standard, .Mod10 등          # 체크 디지트
QRCodeErrorCorrectionLevel.Low, .Medium, .High  # 오류 수정 수준
```

### Analysis 모듈

```python
MeshNode(id, point)         # 메시 노드
BodyMesh(body)              # 바디 메시
PartMesh()                  # 부품 메시
AssemblyMesh()              # 어셈블리 메시

MeshBodySettings.create(body)  # 메시 설정 생성
HexaBlocking()              # 헥사 블로킹
```

### Core 모듈

```python
Command.create(name, text, hint)    # 명령 생성
Command.get_command(name)           # 명령 가져오기
Command.add_executing_handler()     # 실행 핸들러 추가

WriteBlock.ExecuteTask(text, task)  # 쓰기 블록에서 실행
```

### Extensibility 모듈

```python
AddIn                       # 애드인 기본 클래스
AddIn.connect()             # 연결
AddIn.disconnect()          # 연결 해제
AddIn.get_instance(type)    # 인스턴스 가져오기

CommandCapsule              # 명령 캡슐 기본 클래스
CommandCapsule.initialize() # 초기화
```

## 🧪 테스트 실행

```bash
# 모든 테스트 실행
python -m unittest test_pyansysv23 -v

# 특정 테스트 클래스 실행
python -m unittest test_pyansysv23.TestGeometry -v

# 특정 테스트 메서드 실행
python -m unittest test_pyansysv23.TestGeometry.test_point_distance -v
```

## 📝 예제 스크립트

프로젝트에 포함된 `examples.py` 파일:

```bash
python examples.py
```

모든 7개의 예제가 실행됩니다:
1. 기하학 생성
2. 3D 바디 생성
3. 문서 작업
4. 명령 생성
5. 주석 추가
6. 메시 작업
7. 애드인 생성

## 📖 추가 참고 자료

프로젝트 폴더의 공식 문서:
- `API_Class_Library.chm` - 완전한 API 참조
- `Developers Guide.pdf` - 개발 가이드
- `Building Sample Add-Ins.pdf` - 애드인 예제
- `README.md` - 영문 설명서

## 🔍 지원되는 바코드 타입

- **1D 바코드**: Code25, Code39, Code93, Code11, Code128, EAN, UPC
- **2D 바코드**: QR Code, Data Matrix, PDF417, Aztec
- **특수**: ISBN, ISMN, ISSN, LOGMARS, VIN

## 💡 팁과 요령

### 1. 원래 거리 계산
```python
from pyansysv23.geometry import Point
import math

p1 = Point(0, 0, 0)
p2 = Point(3, 4, 0)
distance = p1.distance_to(p2)  # 5.0
```

### 2. 부품의 모든 바디 순회
```python
for body in part.design_bodies:
    print(f"{body.name}: 부피={body.master.volume}")
```

### 3. 명령 유효성 확인
```python
cmd = Command.get_command("MyCommand")
if cmd and cmd.is_enabled:
    cmd.execute()
```

### 4. 바디 복사
```python
original = Modeler.create_sphere(Point(0, 0, 0), 1)
copy = original.copy()
copy.color = (255, 0, 0)  # 빨간색
```

## ⚠️ 주의사항

- **가상 라이브러리**: 이 라이브러리는 실제 SpaceClaim과 상호작용하지 않습니다.
- **교육 목적**: SpaceClaim API 학습 및 스크립트 개발에 사용됩니다.
- **실제 자동화**: 프로덕션 SpaceClaim 자동화는 공식 SDK를 사용하세요.

## 🔧 문제 해결

### 임포트 오류
```python
import sys
sys.path.insert(0, r'c:\Users\Public\PythonProject\PyAnsys')
from pyansysv23 import *
```

### 모듈 찾기 실패
```bash
# Python 경로 확인
python -c "import sys; print(sys.path)"

# 또는 직접 설정
export PYTHONPATH="${PYTHONPATH}:c:/Users/Public/PythonProject/PyAnsys"
```

## 📞 지원

- 공식 SpaceClaim 문서: SpaceClaim API Reference
- ANSYS 웹사이트: www.ansys.com
- PyAnsys 프로젝트: github.com/pyansys

---

**버전**: 0.23.0
**Python**: 3.7+
**플랫폼**: Windows
**라이센스**: MIT (교육용)

---

## 다음 단계

1. `examples.py` 실행해서 작동 확인
2. `test_pyansysv23.py`의 테스트 코드 학습
3. 자신의 스크립트 작성 시작
4. 공식 API 문서와 비교하면서 확장

즐거운 코딩되세요! 🚀
