"""지수 백오프(Exponential Backoff)를 사용한 재시도 로직."""
import time
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Callable:
    """
    지수 백오프 재시도 로직을 위한 데코레이터.

    함수 실행 중 예외가 발생하면, 지정된 횟수만큼 지연 시간을 늘려가며 재시도합니다.

    Args:
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 지연 시간 (초)
        max_delay: 최대 지연 시간 (초)
        exponential_base: 지연 시간을 늘릴 때 사용할 밑수
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"{func.__name__} 함수에 대한 최대 재시도 횟수({max_retries})에 도달했습니다.")
                        raise

                    logger.warning(
                        f"{func.__name__} 함수 실행 실패 (시도 {attempt + 1}/{max_retries}): {e}. "
                        f"{delay:.2f}초 후 재시도합니다..."
                    )

                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

            # 이 코드는 실행되지 않아야 하지만, 타입 안전성을 위해 추가
            if last_exception:
                raise last_exception
            raise RuntimeError("재시도 로직에서 예기치 않은 오류 발생")

        return wrapper
    return decorator
