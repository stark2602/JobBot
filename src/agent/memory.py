"""Short-term scratchpad lives on AgentState; long-term store is SQLite."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

MAX_WORKING_MEMORY_BYTES = 200_000


class MemoryWrite(BaseModel):
    """Proposed long-term write. Logged before commit."""

    key: str
    value: dict[str, Any]
    reason: str


class MemoryPolicy(BaseModel):
    """Evict oversized unsummarized blobs from working memory."""

    max_bytes: int = MAX_WORKING_MEMORY_BYTES
    drop_keys_first: tuple[str, ...] = ("raw_descriptions",)

    def evict(self, working_memory: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of working_memory under the byte budget.

        Drops `drop_keys_first` then truncates string values if still oversized.
        """
        data = dict(working_memory)
        encoded = _size(data)
        if encoded <= self.max_bytes:
            return data
        for key in self.drop_keys_first:
            data.pop(key, None)
            if _size(data) <= self.max_bytes:
                return data
        for key, value in list(data.items()):
            if isinstance(value, str) and len(value) > 500:
                data[key] = value[:500] + "…"
        return data


def _size(payload: dict[str, Any]) -> int:
    return len(repr(payload).encode("utf-8"))


class WorkingMemoryGuard(BaseModel):
    policy: MemoryPolicy = Field(default_factory=MemoryPolicy)

    def apply(self, working_memory: dict[str, Any]) -> dict[str, Any]:
        return self.policy.evict(working_memory)
