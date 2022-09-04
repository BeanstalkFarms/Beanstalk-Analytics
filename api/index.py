from urllib.parse import urlparse, parse_qs
from pathlib import Path 
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    parsed_url = urlparse(self.path)
    qs = parse_qs(parsed_url.query)
    assert len(qs['name']) == 1
    name = qs['name'][0]
    with Path(f"../public/schemas/{name}.json").open("r") as f: 
        json_str = f.read()
    self.wfile.write(json_str.encode(encoding='utf_8'))
    return
