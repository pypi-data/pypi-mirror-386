# INISafeDB SDK (Python)

데이터베이스 암호화를 위한 Python 클라이언트 라이브러리

## 개요

Java Bridge Server를 호출하여 데이터베이스 암호화/복호화 기능을 제공하는 Python SDK입니다.

## 기술 스택

- Python 3.8+
- Poetry (패키지 관리)
- requests (HTTP 클라이언트)

## 설치

```bash
pip install ini-safedb-sdk
```

## 사용 예제

```python
from ini_safedb_sdk import INISafeDBSDK

# 클라이언트 초기화
with INISafeDBSDK(base_url="http://localhost:9081") as client:
    # 암호화
    encrypted = client.encrypt("user1", "users", "ssn", b"123-45-6789")

    # 복호화
    decrypted = client.decrypt("user1", "users", "ssn", encrypted)
    print(decrypted.decode('utf-8'))
```

## 시작하기

상세한 개발 가이드는 [PHASE2_PYTHON_SDK.md](../docs/PHASE2_PYTHON_SDK.md)를 참조하세요.

## 개발

```bash
# 의존성 설치
poetry install

# 테스트
poetry run pytest

# 빌드
poetry build
```

## PyPI 배포

```bash
poetry publish
```
