#!/usr/bin/env python3
"""
A simple webserver that records incoming requests to files.
Useful for troubleshooting proxies that modify headers in
unexpected ways.

When a request is received, three files are written:
- headers.data, which contains the headers in raw format
- body.data, which includes the request body
- request.curl, which contains a curl command to replicate
  the request with the same headers and body.

Once the request is processed, the server exits, resulting
in an empty response back to the originating client.
"""
# Credit to the simple-python-webserver github project for inspiration.

import argparse
from io import BytesIO
import socket

class Server:
    def __init__(self, port=80):
        self.host = '0.0.0.0'
        self.port = port
        self._socket = None
        self.max_queued_connections = 50

    def open(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.bind((self.host, self.port))
        except:
            self._socket.close()
            raise
        else: 
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def serve(self):
        self.open()
        while True:
            self.handle_request()
            break

    def handle_request(self):
        self._socket.listen(self.max_queued_connections)
        connection, _ = self._socket.accept()
        data = connection.recv(65536)
        in_headers = True
        with BytesIO(data) as fp:
            headers = []
            while True:
                line = fp.readline()
                headers.append(line)
                if line in (b'\r\n', b'\n', b''):
                    break
            body = fp.read()
        hstring = b''.join(headers).decode('iso-8859-1')

        # Write raw headers and body to files
        with open('headers.data', 'w') as f:
            f.write(hstring)
        with open('body.data', 'wb') as f:
            f.write(body)

        # Write a curl command line to replay the request.
        first_line = headers[0].decode('utf-8').split(' ')
        method = first_line[0]
        url = first_line[1]
        headers2 = ["-H '{}'".format(x.strip().decode('utf-8')) for x in headers[1:]]
        body2 = ''
        if body:
            # TODO: Decode this correctly, unsure what is correct.
            body2 = "--data '{}'".format(body.decode('utf-8'))
        s = '''curl -v -X {} {} {} {}'''.format(method, url, ' '.join(headers2), body2)
        with open('request.curl', 'w') as f:
            f.write(s)

    def stop(self):
        self._socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start a proxying webserver, records requests to a file')
    parser.add_argument('port', type=int, help='port to listen on')
    args = parser.parse_args()
    server = Server(args.port)
    try:
        server.serve()
    finally:
        server.stop()

