"""Real HTTPX socket client. Start a fresh local Uvicorn server separately."""
import argparse

import httpx


def check(port: int) -> None:
    if not 1 <= port <= 65535:
        raise ValueError("port must be from 1 to 65535")
    with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5, trust_env=False) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/tasks").json()["total"] == 0, "Use a fresh learning server"
        response = client.post("/tasks", json={"title": "HTTPX socket", "minutes": 0})
        assert response.status_code == 201
        task = response.json()
        path = f"/tasks/{task['id']}"
        try:
            assert task == {"id": task["id"], "title": "HTTPX socket", "minutes": 0, "done": False, "note": None}
            assert client.get(path).json() == task
            rejected = client.patch(path, json={"minutes": True})
            assert rejected.status_code == 422
            assert client.get(path).json() == task
            assert client.get("/tasks", params={"limit": 1, "offset": 0}).json()["items"] == [task]
            preflight = client.options("/tasks", headers={
                "Origin": "http://127.0.0.1:5506",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            })
            assert preflight.status_code == 200
            assert preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:5506"
            print("HTTPX LIVE PASS: real socket, 201/200/422, PATCH unchanged, preflight")
        finally:
            deleted = client.delete(path)
            assert deleted.status_code == 204
            assert deleted.content == b""
        assert client.get(path).status_code == 404
        assert client.get("/tasks").json()["total"] == 0
        print("HTTPX LIVE PASS: cleanup 204/404")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8006)
    check(parser.parse_args().port)
