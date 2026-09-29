def test_allowed_preflight(client):
    response = client.options("/tasks", headers={
        "Origin": "http://127.0.0.1:5506",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5506"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_disallowed_preflight(client):
    response = client.options("/tasks", headers={
        "Origin": "http://127.0.0.1:5507",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_does_not_protect_the_api(client):
    response = client.get("/tasks", headers={"Origin": "http://127.0.0.1:5507"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    assert client.get("/tasks").status_code == 200
