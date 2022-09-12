import os
import logging
from gcp_storage_emulator.server import create_server


logger = logging.getLogger(__name__)


def get_emulator_server(): 
	host = os.environ['STORAGE_EMULATOR_HOST_NAME']
	port = int(os.environ['STORAGE_EMULATOR_PORT'])
	bucket = os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"]
	server = create_server(
		host, port, in_memory=False, default_bucket=bucket
	)
	logger.info(
		f"Created emulator server at {host}:{port} for bucket={bucket}"
	)
	return server 


if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	server = get_emulator_server()
	server.start()
	