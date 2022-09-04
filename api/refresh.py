from http.server import BaseHTTPRequestHandler
import os
import nbformat
from nbclient import NotebookClient

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
      return
    except Exception as e:
      self.send_response(500)
      self.end_headers()
      self.wfile.write(str(e).encode())
      raise e