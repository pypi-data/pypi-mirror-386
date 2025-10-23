from abc import ABC, abstractmethod
from typing import List

from .route_info import RouteInfo


class AbstractSocketRouter(ABC):
    _routes: List[RouteInfo] = []

    @property
    def routes(self) -> List[RouteInfo]:
        return self._routes

    """
    this method can simply be overridden by passing an array of RouteInfo objects like this:
    @routes.setter
    def routes(self, routes: List[RouteInfo]):
        self._routes = [
            {route: 'sayHello'}, # hydrate and dehydrate functions are optional
            {route: 'getArticles', dehydrate: multi_article_serializer}
        ]

    though this approach is simple, I highly recommend you to put this list in a `SOME.env` file, so it can be shared by both Django and React-based frontend.
    """

    @routes.setter
    @abstractmethod
    def routes(self, routes: List[RouteInfo]):
        pass

    def _get_route(self, route: str) -> RouteInfo | None:
        for route_info in self.routes:
            if route_info['route'] == route:
                return route_info
        return None
