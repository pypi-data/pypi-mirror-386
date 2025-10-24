"""요청 및 응답에 사용되는 데이터 모델."""
from typing import Optional
from dataclasses import dataclass


@dataclass
class EncryptRequest:
    """암호화 요청 모델."""
    user_id: str  # 사용자 ID
    table: str    # 테이블 이름
    column: str   # 컬럼 이름
    data: str     # Base64로 인코딩된 원본 데이터


@dataclass
class DecryptRequest:
    """복호화 요청 모델."""
    user_id: str  # 사용자 ID
    table: str    # 테이블 이름
    column: str   # 컬럼 이름
    data: str     # Base64로 인코딩된 암호화된 데이터


@dataclass
class CryptoResponse:
    """암호화/복호화 작업의 응답 모델."""
    success: bool  # 작업 성공 여부
    data: str      # Base64로 인코딩된 결과 데이터


@dataclass
class ErrorResponse:
    """서버 에러 응답 모델."""
    error: str                # 에러 유형 코드
    message: str              # 에러 메시지
    details: Optional[str] = None  # 에러 상세 정보
