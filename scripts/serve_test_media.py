#!/usr/bin/env python3

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


def main() -> int:
    server = ThreadingHTTPServer(("0.0.0.0", 8765), SimpleHTTPRequestHandler)
    print("serving on 8765")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
