import json 
import datetime 
import logging 
from typing import Tuple  

from utils_serverless.utils import StorageClient, NotebookRunner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MAX_AGE_SECONDS = 15 * 60 # 15 minutes 

sc = StorageClient()
nbr = NotebookRunner()


def handler_charts_refresh(request) -> Tuple[any, int]: 
    """Recalculates one or more chart objects 
    
    Matches incoming requests to one or more jupyter notebook(s). 
    Executes the notebook(s) and writes their outputs to a GCP bucket. 
    Notebooks are only executed if they are older than MAX_AGE_SECONDS. 
    
    Notebook output is a JSON object representing a compiled vega spec 
    that can be rendered as is on the client side. 
    """
    data = request.args.get('data')
    data = data and data.lower() 
    force_refresh = request.args.get("force_refresh", "false").lower() == "true"

    # Determine target schema(s)
    match data: 
        case sn if nbr.exists(sn):
            schema_names = [sn]
        case "*":
            schema_names = nbr.names
        case schema_name_csv if (
            "," in schema_name_csv and all(
                nbr.exists(sn) for sn in schema_name_csv.split(',')
            )
        ):
            schema_names = schema_name_csv.split(',')
        case None: 
            return "No name(s) specified", 404 
        case _: 
            return (
                "Invalid value for querystring parameter 'data'. "
                "The value must be one of the following.\n"
                "1. A single chart name.\n"
                "2. A csv string of multiple chart names\n"
                "3. The symbol '*'\n"
                f"Valid individual names are {nbr.names}."
            ), 404 

    # Optionally re-compute and upload each schema
    statuses = {}
    code = 200 
    for schema_name in set(schema_names):  # ensure no duplicate computation 
        try:
            cur_dtime = datetime.datetime.now(datetime.timezone.utc)
            blob, exists, age_seconds = sc.get_blob(f"schemas/{schema_name}.json", cur_dtime)
            compute_schema = force_refresh or not exists or age_seconds >= MAX_AGE_SECONDS
            if compute_schema:
                status = "recomputed"
                ntbk_output = nbr.execute(schema_name)
                data = {
                    "timestamp": cur_dtime.isoformat(), 
                    "run_time_seconds": nbr.execute._decorated_run_time_seconds,
                    "spec": ntbk_output['spec'],
                    "width_paths": ntbk_output['width_paths'],
                    "css": ntbk_output['css'],
                }
                sc.upload(blob, json.dumps(data))
            else: 
                status = "use_cached"
            statuses[schema_name] = {"status": status}
        except BaseException as e:
            code = 500 
            err_msg = str(e) or "Internal Server Error"
            statuses[schema_name] = {"status": "failure", "error": str(err_msg)}
            logger.error(err_msg)
    return statuses, code
