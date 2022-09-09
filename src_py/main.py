import logging 
import json 
import datetime 

import functions_framework

from utils_serverless import StorageClient, NotebookRunner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MAX_AGE_SECONDS = 15 * 60 # 15 minutes 

storage_client = StorageClient()
nb_runner = NotebookRunner()


@functions_framework.http
def recalculate_chart(request):
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
        case schema_name if nb_runner.exists(schema_name):
            schema_names = [schema_name]
        case "*":
            schema_names = nb_runner.names
        case None: 
            return "No name specified", 404 
        case _: 
            return (
                f"Chart with name {name} does not exist. "
                f"Valid options are {nb_runner.names}."
            ), 404 

    # Optionally re-compute and upload each schema
    try:
        for schema_name in schema_names:  
            cur_dtime = datetime.datetime.now(datetime.timezone.utc)
            blob, exists, age_seconds = storage_client.get_blob(f"schemas/{schema_name}.json", cur_dtime)
            compute_schema = force_refresh or not exists or age_seconds >= MAX_AGE_SECONDS
            if compute_schema:
                logger.info(f"Computing schema {nb_name}.")
                nb_name, schema = nb_runner.execute(nb_name)
                logger.info(f"Uploading schema to storage bucket {nb_name}.")
                data = {"timestamp": str(cur_dtime), "schema": schema}
                storage_client.upload(blob, json.dumps(data))
        return ("recomputed" if compute_schema else "use_cached"), 200
    except BaseException as e:
        err_msg = str(e) or "Internal Server Error"
        logger.error(err_msg)
        return err_msg, 500
