import os
import logging
import subprocess 
import shlex
from contextlib import closing
from urllib.parse import urlparse
from gcp_storage_emulator.server import create_server


logger = logging.getLogger(__name__)


def localhost_port_open(port): 
	try: 
		output = subprocess.check_output(shlex.split(f"lsof -i :{port}")
			).decode("utf-8"
			).lower()
		print(output)
		port_open = not ("localhost" in output or "1.0.0.127" in output) 
	except subprocess.CalledProcessError: 
		port_open = True 
	return port_open


def get_emulator_server(): 
	url = urlparse(os.environ['STORAGE_EMULATOR_HOST'])
	host, port = url.netloc.split(":")
	port = int(port)
	assert host == "localhost" # emulator should only run locally
	bucket = os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"]
	assert localhost_port_open(port), f"localhost:{port} is not open."
	server = create_server(
		host, port, in_memory=False, default_bucket=bucket
	)
	logger.info(f"Created emulator server at {host}:{port} for bucket {bucket}")
	return server 


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	server = get_emulator_server()
	server.start()
	