"""INISafeDB SDK의 메인 클라이언트 모듈."""
import base64
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    ServerUnavailableException,
    EncryptionFailedException,
    DecryptionFailedException,
    ValidationException,
)
from .retry import exponential_backoff

logger = logging.getLogger(__name__)


class INISafeDBSDK:
    """
    Java 브리지 서버를 통해 데이터베이스 암호화/복호화를 수행하는 클라이언트.

    - Connection Pooling 및 Retry 전략을 포함한 세션 관리
    - 암호화/복호화 메서드 제공
    - 헬스 체크 기능
    - 컨텍스트 관리자(with ... as) 지원

    사용 예시:
        >>> with INISafeDBSDK(base_url="http://localhost:9081") as client:
        ...     encrypted = client.encrypt("user1", "users", "ssn", b"123-45-6789")
        ...     decrypted = client.decrypt("user1", "users", "ssn", encrypted)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:9081",
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
    ):
        """
        INISafeDB SDK 클라이언트를 초기화합니다.

        Args:
            base_url: Java 브리지 서버의 기본 URL (기본값: http://localhost:9081)
            timeout: 요청 타임아웃 (초) (기본값: 30)
            max_retries: 실패한 요청에 대한 최대 재시도 횟수 (기본값: 3)
            verify_ssl: SSL 인증서 검증 여부 (기본값: True)
            pool_connections: 캐시할 커넥션 풀의 수 (기본값: 10)
            pool_maxsize: 커넥션 풀의 최대 크기 (기본값: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl

        # 커넥션 풀링과 재시도 전략을 포함한 세션 생성
        self.session = requests.Session()

        # 연결 오류에 대한 재시도 전략 설정
        # 여기서는 수동으로 재시도를 제어하므로 total=0으로 설정
        retry_strategy = Retry(
            total=0,
            status_forcelist=[500, 502, 503, 504],  # 서버 오류 시 재시도 대상 상태 코드
            allowed_methods=["POST", "GET"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 기본 헤더 설정
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

        logger.info(f"INISafeDBSDK가 다음 URL로 초기화되었습니다: {base_url}")

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HTTP 요청을 보내는 내부 메서드.

        Args:
            method: HTTP 메서드 (GET, POST 등)
            endpoint: API 엔드포인트 경로
            json_data: 요청 본문에 포함될 JSON 데이터

        Returns:
            응답받은 JSON 데이터를 담은 딕셔너리

        Raises:
            ServerUnavailableException: 서버에 연결할 수 없을 때 발생
            ValidationException: 요청 유효성 검사에 실패했을 때 발생
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            # 유효성 검사 오류 확인 (400 Bad Request)
            if response.status_code == 400:
                error_data = response.json()
                raise ValidationException(
                    f"유효성 검사 실패: {error_data.get('message', '알 수 없는 오류')}"
                )

            # 서버 오류 확인 (5xx)
            if response.status_code >= 500:
                raise ServerUnavailableException(
                    f"서버 오류: HTTP {response.status_code}"
                )

            response.raise_for_status()  # 4xx, 5xx 에러 발생 시 예외 발생
            return response.json()

        except requests.exceptions.ConnectionError as e:
            logger.error(f"연결 오류 발생 ({url}): {e}")
            raise ServerUnavailableException(f"서버에 연결할 수 없습니다: {url}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"요청 시간 초과 ({url}): {e}")
            raise ServerUnavailableException(f"요청 시간 초과: {url}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"요청 실패 ({url}): {e}")
            raise ServerUnavailableException(f"요청 실패: {str(e)}") from e

    def health_check(self) -> bool:
        """
        Java 브리지 서버가 정상이고 초기화되었는지 확인합니다.

        Returns:
            서버가 정상이고 SDK가 초기화되었으면 True, 그렇지 않으면 False
        """
        try:
            response = self._request("GET", "/api/v1/health")
            is_healthy = (
                response.get("status") == "UP" and
                response.get("sdkInitialized") is True
            )
            logger.info(f"헬스 체크 결과: {is_healthy}")
            return is_healthy
        except Exception as e:
            logger.warning(f"헬스 체크 실패: {e}")
            return False

    @exponential_backoff(max_retries=3, initial_delay=1.0, max_delay=10.0)
    def encrypt(
        self,
        user_id: str,
        table: str,
        column: str,
        data: bytes
    ) -> bytes:
        """
        Java 브리지 서버를 사용하여 데이터를 암호화합니다.

        Args:
            user_id: 사용자 식별자
            table: 테이블 이름
            column: 컬럼 이름
            data: 암호화할 원본 데이터 (bytes)

        Returns:
            암호화된 데이터 (bytes)

        Raises:
            EncryptionFailedException: 암호화에 실패했을 때 발생
            ServerUnavailableException: 서버에 연결할 수 없을 때 발생
            ValidationException: 요청 유효성 검사에 실패했을 때 발생
        """
        # 데이터를 base64로 인코딩
        base64_data = base64.b64encode(data).decode('utf-8')

        request_data = {
            "userId": user_id,
            "table": table,
            "column": column,
            "data": base64_data,
        }

        logger.debug(f"데이터 암호화 요청: user={user_id}, table={table}, column={column}")

        try:
            response = self._request("POST", "/api/v1/encrypt", json_data=request_data)

            if not response.get("success"):
                raise EncryptionFailedException("암호화 실패: success=false")

            encrypted_base64 = response.get("data")
            if not encrypted_base64:
                raise EncryptionFailedException("응답에 암호화된 데이터가 없습니다.")

            # base64로부터 디코딩
            encrypted_bytes = base64.b64decode(encrypted_base64)
            logger.debug(f"암호화 성공: user={user_id}")
            return encrypted_bytes

        except (ServerUnavailableException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"암호화 처리 중 오류 발생: {e}")
            raise EncryptionFailedException(f"암호화 실패: {str(e)}") from e

    @exponential_backoff(max_retries=3, initial_delay=1.0, max_delay=10.0)
    def decrypt(
        self,
        user_id: str,
        table: str,
        column: str,
        data: bytes
    ) -> bytes:
        """
        Java 브리지 서버를 사용하여 데이터를 복호화합니다.

        Args:
            user_id: 사용자 식별자
            table: 테이블 이름
            column: 컬럼 이름
            data: 복호화할 암호화된 데이터 (bytes)

        Returns:
            복호화된 원본 데이터 (bytes)

        Raises:
            DecryptionFailedException: 복호화에 실패했을 때 발생
            ServerUnavailableException: 서버에 연결할 수 없을 때 발생
            ValidationException: 요청 유효성 검사에 실패했을 때 발생
        """
        # 암호화된 데이터를 base64로 인코딩
        base64_data = base64.b64encode(data).decode('utf-8')

        request_data = {
            "userId": user_id,
            "table": table,
            "column": column,
            "data": base64_data,
        }

        logger.debug(f"데이터 복호화 요청: user={user_id}, table={table}, column={column}")

        try:
            response = self._request("POST", "/api/v1/decrypt", json_data=request_data)

            if not response.get("success"):
                raise DecryptionFailedException("복호화 실패: success=false")

            decrypted_base64 = response.get("data")
            if not decrypted_base64:
                raise DecryptionFailedException("응답에 복호화된 데이터가 없습니다.")

            # base64로부터 디코딩
            decrypted_bytes = base64.b64decode(decrypted_base64)
            logger.debug(f"복호화 성공: user={user_id}")
            return decrypted_bytes

        except (ServerUnavailableException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"복호화 처리 중 오류 발생: {e}")
            raise DecryptionFailedException(f"복호화 실패: {str(e)}") from e

    def close(self) -> None:
        """HTTP 세션을 닫고 리소스를 해제합니다."""
        self.session.close()
        logger.info("INISafeDBSDK가 닫혔습니다.")

    def __enter__(self) -> 'INISafeDBSDK':
        """컨텍스트 관리자 진입 시 호출됩니다."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 관리자 종료 시 호출됩니다."""
        self.close()
