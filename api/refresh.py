from http.server import BaseHTTPRequestHandler
import os
import nbformat
from nbclient import NotebookClient
from google.cloud import storage

storage_client = storage.Client()
bucket = storage_client.bucket(os.environ["STORAGE_BUCKET_NAME"])

def save(name, data):
  blob = bucket.blob(name)
  blob.upload_from_string(data)
  return

class handler(BaseHTTPRequestHandler):
  def do_GET(self):
    nb = nbformat.read("notebooks/Fertilizer.ipynb", as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': 'notebooks/'}})
    print(os.getcwd())
    try:
      client.execute()
      self.send_response(200)
      self.send_header('Content-type','text/plain')
      self.end_headers()
      self.wfile.write("success".encode())
      save("test.json", "{}")
      return
    except Exception as e:
      self.send_response(500)
      self.end_headers()
      self.wfile.write(str(e).encode())
      raise e