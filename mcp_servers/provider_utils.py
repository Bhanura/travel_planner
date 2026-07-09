from typing import Any, Optional

import httpx


def get_json(url: str, params: Optional[dict] = None) -> Any:
    with httpx.Client(timeout=15) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def post_json(url: str, payload: Optional[dict] = None) -> Any:
    with httpx.Client(timeout=15) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def extract_list(data: Any, key: str) -> list[dict]:
    if isinstance(data, dict):
        items = data.get(key, [])
        return items if isinstance(items, list) else []

    if isinstance(data, list):
        return data

    return []

