import http.server
import socketserver
import threading

PORT = 8080  # health check port

def start_server():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return  # disable logs

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

thread = threading.Thread(target=start_server, daemon=True)
thread.start()
