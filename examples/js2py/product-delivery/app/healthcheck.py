"""Copy into the learner app. Readiness must inspect DB/schema in the app itself."""
from http.client import HTTPConnection


def main():
    connection = HTTPConnection("127.0.0.1", 8000, timeout=2)
    try:
        connection.request("GET", "/health/ready")
        response = connection.getresponse()
        response.read(8192)
        return 0 if response.status == 200 else 1
    except (OSError, TimeoutError):
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
