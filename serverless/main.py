import logging 
import json 
import datetime 

import functions_framework

from utils_serverless.utils import StorageClient, NotebookRunner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MAX_AGE_SECONDS = 15 * 60 # 15 minutes 

sc = StorageClient()
nbr: NotebookRunner = NotebookRunner()


@functions_framework.http
def bean_analytics_recalculate_chart(request):
    """Top level server router 
    
    Matches incoming requests to one or more jupyter notebook(s). 
    Executes the notebook(s) and writes their outputs to a GCP bucket. 
    
    Notebook output is a JSON object representing a compiled vega spec 
    that can be rendered as is on the client side. 
    """
    # Determine what notebook(s) should be executed 
    name = request.args.get('name')
    name = name and name.lower() 
    force_refresh = request.args.get("force_refresh", "false").lower() == "true"

    # Determine target schema(s)
    match name: 
        case schema_name if nbr.exists(schema_name):
            schema_names = [schema_name]
        case "*":
            schema_names = nbr.names
        case None: 
            return "No name specified", 404 
        case _: 
            return (
                f"Chart with name {name} does not exist. "
                f"Valid options are {nbr.names}."
            ), 404 

    # Optionally re-compute and upload each schema
    statuses = {}
    code = 200 
    for schema_name in schema_names:  
        try:
            cur_dtime = datetime.datetime.now(datetime.timezone.utc)
            blob, exists, age_seconds = sc.get_blob(f"schemas/{schema_name}.json", cur_dtime)
            compute_schema = force_refresh or not exists or age_seconds >= MAX_AGE_SECONDS
            if compute_schema:
                status = "recomputed"
                schema = nbr.execute(schema_name)
                run_time_seconds = nbr.execute._decorated_run_time_seconds, 
                data = {"timestamp": str(cur_dtime), "schema": schema}
                sc.upload(blob, json.dumps(data))
            else: 
                status = "use_cached"
                run_time_seconds = None
            statuses[schema_name] = {"status": status, "run_time_seconds": run_time_seconds}
        except BaseException as e:
            code = 500 
            err_msg = str(e) or "Internal Server Error"
            statuses[schema_name] = {"status": err_msg, "run_time": None}
            logger.error(err_msg)
    return statuses, code
