# PyAnsysV23 - 배포 및 설치 가이드

## 📦 라이브러리 배포 방법

PyAnsysV23 라이브러리를 다른 Python 환경에서도 사용할 수 있도록 배포하는 방법을 설명합니다.

---

## 🚀 방법 1: PyPI에 배포 (권장)

### 1단계: 패키지 준비

PyPI(Python Package Index)에 배포하기 전에 필수 파일들을 확인합니다:

- ✅ `setup.py` - 패키지 설정 (이미 생성됨)
- ✅ `setup.cfg` - 빌드 설정 (이미 생성됨)
- ✅ `MANIFEST.in` - 포함할 파일 목록
- ✅ `README.md` - 프로젝트 설명 (이미 생성됨)
- ✅ `LICENSE` - 라이센스 파일
- ✅ `pyproject.toml` - 현대식 프로젝트 설정

### 2단계: 배포용 도구 설치

```bash
pip install build twine wheel
```

### 3단계: MANIFEST.in 생성

```bash
# MANIFEST.in 파일 내용
include README.md
include LICENSE
include requirements.txt
recursive-include pyansysv23 *.py
recursive-include tests *.py
include examples.py
```

### 4단계: LICENSE 파일 생성

```bash
# MIT 라이센스 선택 또는 자신의 라이센스 생성
```

### 5단계: 패키지 빌드

```bash
python -m build
```

이 명령은 `dist/` 폴더에 다음을 생성합니다:
- `PyAnsysV23-0.23.0-py3-none-any.whl` (바이너리 배포)
- `PyAnsysV23-0.23.0.tar.gz` (소스 배포)

### 6단계: PyPI 계정 생성

1. https://pypi.org 방문
2. 계정 생성 및 이메일 확인
3. API 토큰 생성

### 7단계: PyPI에 업로드

```bash
# 테스트 PyPI에 먼저 업로드
twine upload --repository testpypi dist/*

# 성공하면 실제 PyPI에 업로드
twine upload dist/*
```

### 8단계: 설치 확인

```bash
pip install PyAnsysV23
```

---

## 🐳 방법 2: GitHub + GitHub Actions (자동 배포)

### 1단계: GitHub Repository 생성

```bash
git init
git add .
git commit -m "Initial commit: PyAnsysV23 library"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pyansysv23.git
git push -u origin main
```

### 2단계: GitHub Actions 워크플로우 생성

`.github/workflows/publish.yml` 파일 생성:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### 3단계: PyPI API 토큰 설정

GitHub Settings → Secrets → New repository secret:
- **Name**: `PYPI_API_TOKEN`
- **Value**: PyPI에서 생성한 API 토큰

### 4단계: Release 생성

GitHub → Releases → Create a new release
- Tag: `v0.23.0`
- Release notes 작성

자동으로 PyPI에 배포됩니다!

---

## 📂 방법 3: 개인 저장소 (회사 내부 사용)

### 1단계: 개인 서버에 배포

```bash
# 간단한 HTTP 서버 설정
pip install twine passlib watchdog

# 저장소 초기화
mkdir ~/pypi-repo
cd ~/pypi-repo
```

### 2단계: 패키지 업로드

```bash
twine upload --repository-url http://your-server:8080 dist/*
```

### 3단계: pip에서 설치

```bash
pip install -i http://your-server:8080 PyAnsysV23
```

---

## 🔧 방법 4: Conda 패키지 생성

### 1단계: conda-build 설치

```bash
conda install conda-build conda-verify
```

### 2단계: meta.yaml 생성

`meta.yaml`:
```yaml
package:
  name: pyansysv23
  version: 0.23.0

source:
  path: .

build:
  number: 0
  noarch: python
  script: python -m pip install --no-deps --ignore-installed .

requirements:
  build:
    - python >=3.7
  host:
    - python >=3.7
  run:
    - python >=3.7

test:
  imports:
    - pyansysv23

about:
  home: https://github.com/pyansys/pyansysv23
  license: MIT
  summary: 'Virtual SpaceClaim API V23 library for Python'
```

### 3단계: 패키지 빌드

```bash
conda-build .
```

### 4단계: Anaconda.org에 업로드

```bash
anaconda upload ~/anaconda3/envs/myenv/conda-bld/win-64/pyansysv23-0.23.0-py_0.tar.bz2
```

---

## 📋 배포 체크리스트

배포 전 확인 사항:

```
[ ] setup.py 버전 업데이트
[ ] setup.cfg 메타데이터 확인
[ ] README.md 최신 상태
[ ] CHANGELOG.md 작성
[ ] LICENSE 파일 존재
[ ] pyproject.toml 생성
[ ] MANIFEST.in 생성
[ ] 모든 테스트 통과 (pytest)
[ ] 코드 품질 확인 (flake8, black)
[ ] 타입 체크 (mypy)
[ ] 버전 태그 생성 (git tag v0.23.0)
```

---

## 🎯 배포 전략 비교

| 방법 | 장점 | 단점 | 난이도 |
|------|------|------|--------|
| **PyPI** | 공식, 가장 많은 사용자 | 심사 필요 | 중간 |
| **GitHub** | 소스코드 관리, 자동화 | 별도 구성 필요 | 중간-높음 |
| **개인 저장소** | 보안, 제어 가능 | 유지보수 필요 | 높음 |
| **Conda** | 과학 커뮤니티 | 별도 빌드 필요 | 중간 |

---

## 🔑 PyPI 배포 상세 단계

### 완전한 배포 스크립트

`deploy.sh`:
```bash
#!/bin/bash

# 버전 업데이트
VERSION="0.23.0"
echo "Deploying PyAnsysV23 v$VERSION..."

# 이전 빌드 정리
rm -rf build/ dist/ *.egg-info

# 패키지 빌드
echo "Building package..."
python -m build

# 테스트 PyPI에 업로드
echo "Uploading to TestPyPI..."
python -m twine upload --repository testpypi dist/* --skip-existing

# 확인 대기
echo "Check https://test.pypi.org/project/PyAnsysV23/"
echo "Press Enter to continue to production PyPI..."
read

# PyPI에 업로드
echo "Uploading to PyPI..."
python -m twine upload dist/*

echo "✓ Deployment complete!"
echo "Install with: pip install PyAnsysV23==$VERSION"
```

실행:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📥 설치 방법 (사용자 관점)

배포 후 사용자들이 설치하는 방법:

### PyPI에서 설치
```bash
pip install PyAnsysV23
```

### 특정 버전 설치
```bash
pip install PyAnsysV23==0.23.0
```

### 최신 버전 업그레이드
```bash
pip install --upgrade PyAnsysV23
```

### 특정 Python 버전용 설치
```bash
python3.9 -m pip install PyAnsysV23
```

### 개발 모드 설치 (소스에서)
```bash
cd pyansysv23
pip install -e .
```

---

## 🧪 배포 후 테스트

배포 후 다른 환경에서 테스트:

```bash
# 새로운 가상환경 생성
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 설치
pip install PyAnsysV23

# 테스트
python -c "from pyansysv23 import *; print('✓ Library imported successfully')"
python -m unittest discover -s tests -p "test_*.py"

# 정리
deactivate
rm -rf test_env
```

---

## 📊 버전 관리 전략

### Semantic Versioning (권장)
```
MAJOR.MINOR.PATCH
0.23.0

- MAJOR: API 비호환 변경
- MINOR: 이전 호환 새로운 기능
- PATCH: 버그 수정
```

### 버전 업데이트 절차
```bash
# 1. 코드 변경
# 2. 버전 업데이트
#    - setup.py: version="0.24.0"
#    - setup.cfg: version = 0.24.0
#    - pyansysv23/__init__.py: __version__ = "0.24.0"

# 3. CHANGELOG.md 업데이트
# 4. 테스트 실행
python -m unittest test_pyansysv23

# 5. 커밋 및 태그
git add .
git commit -m "Release v0.24.0"
git tag -a v0.24.0 -m "Version 0.24.0"
git push origin main --tags

# 6. 배포
python -m build
twine upload dist/*
```

---

## 🔐 보안 고려사항

배포 시 보안:

1. **API 토큰 보호**
   - GitHub Secrets에 저장
   - `.env` 파일은 `.gitignore`에 추가
   - 토큰 주기적 갱신

2. **패키지 서명**
   ```bash
   twine upload --sign dist/*
   ```

3. **정보 공개**
   - 민감한 정보 제거
   - LICENSE 명확히
   - 보안 정책 수립

4. **의존성 관리**
   - `requirements.txt` 최소화
   - 신뢰할 수 있는 패키지만 사용
   - 정기적 보안 업데이트

---

## 📞 배포 후 지원

### CHANGELOG.md 유지
```markdown
# Changelog

## [0.24.0] - 2024-10-25
### Added
- 새로운 기능 설명

### Changed
- 변경된 기능 설명

### Fixed
- 버그 수정 설명

## [0.23.0] - 2024-10-23
### Initial Release
- PyAnsysV23 첫 배포
```

### 문제 해결 가이드
```markdown
# FAQ

**Q: 설치 안 됨**
A: pip install --upgrade pip 후 재시도

**Q: 임포트 오류**
A: Python 3.7+ 필요

**Q: 버전 충돌**
A: pip install --force-reinstall PyAnsysV23
```

---

## 🎯 완전한 배포 체크리스트

### 코드 준비
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서 최신화
- [ ] CHANGELOG 작성

### 파일 준비
- [ ] setup.py 확인
- [ ] setup.cfg 확인
- [ ] pyproject.toml 생성
- [ ] MANIFEST.in 생성
- [ ] LICENSE 생성
- [ ] README.md 최신화

### 로컬 테스트
- [ ] `python -m build` 성공
- [ ] `twine check dist/*` 성공
- [ ] 테스트 PyPI 업로드 성공
- [ ] 테스트 환경에서 설치/테스트 성공

### 배포
- [ ] PyPI 계정 준비
- [ ] 버전 태그 생성
- [ ] GitHub에 푸시
- [ ] PyPI 업로드
- [ ] 설치 확인

### 후처리
- [ ] Release note 작성
- [ ] 사용자 알림
- [ ] 모니터링
- [ ] 피드백 수집

---

## 🚀 빠른 시작 배포

한 줄 배포 (이미 준비됨):

```bash
# 1. 버전 확인 및 업데이트
# 2. 빌드 및 배포
python -m build && python -m twine upload dist/*
```

---

## 📚 참고 자료

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [Twine Documentation](https://twine.readthedocs.io/)

---

**다음: 실제 배포하려면 위의 단계들을 따르세요!**
