#!/usr/bin/env python3
"""Launch the Orion web settings panel."""

import argparse
from orion.web.app import app, find_free_port


def main():
    parser = argparse.ArgumentParser(description="Orion Settings Panel")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Port (default: auto, starting at 5000)")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")
    args = parser.parse_args()

    port = args.port if args.port else find_free_port(args.host)

    print()
    print("  ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗")
    print(" ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║")
    print(" ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║")
    print(" ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║")
    print(" ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║")
    print("  ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝")
    print()
    print(f"  Settings panel: http://{args.host}:{port}")
    print()

    app.run(host=args.host, port=port, debug=not args.no_debug)


if __name__ == "__main__":
    main()
