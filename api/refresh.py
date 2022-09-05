from http.server import BaseHTTPRequestHandler
import os
import nbformat
from nbclient import NotebookClient
from google.cloud import storage
from urllib.parse import urlparse, parse_qs
import json

storage_client = storage.Client()
bucket = storage_client.bucket(os.environ["NEXT_PUBLIC_STORAGE_BUCKET_NAME"])

def upload(name, data):
  blob = bucket.blob(name)
  blob.upload_from_string(data)
  return

NOTEBOOKS = {
  "Fertilizer",
  "Field",
  "Liquidity",
  "Silo",
  "Creditworthiness"
}

class handler(BaseHTTPRequestHandler):
  def do_GET(self):
    # Select notebook
    url = urlparse(self.path)
    qs  = parse_qs(url.query)
    print(qs)
    name = (qs["name"][0] if "name" in qs else False)
  
    print(f"Name: {name}")
    if not name or name not in NOTEBOOKS:
      self.send_response(404)
      self.end_headers()
      return
    
    # Setup client
    nb = nbformat.read(f"notebooks/{name}.ipynb", as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': 'notebooks/'}})

    # Execute notebook
    try:
      client.execute()
    except Exception as e:
      self.send_response(500)
      self.end_headers()
      self.wfile.write(str(e).encode())
      raise e

    # Get last cell output
    # print(client.code_cells_executed)
    # print(client.nb['cells'][-1])

    # Load last cell in notebook
    last_cell = client.nb['cells'][-1]
    if not last_cell or not "outputs" in last_cell or len(last_cell) is 0:
      self.send_response(500)
      self.end_headers()
      self.wfile.write("no output")
      return
    
    # Extract output JSON
    res = last_cell["outputs"][0]["data"]["application/json"]

    # Upload to storage
    upload(f"{name}.json", json.dumps(res))

    self.send_response(200)
    self.send_header('Content-type','text/plain')
    self.end_headers()
    self.wfile.write("success".encode())  
    return