from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs

class OAuthHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path.startswith('/verifier'):
      self.send_response(200)
      parsed_path = urlparse(self.path)
      qs = parse_qs(parsed_path.query)
      self.server.oauth_verifier = qs['oauth_verifier'][0]
      self.server.socket.close()
    else:
      self.send_response(404)

class OAuthHTTPServer(HTTPServer):
  port = 0
  server = None
  oauth_verifier = None

  def __init__(self):
    self.port = self._pick_unused_port()
    HTTPServer.__init__(self, ('localhost', self.port), OAuthHandler)

  def _pick_unused_port(self):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    addr, port = s.getsockname()
    s.close()
    return port
