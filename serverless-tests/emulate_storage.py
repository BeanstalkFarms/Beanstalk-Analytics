import os
import logging
from urllib.parse import urlparse
from gcp_storage_emulator.server import create_server


logger = logging.getLogger(__name__)


def get_emulator_server(): 
	url = urlparse(os.envion['STORAGE_EMULATOR_HOST'])
	host = url.netloc 
	port = url.port 
	assert host == "localhost" # emulator should only run locally
	bucket = os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"]
	server = create_server(
		host, port, in_memory=False, default_bucket=bucket
	)
	logger.info(f"Created emulator server at {url} for bucket {bucket}")
	return server 


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	server = get_emulator_server()
	server.start()
	