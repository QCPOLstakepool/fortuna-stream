import json
from http.server import HTTPServer, BaseHTTPRequestHandler

import typer

class HttpRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/mints":
            self.post_mints()
        else:
            self.not_found()

    def post_mints(self):
        content_length = int(self.headers.get('Content-Length'))
        post_body_json = json.loads(self.rfile.read(content_length))

        with open("mint.json", "w") as debug_file:
            json.dump(post_body_json, debug_file)

        self.send_response(204)
        self.end_headers()

    def not_found(self):
        self.send_response(404)
        self.end_headers()


def main(host: str, port: int):
    server = HTTPServer((host, port), HttpRequestHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()

if __name__ == "__main__":
    typer.run(main)