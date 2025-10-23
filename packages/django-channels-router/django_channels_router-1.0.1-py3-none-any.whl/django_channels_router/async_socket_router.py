from django.contrib.auth import get_user_model

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import StatusCodes, SocketResult, BaseMessage, AbstractSocketRouter, RouteInfo
from .tools import route_to_method_name, result_is_successful

User = get_user_model()


class AsyncSocketRouterConsumer(AsyncJsonWebsocketConsumer, AbstractSocketRouter):
    """
    To implement this class, you'll need to implement this method:

    @routes.setter
    @abstractmethod
    def routes (self, routes: List[RouteInfo]):
        pass

    This method can simply be overridden by passing an array of RouteInfo objects like this:
    @routes.setter
    def routes (self, routes: List[RouteInfo]):
        self._routes = [
            {route: 'sayHello'}, # hydrate and dehydrate functions are optional
            {route: 'getArticles', dehydrate: multi_article_serializer}
        ]

    Though this approach is straightforward, I highly recommend you to put this list in a `SOME.env` file, so it can be shared by both Django and React-based frontend.

    Then, if you have a route like `sayHello`,
    your consumer will need to have a method named on_say_hello, and there you can define the code you expect to be executed when sayHello is called.

    So when in the frontend you call sayHello route, the code in on_say_hello will be executed automatically.

    Read more in README.md about how it facilitates the entire process, using hydrate and dehydrate functions.
    """

    _user = None

    @property
    def user(self) -> User:
        return self._user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self):
        self._user = self.scope['user']
        await self.accept()

    async def receive_json(self, content, **kwargs):
        message: BaseMessage
        try:
            message = BaseMessage.from_incoming_message(content)
            if message.route == 'PING':  # only heart-bit checks, response, so the client makes sure the connection is open
                await self.send_json(
                    BaseMessage(
                        route='PING',
                        uuid=message.uuid
                    ).serialize()
                )
                return

            # find route
            route_info: RouteInfo | None = self._get_route(message.route)
            if not route_info:
                await self.send_json(
                    BaseMessage.build_response(message, None, None, StatusCodes.NOT_FOUND).serialize()
                )
                return

            # find method
            method_name = route_to_method_name(route_info['route'])
            method = getattr(self, method_name)  # if the method doesn't exist, an exception will be raised

            # hydrate the payload if the function is provided
            payload = await route_info['hydrate'](message.headers, message.payload) if route_info.get('hydrate', False) else message.payload

            result: SocketResult = await method(payload, message.headers)

            should_dehydrate = route_info.get('dehydrate', False) and result_is_successful(result['status'])
            out_payload = await route_info['dehydrate'](result['payload']) if should_dehydrate else result['payload']

            await self.send_json(
                BaseMessage.build_response(message, result['headers'], out_payload, result['status']).serialize()
            )
        except AttributeError:
            message = BaseMessage(content.get('route'), content.get('uuid'))
            await self.send_json(
                BaseMessage.build_response(
                    message, None, {'Error': 'Route not declared properly in backend'},
                    StatusCodes.INTERNAL_SERVER_ERROR
                ).serialize()
            )
        except KeyError:
            await self.send_json(
                BaseMessage(
                    content.get('uuid', ''), content.get('route', ''), None, None, StatusCodes.BAD_REQUEST
                ).serialize()
            )
            return