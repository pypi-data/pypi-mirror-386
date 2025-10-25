from __future__ import annotations

from collections.abc import MutableMapping


class CaseInsensitiveDict(MutableMapping[str, str]):
    """A minimal case-insensitive dict implementation for HTTP headers."""

    def __init__(self, data: MutableMapping[str, str] | None = None, **kwargs: str) -> None:
        self._store: dict[str, tuple[str, str]] = {}
        if data:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    def __setitem__(self, key: str, value: str) -> None:
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> str:
        return self._store[key.lower()][1]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self):
        return (orig for orig, _ in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return key.lower() in self._store

    def __repr__(self) -> str:
        return str(dict(self.items()))

    def copy(self) -> "CaseInsensitiveDict":
        new = CaseInsensitiveDict()
        new._store = self._store.copy()
        return new

    def lower_items(self):
        return ((key, value[1]) for key, value in self._store.items())

    def get(self, key: str, default: str | None = None):
        return self._store.get(key.lower(), (None, default))[1]

    def items(self):  # type: ignore[override]
        return ((orig, value) for orig, value in self._store.values())

    def update(self, data=None, **kwargs):  # type: ignore[override]
        if data:
            if hasattr(data, "items"):
                data = data.items()
            for key, value in data:
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value
