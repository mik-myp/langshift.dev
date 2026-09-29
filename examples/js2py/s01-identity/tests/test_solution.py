def test_session_count_is_current_user_and_current_generation_only(api, accounts):
    first = api.token("Alice", accounts.password)
    second = api.token("Alice", accounts.password)
    api.token("Bob", accounts.password)
    assert api.request("GET", "/users/me/session-count", token=first).body == {"count": 2}
    assert api.request("POST", "/auth/logout", token=second).status == 204
    assert api.request("GET", "/users/me/session-count", token=first).body == {"count": 1}
    assert api.request("POST", "/auth/logout-all", token=first).status == 204
    fresh = api.token("Alice", accounts.password)
    assert api.request("GET", "/users/me/session-count", token=fresh).body == {"count": 1}
    assert api.request("GET", "/users/me/session-count").status == 401
