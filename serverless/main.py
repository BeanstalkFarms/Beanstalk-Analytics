from pathlib import Path 

import functions_framework

from handlers import handler_charts_refresh


ROUTER = {
    Path("/charts/refresh"): handler_charts_refresh
}
routes = [str(r) for r in ROUTER.keys()]

@functions_framework.http
def bean_analytics_http_handler(request):
    """Matches incoming url path to appropriate handler. """
    handler = ROUTER.get(Path(request.path))
    if not handler: 
        return f"Invalid url path {request.path}\nValid routes are {routes}.", 404 
    return handler(request)
