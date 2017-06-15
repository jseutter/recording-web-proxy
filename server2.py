#!/usr/bin/env python3
"""
A simple process that proxies HTTP requests to a backend
server, inserting headers along the way.
"""
# Credit to the simple-python-webserver github project for inspiration.

import argparse
from http.client import parse_headers
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import requests
import socket

class MyHTTPHandler(BaseHTTPRequestHandler):
    backend_port = 0
    def do_GET(self):
        return self._internal('GET')

    def do_POST(self):
        return self._internal('POST')

    def do_PUT(self):
        return self._internal('PUT')

    def do_DELETE(self):
        return self._internal('DELETE')

    def _internal(self, method):
        url = 'http://localhost:{}{}'.format(self.backend_port, self.path)
        # self.headers.as_string()
        # data is not yet handled.  Need content-length?)
        headers = dict(self.headers)
        with open('headers.data', 'rb') as fp:
            # Throw away first line which is not a header
            request_line = fp.readline()
            headers.update(dict(parse_headers(fp)))

        content_len = int(self.headers.get('content-length', 0))
        body = self.rfile.read(content_len)
        self.log_message('REQUEST_LINE: {}'.format(request_line.decode('ascii').strip()))
        self.log_message('HEADERS:\n{}'.format('\n'.join(['{}: {}'.format(k, v) for k, v in headers.items()])))
        self.log_message('BODY:\n{}'.format(body.decode('ascii')))
        resp = requests.request(method, url, headers=headers, data=body)

        self.send_response(resp.status_code)
        for key, value in resp.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(resp.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fake out repose')
    parser.add_argument('lport', type=int, help='port to listen on')
    parser.add_argument('bport', type=int, help='backend port to forward requests to')
    args = parser.parse_args()

    MyHTTPHandler.backend_port = args.bport

    server = HTTPServer(('localhost', args.lport), MyHTTPHandler)
    server.backend_port = args.bport

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

