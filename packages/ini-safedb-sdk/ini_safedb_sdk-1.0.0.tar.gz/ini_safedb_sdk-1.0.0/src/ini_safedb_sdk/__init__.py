"""
INISafeDB SDK

데이터베이스 암호화/복호화를 위한 Python 클라이언트 라이브러리입니다.
이 패키지는 Java 브리지 서버와 통신하여 실제 암호화 작업을 수행합니다.
"""

from .client import INISafeDBSDK
from .exceptions import (
    DBCryptoException,
    ServerUnavailableException,
    EncryptionFailedException,
    DecryptionFailedException,
    ValidationException,
    ServerInitializationException,
)

__version__ = "1.0.0"
__all__ = [
    "INISafeDBSDK",
    "DBCryptoException",
    "ServerUnavailableException",
    "EncryptionFailedException",
    "DecryptionFailedException",
    "ValidationException",
    "ServerInitializationException",
]
