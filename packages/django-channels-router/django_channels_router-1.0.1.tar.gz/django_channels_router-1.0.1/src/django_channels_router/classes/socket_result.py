from typing import TypedDict, Optional


class SocketResult(TypedDict, total=False):
    headers: Optional[dict[str, str]]
    payload: Optional[dict | str]
    status: Optional[int]
