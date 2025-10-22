# GamlSet

Type집합을 만드는 라이브러리 입니다.

[![Python Version](https://img.shields.io/pypi/pyversions/gamlset.svg)](https://pypi.org/project/gamlset/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 설치

```bash
pip install gamlset
```

## 소개

유연하고 가독성 좋은 Type 생성 및 grouping을 돕습니다.

## 사용법

```python
# 기존 방식
class OldTypeSet:
    class OldTypeFeild_1:
        pass
    class OldTypeFeild_2:
        pass

# GamlSet
class GamlTypeSet(GamlSet):
    GamlType_1 = GamlType # GamlTypeSet__GamlType1
    GamlType_2 = GamlType # GamlTypeSet__GamlType2
```

사용 예시들은 `examlple/`을 참고하세요.

## 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/gamultong/gamlset.git
cd gamlset

# 개발 의존성 설치
pip install -e ".[dev]"

# 테스트 실행
python -m tests.run
```

## 빌드 및 배포

```bash
# 빌드
python setup.py sdist bdist_wheel

# PyPI 업로드
pip install twine
twine upload dist/*
```

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
