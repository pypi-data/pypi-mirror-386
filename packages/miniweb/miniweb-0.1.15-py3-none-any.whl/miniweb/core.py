import typing
from cached_property import cached_property
from wsgiref.util import FileWrapper

from miniweb.exceptions import PayloadTooLarge
from miniweb.exceptions import LengthRequired

from .request import HttpRequest
from .response import HttpResponse
from .response import HttpChunkResponseData
from .router import Router

MiniwebRequestHandlerType = typing.Callable[[HttpRequest, HttpResponse], None] # miniweb defined handler type
WsgiHandlerResultType = typing.Union[typing.List[bytes], FileWrapper, HttpChunkResponseData] # wsgi defined handler result type
WsgiEnvType = typing.Any
WsgiStartResponseType = typing.Any

class Middleware(object):
    def __init__(self, get_response:MiniwebRequestHandlerType) -> None:
        self.get_response = get_response
    
    def __call__(self, http_request:HttpRequest, http_response:HttpResponse) -> None:
        return self.get_response(http_request, http_response)

class Application(object):

    DEFAULT_ALLOWED_METHODS = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT"]

    def __init__(self) -> None:
        self.middlewares = []
        self.router = Router()
        self.global_allowed_methods = [] + self.DEFAULT_ALLOWED_METHODS

    def reset_global_allowed_methods(self):
        self.global_allowed_methods = [] + self.DEFAULT_ALLOWED_METHODS

    def set_middlewares(self, middlewares:typing.List[Middleware]) -> None:
        self.middlewares = [] + middlewares

    @cached_property
    def dispatch_chain(self) -> MiniwebRequestHandlerType:
        dispatch = self.dispatch
        for middleware_class in reversed(self.middlewares):
            dispatch = middleware_class(dispatch)
        return dispatch

    def dispatch(self, http_request:HttpRequest, http_response:HttpResponse) -> None:
        if self.global_allowed_methods and (not http_request.method in self.global_allowed_methods):
            http_response.not_allowed(method=http_request.method, permitted_methods=self.global_allowed_methods)
        else:
            handler = self.router.dispatch(http_request.path)
            if not handler:
                http_response.not_found()
            else:
                permitted_methods = getattr(handler, "allowed_methods", None)
                if permitted_methods and (not http_request.method in permitted_methods):
                    http_response.not_allowed(method=http_request.method, permitted_methods=permitted_methods)
                try:
                    handler(http_request, http_response)
                except LengthRequired as error:
                    http_response.length_required()
                except PayloadTooLarge as error:
                    http_response.payload_too_large(error.args[0], error.args[1])

    def __call__(self, env:WsgiEnvType, start_response:WsgiStartResponseType) -> WsgiHandlerResultType:
        http_request = HttpRequest(env, application=self)
        http_response = HttpResponse(start_response, request=http_request, application=self)
        self.dispatch_chain(http_request, http_response)
        return self.do_final_response(http_request, http_response)

    def do_final_response(self, http_request:HttpRequest, http_response:HttpResponse) -> WsgiHandlerResultType:
        http_response.start_response(http_response.final_status_code, http_response.final_headers)
        final_content = http_response.final_content
        if not final_content:
            return []
        FileWrapperClass = http_request.env.get("wsgi.file_wrapper", None)
        if FileWrapperClass and isinstance(final_content, FileWrapperClass):
            return final_content
        if isinstance(final_content, FileWrapper):
            return final_content
        if isinstance(final_content, HttpChunkResponseData):
            return final_content
        return [final_content]
