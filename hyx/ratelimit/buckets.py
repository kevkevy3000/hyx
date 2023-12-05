import asyncio
from typing import Optional

from hyx.ratelimit.exceptions import EmptyBucket


class TokenBucket:
    """
    Token Bucket Logic
    Replenish tokens as time passes on. If tokens are available, executions can be allowed.
    Otherwise, it's going to be rejected with an EmptyBucket error
    """

    __slots__ = (
        "_max_executions",
        "_per_time_secs",
        "_bucket_size",
        "_loop",
        "_token_per_secs",
        "_tokens",
        "_next_replenish_at",
    )

    def __init__(self, max_executions: float, per_time_secs: float, bucket_size: Optional[float] = None) -> None:
        self._max_executions = max_executions
        self._per_time_secs = per_time_secs

        self._bucket_size = bucket_size if bucket_size else max_executions

        self._loop = asyncio.get_running_loop()
        self._token_per_secs = self._per_time_secs / self._max_executions

        self._tokens = self._bucket_size
        self._next_replenish_at = self._loop.time() + self._token_per_secs

    @property
    def tokens(self) -> float:
        self._replenish()
        return self._tokens

    @property
    def empty(self) -> bool:
        self._replenish()
        return self._tokens <= 0

    async def take(self) -> None:
        if not self.empty:
            self._tokens -= 1
            return

        now = self._loop.time()

        next_replenish = self._next_replenish_at
        until_next_replenish = next_replenish - now

        if until_next_replenish > 0:
            raise EmptyBucket

        tokens_to_add = min(self._bucket_size, 1 + abs(until_next_replenish / self._token_per_secs))

        self._next_replenish_at = max(
            next_replenish + tokens_to_add * self._token_per_secs,
            now + self._token_per_secs,
        )

        self._tokens = tokens_to_add - 1
        return

    def _replenish(self) -> None:
        now = self._loop.time()

        next_replenish = self._next_replenish_at
        until_next_replenish = next_replenish - now

        if until_next_replenish > 0:
            return

        tokens_to_add = min(self._bucket_size, 1 + abs(until_next_replenish / self._token_per_secs))
        self._next_replenish_at = max(
            next_replenish + tokens_to_add * self._token_per_secs,
            now + self._token_per_secs,
        )
        self._tokens = tokens_to_add
        return
