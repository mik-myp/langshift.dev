"""Local-only process owner; no reload, access log or shared global sessions."""
import argparse
import logging
import uvicorn
from db import engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8061)
    parser.add_argument("--app", default="app:app", help="Trusted local module:object, e.g. a solution entry")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    try:
        uvicorn.run(args.app, host="127.0.0.1", port=args.port, workers=1,
                    access_log=False, log_level="info")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
