"""Utility condivise dalle piattaforme Emmeti AQ-IoT."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .const import SPECIAL_ENTITIES


def iter_platform_registers(
    data: list[dict[str, Any]] | None, platform: str
) -> Iterator[tuple[str, Any, Any, str]]:
    """Itera i registri assegnati a una piattaforma.

    Restituisce (group_code, device_id, thing_id, r_code) deduplicando su
    device_id + r_code: lo stesso registro puo' comparire in piu' gruppi dello
    stesso dispositivo e va esposto una volta sola.
    """
    seen: set[tuple[Any, str]] = set()
    for group in data or []:
        group_code = group.get("groupCode")
        if not group_code:
            continue
        device_id = group.get("deviceId")
        thing_id = group.get("thingId")
        for r_code in group.get("data") or {}:
            if SPECIAL_ENTITIES.get(r_code) != platform:
                continue
            key = (device_id, r_code)
            if key in seen:
                continue
            seen.add(key)
            yield group_code, device_id, thing_id, r_code
