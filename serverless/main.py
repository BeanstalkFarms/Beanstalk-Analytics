import logging 
import json 
import datetime 

import functions_framework

from src.utils import StorageClient, CDNClient, NotebookRunner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MAX_AGE_SECONDS = 15 * 60 # 15 minutes 

storage_client = StorageClient()
cdn_client = CDNClient()
nb_runner = NotebookRunner()


@functions_framework.http
def beanstalk_analytics_handler(request):
    """Top level server router 
    
    Matches incoming requests to one or more jupyter notebook(s). 
    Executes the notebook(s) and writes their outputs to a GCP bucket. 
    
    Notebook output is a JSON object representing a compiled vega spec 
    that can be rendered as is on the client side. 
    """
    # Determine what notebook(s) should be executed 
    name = request.args.get('name')
    name = name and name.lower() 
    match name: 
        case nb_name if nb_runner.exists(nb_name):
            nb_names = [nb_name]
        case "*":
            nb_names = nb_runner.names
        case None: 
            return "No name specified", 404 
        case _: 
            return (
                f"Chart with name {name} does not exist. "
                f"Valid options are {nb_runner.names}."
            ), 404 
    try:
        for nb_name in nb_names:  
            # Determine object age in seconds 
            obj_name = f"{nb_name}.json"
            cur_dtime = datetime.datetime.now(datetime.timezone.utc)
            blob, exists, age_seconds = storage_client.get_blob(obj_name, cur_dtime)
            if exists: 
                stale = age_seconds >= MAX_AGE_SECONDS
                recompute, invalidate_cache = stale, stale 
            else: 
                # If the object doesn't exist in the bucket, we  
                # send a cache invalidation request just to be safe 
                recompute, invalidate_cache = True, True   
            if invalidate_cache: 
                cdn_client.invalidate(f"/{obj_name}")
            if recompute:
                logger.info(f"Computing schema {nb_name}.")
                nb_name, schema = nb_runner.execute(nb_name)
                logger.info(f"Uploading schema to storage bucket {nb_name}.")
                data = {"timestamp": str(cur_dtime), "schema": schema}
                storage_client.upload(blob, json.dumps(data))
            return "Success", 200
    except BaseException as e:
        err_msg = str(e) or "Internal Server Error"
        logger.error(err_msg)
        return err_msg, 500
