from uuid import uuid4


def test_project_summary_is_scoped_and_denies_outsiders(api, accounts):
    owner, outsider = api.token("Alice", accounts.password), api.token("Bob", accounts.password)
    project = api.request("POST", "/projects", {"name":"Summary"}, owner).body["id"]
    base = f"/projects/{project}"
    for title, minutes, status in [("Zero",0,"todo"),("Work",15,"doing"),("Done",40,"done")]:
        assert api.request("POST",base+"/tasks",{"title":title,"minutes":minutes,"status":status},owner,str(uuid4())).status == 201
    assert api.request("GET",base+"/summary",token=owner).body == {"count":2,"minutes":15}
    assert api.request("GET",base+"/summary",token=outsider).status == 404
