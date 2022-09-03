"""
--------------------- DUMMY STUBS (so python doesn't yell at me) --------------------------
"""
from datetime import datetime

aws = None 
cdn = None 
N = None 

"""
--------------------- SERVERLESS FUNCTION HANDLER (vercel) --------------------------
"""

class HandlersInternal: 

    @staticmethod
    def compute_chart_1(self): 
        return {
            # body of schema for chart 1 
        }

    @staticmethod
    def compute_chart_2(self): 
        return {
            # body of schema for chart 2
        }


class HandlerExternal: 

    def __init__(self): 
        self.aws = None # client for interacting with aws 
        self.cdn = None # client for interacting with cdn 
        self.max_age_minutes = 10 # max age of files before they are stale 

    def handler(self, req): 
        """Generic API handler that will route all incoming requests to the appropriate 
        internal handler function. Each internal handler function produces a JSON object 
        representing a compiled vega schema. Urls to reach this handler will be of the 
        following form 

        /api/chart?name=<chart_name>&timestamp=<timestamp>

        Including the timestamp within the querystring forces browsers to re-request 
        data for the chart on each page load (as the timestamp will be different). 

        "It's okay if the site re-requests raw data from the CDN on each page load IMO. 
        Treating the static files as a sort of cheap API" - SiloChad

        Args: 
            req: Request object (incoming from UI client)
        Returns: 
            resp: Response object (outgoing to UI client)
        """
        # Generic handler for all incoming requests. 
        # Endpoint would be something like 
        name = req.name 
        handler = getattr(HandlersInternal, name)
        if not handler: 
            return {"code": 404}
        filename_regex = rf".*-{name}.json" # this will be changed to more accurately capture valid names prefixed with dates. 
        file, recompute, invalidate_cache = self.get_file(filename_regex)
        if invalidate_cache: 
            cdn.invalidate_cache(file.name)
        if recompute: 
            try: 
                timestamp = datetime.now() 
                new_filename = f"{timestamp}-{name}.json"
                new_schema = handler() 
                aws.s3.write(new_filename, new_schema)
            except BaseException as e: 
                return {"code": 501, "message": e.msg}
            return {"code": 200, "status": "refreshed", "filename": new_filename}
        else: 
            return {"code": 200, "status": "use_cached", "filename": file.name}

    def get_file(self, filename_regex: str): 
        """Returns file handler (if exists) plus flags indicating 
        if recomputation / cache invalidation required. 
        
        Args: 
            filename_regex: Regex that we test against files in aws s3. 
        Returns: 
            file: A file handle (not the underlying data)
            recompute: bool indicating if schema recomputation required.
            invalidate_cache: bool indicating if cache invalidation required.
        """
        file = aws.s3.file_system.match(filename_regex) 
        if file: 
            stale = file.age_minutes > self.max_age_minutes
            recompute, invalidate_cache = stale, stale 
        else: 
            # No file exists so we compute schema but no need to invalidate cache. 
            recompute, invalidate_cache = True, False  
        return file, recompute, invalidate_cache
