"""DB Crypto SDK에서 사용하는 커스텀 예외 클래스."""


class DBCryptoException(Exception):
    """모든 DB Crypto SDK 관련 예외의 기본 클래스."""
    pass


class ServerUnavailableException(DBCryptoException):
    """Java 브리지 서버에 연결할 수 없을 때 발생하는 예외."""
    pass


class EncryptionFailedException(DBCryptoException):
    """암호화 작업이 실패했을 때 발생하는 예외."""
    pass


class DecryptionFailedException(DBCryptoException):
    """복호화 작업이 실패했을 때 발생하는 예외."""
    pass


class ValidationException(DBCryptoException):
    """요청 파라미터의 유효성 검사에 실패했을 때 발생하는 예외."""
    pass


class ServerInitializationException(DBCryptoException):
    """서버가 제대로 초기화되지 않았을 때 발생하는 예외."""
    pass
