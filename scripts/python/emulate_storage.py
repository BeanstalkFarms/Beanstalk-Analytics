import os
import logging 
from gcp_storage_emulator.server import create_server


logging.basicConfig(level=logging.INFO)

host = os.environ['STORAGE_EMULATOR_HOST_NAME']
port = os.environ['STORAGE_EMULATOR_PORT']
bucket = os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"]

server = create_server(
  host, port, in_memory=False, default_bucket=bucket
)

server.start()
print(f"Server started: bucket={bucket}")
