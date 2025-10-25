from starlette.routing import Route
from starlette.responses import JSONResponse
import inspect
from starlette.applications import Starlette

def patch_starlette_app():

    def add_decorator(self, path, methods):
        def decorator(func):
            if not inspect.iscoroutinefunction(func):
                async def async_wrapper(request, *args, **kwargs):
                    result = func(request, *args, **kwargs)
                    if isinstance(result, dict):
                        return JSONResponse(result)
                    return result
                handler = async_wrapper
            else:
                async def async_handler(request, *args, **kwargs):
                    result = await func(request, *args, **kwargs)
                    if isinstance(result, dict):
                        return JSONResponse(result)
                    return result
                handler = async_handler

            self.routes.append(Route(path, handler, methods=methods))
            return func
        return decorator

    http_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT"]

    for method in http_methods:
        method_lower = method.lower()
        setattr(Starlette, method_lower, lambda self, path, m=method: add_decorator(self, path, [m]))