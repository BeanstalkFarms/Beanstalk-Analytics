import os
import logging 
from gcp_storage_emulator.server import create_server

logging.basicConfig(level=logging.INFO)

bucket = os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"]
server = create_server(
  "localhost",
  9023,
  in_memory=False,
  default_bucket=bucket
)

server.start()
print(f"Server started: bucket={bucket}")
