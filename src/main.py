#!/usr/bin/env python3
"""
MALDB - Main entry point
"""

import sys
import argparse
from .repl.shell import start_repl
from .api.server import start_api_server

def main():
    parser = argparse.ArgumentParser(
        description='MALDB - A minimal RDBMS with column-level encryption'
    )
    
    parser.add_argument(
        '--repl',
        action='store_true',
        help='Start interactive SQL REPL (default)'
    )
    
    parser.add_argument(
        '--api',
        action='store_true',
        help='Start REST API server'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for API server (default: 8000)'
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='Database file to open (creates if not exists)'
    )
    
    args = parser.parse_args()
    
    if args.api:
        print(f"Starting MALDB API server on port {args.port}")
        start_api_server(port=args.port, db_file=args.file)
    else:
        print("=" * 50)
        print("MALDB - Minimal RDBMS")
        print("Type SQL commands or 'exit;' to quit")
        print("=" * 50)
        start_repl(db_file=args.file)

if __name__ == "__main__":
    main()