from typing import TypedDict, Callable, Optional, Any


class RouteInfo(TypedDict, total=False):
    """
    if the incoming message has route attribute equal to `loadNode` then the on_load_node method will be called automatically.
    no more need to parse the message to recognize what has to be done.
    """
    route: str
    """
    any function that takes headers and payload, and loads the data from it.
    deserializing can be considered as good candidate.
    another example is to fetch the entity_id from headers and load the entity using it.
    """
    hydrate: Optional[Callable[[dict[str, str],Any], Any]]
    """
    the duty of dehydrate function is to get an object and serialize it as string or dict (no complex object included).
    PS. the dehydrate function runs only if status code is successful (200 series)
    """
    dehydrate: Optional[Callable]