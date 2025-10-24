#!/usr/bin/env python3
"""
MatsushibaDB CLI
"""

import argparse
import sys
from .client import MatsushibaDBClient

def main():
    parser = argparse.ArgumentParser(description="MatsushibaDB CLI")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--db", help="Database file")
    parser.add_argument("--sql", help="SQL query to execute")
    
    args = parser.parse_args()
    
    if args.sql:
        client = MatsushibaDBClient(host=args.host, port=args.port, api_key=args.api_key)
        try:
            result = client.execute(args.sql)
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("MatsushibaDB Python client")
        print("Use --sql 'query' to execute SQL")
        print("Use the full MatsushibaDB binary for server functionality")

if __name__ == "__main__":
    main()
