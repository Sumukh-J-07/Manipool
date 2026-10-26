import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Optional

_group_locks: Dict[str, asyncio.Lock] = {}
_master_lock: Optional[asyncio.Lock] = None


def _get_master_lock() -> asyncio.Lock:
    global _master_lock
    if _master_lock is None:
        _master_lock = asyncio.Lock()
    return _master_lock


async def get_group_lock(group_id: str) -> asyncio.Lock:
    master = _get_master_lock()
    async with master:
        if group_id not in _group_locks:
            _group_locks[group_id] = asyncio.Lock()
        return _group_locks[group_id]


@asynccontextmanager
async def group_transaction_lock(group_id: str):
    lock = await get_group_lock(group_id)
    await lock.acquire()
    try:
        yield
    finally:
        lock.release()
