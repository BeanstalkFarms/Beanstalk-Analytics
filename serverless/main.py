import logging 

import functions_framework

from src.utils import StorageClient, NotebookRunner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

storage_client = StorageClient()
nb_runner = NotebookRunner(storage_client=storage_client)


@functions_framework.http
def beanstalk_analytics_handler(request):
    """Top level server router 
    
    Matches incoming requests to one or more jupyter notebook(s). 
    Executes the notebook(s) and writes their outputs to a GCP bucket. 
    
    Notebook output is a JSON object representing a compiled vega spec 
    that can be rendered as is on the client side. 
    """
    # Determine what notebook(s) should be executed 
    match ((name := request.args.get("name", None)) and name.lower()): 
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
        nb_runner.execute_upload_many(nb_names)
        return "Success", 200
    except BaseException as e:
        err_msg = str(e) or "Internal Server Error"
        logging.error(err_msg)
        return err_msg, 500
