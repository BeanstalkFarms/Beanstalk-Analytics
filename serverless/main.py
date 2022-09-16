from pathlib import Path 

import functions_framework

from handlers import handler_charts_refresh


ROUTER = {
    Path("/schemas/refresh"): handler_charts_refresh
}
routes = [str(r) for r in ROUTER.keys()]


def handle_cors_preflight(): 
    # Allows GET requests from any origin with the Content-Type
    # header and caches preflight response for an 3600s
    # https://cloud.google.com/functions/docs/samples/functions-http-cors#functions_http_cors-python
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    }
    # changed from 204 to 200 for unit tests 
    return ('', 200, headers)


@functions_framework.http
def bean_analytics_http_handler(request):
    """Matches incoming url path to appropriate handler. """
    
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        return handle_cors_preflight() 
        
    # Handle route 
    handler = ROUTER.get(Path(request.path))
    if not handler: 
        return f"Invalid url path {request.path}\nValid routes are {routes}.", 404 

    body, status = handler(request)
    headers = {'Access-Control-Allow-Origin': '*'} # CORS 
    return body, status, headers 
