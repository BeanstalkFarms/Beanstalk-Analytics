import os
from gcp_storage_emulator.server import create_server

bucket = os.environ["STORAGE_BUCKET_NAME"]
server = create_server(
  "localhost",
  9023,
  in_memory=False,
  default_bucket=bucket
)

server.start()
print(f"Server started: bucket={bucket}")
