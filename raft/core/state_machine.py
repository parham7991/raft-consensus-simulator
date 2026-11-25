"""ماشین حالت KV — اعمال دستورها بعد از commit (اعمال واقعی در فاز ۴).

دستورها: ``SET k v`` / ``DEL k`` / ``GET k`` (GET بی‌اثر است و فقط برای trace ثبت می‌شود).
"""

from __future__ import annotations


class StateMachine:
    def __init__(self) -> None:
        self._kv: dict[str, str] = {}
        self._applied_log: list[str] = []

    def apply(self, command: str) -> None:
        parts = command.split()
        if not parts:
            raise ValueError("دستور خالی است")
        op = parts[0].upper()
        if op == "SET":
            if len(parts) != 3:
                raise ValueError("شکل درست: SET <key> <value>")
            self._kv[parts[1]] = parts[2]
        elif op == "DEL":
            if len(parts) != 2:
                raise ValueError("شکل درست: DEL <key>")
            self._kv.pop(parts[1], None)
        elif op == "GET":
            if len(parts) != 2:
                raise ValueError("شکل درست: GET <key>")
        else:
            raise ValueError(f"دستور ناشناخته: {op}")
        self._applied_log.append(command)

    def get(self, key: str) -> str | None:
        return self._kv.get(key)

    @property
    def applied_log(self) -> list[str]:
        """ترتیب دستورهای اعمال‌شده — برای assertionهای تست."""
        return list(self._applied_log)
