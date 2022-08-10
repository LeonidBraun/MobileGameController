# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import socket

IPAddr = socket.gethostbyname(socket.gethostname())

# hostName = "localhost"
hostName = "0.0.0.0"
serverPort = 4443
print(IPAddr, serverPort)


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "html")
            self.end_headers()
            f = open("index.html", "r")
            for line in f:
                if line.find("const IP = 'XXX.XXX.XXX.XX';") >= 0:
                    self.wfile.write(bytes(f"const IP = '{IPAddr}';", "utf-8"))
                else:
                    self.wfile.write(bytes(line, "utf-8"))
            f.close()
        elif self.path[:2] == "/X":
            self.send_response(200)
            print(self.path[2:], str(self.path[2:]))
        elif self.path == "/assets/css/bootstrap.min.css":
            self.send_response(200)
            self.send_header("Content-type", "css")
            self.end_headers()
            f = open("bootstrap.min.css", "r")
            for line in f:
                self.wfile.write(bytes(line, "utf-8"))
            f.close()
        elif self.path == "/ball":
            self.send_response(200)
            self.send_header("Content-type", "html")
            self.end_headers()
            f = open("ball.html", "r")
            for line in f:
                self.wfile.write(bytes(line, "utf-8"))
            f.close()
        # elif self.path == "/favicon.ico":
        #     self.send_response(200)
        #     self.send_header("Content-type", "html")
        #     self.end_headers()
        #     f = open("ball.html","r")
        #     for line in f:
        #         self.wfile.write(bytes(line, "utf-8"))
        #     f.close()
        else:
            self.send_response(200)
            # self.send_header("Content-type", "html")
            self.end_headers()


if __name__ == "__main__":

    # & "C:\Program Files\Git\usr\bin\openssl.exe" req -new -x509 -keyout key.pem -out server.pem -days 365 -nodes
    # & "C:\Program Files\Git\usr\bin\openssl.exe" req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="./cert.pem", keyfile="./cert.pem")

    webServer = HTTPServer((hostName, serverPort), MyServer)
    webServer.socket = ssl_context.wrap_socket(
        webServer.socket,
    )

    print("Server starting https://%s:%s" % (hostName, serverPort))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
