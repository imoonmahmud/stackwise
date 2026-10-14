def test_create_solution_success(client):
    t1 = client.post("/tools/", json={"name": "HubSpot", "slug": "hubspot"}).json()
    t2 = client.post("/tools/", json={"name": "Make", "slug": "make"}).json()
    
    res = client.post(
        "/solutions/",
        json={
            "title": "Automate lead follow-up",
            "slug": "automate-lead-follow-up",
            "short_description": "Lead management workflow",
            "steps": [
                {"tool_id": t1["id"], "role": "CRM", "note": "Capture the lead"},
                {"tool_id": t2["id"], "role": "Automation", "note": "Trigger on contact"},
                {"tool_id": t2["id"], "role": "AI", "note": "Write email via Make again"}
            ]
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert len(data["steps"]) == 3
    assert data["steps"][0]["step_order"] == 1
    assert data["steps"][1]["step_order"] == 2
    assert data["steps"][2]["step_order"] == 3
    assert data["steps"][1]["tool"]["id"] == t2["id"]
    assert data["steps"][2]["tool"]["id"] == t2["id"]


def test_create_solution_unknown_tool(client):
    res = client.post(
        "/solutions/",
        json={
            "title": "Bad Solution",
            "slug": "bad-solution",
            "steps": [{"tool_id": 9999, "role": "CRM"}]
        }
    )
    assert res.status_code == 404
    
    list_res = client.get("/solutions/")
    assert list_res.status_code == 200
    assert list_res.json() == []


def test_create_solution_empty_steps(client):
    res = client.post(
        "/solutions/",
        json={
            "title": "Empty Steps",
            "slug": "empty-steps",
            "steps": []
        }
    )
    assert res.status_code == 422


def test_create_solution_duplicate_slug(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    payload = {
        "title": "Solution A",
        "slug": "duplicate-slug",
        "steps": [{"tool_id": t1["id"], "role": "CRM"}]
    }
    res1 = client.post("/solutions/", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/solutions/", json=payload)
    assert res2.status_code == 409


def test_get_solutions_list_no_steps(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    client.post(
        "/solutions/",
        json={
            "title": "My Solution",
            "slug": "my-solution",
            "short_description": "Short desc",
            "steps": [{"tool_id": t1["id"], "role": "CRM"}]
        }
    )
    res = client.get("/solutions/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert "steps" not in data[0]
    assert data[0]["title"] == "My Solution"
    assert data[0]["slug"] == "my-solution"


def test_patch_solution_title_only(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    create_res = client.post(
        "/solutions/",
        json={
            "title": "Original Title",
            "slug": "orig-slug",
            "steps": [{"tool_id": t1["id"], "role": "CRM", "note": "Keep note"}]
        }
    ).json()
    sol_id = create_res["id"]

    patch_res = client.patch(
        f"/solutions/{sol_id}",
        json={"title": "Updated Title"}
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "Updated Title"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["note"] == "Keep note"


def test_patch_solution_new_steps(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    t2 = client.post("/tools/", json={"name": "Tool 2", "slug": "t2"}).json()
    create_res = client.post(
        "/solutions/",
        json={
            "title": "Solution",
            "slug": "sol-slug",
            "steps": [{"tool_id": t1["id"], "role": "CRM"}]
        }
    ).json()
    sol_id = create_res["id"]

    patch_res = client.patch(
        f"/solutions/{sol_id}",
        json={"steps": [{"tool_id": t2["id"], "role": "New Role", "note": "New note"}]}
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert len(data["steps"]) == 1
    assert data["steps"][0]["role"] == "New Role"
    assert data["steps"][0]["step_order"] == 1
    assert data["steps"][0]["tool"]["id"] == t2["id"]


def test_patch_solution_steps_null(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    create_res = client.post(
        "/solutions/",
        json={
            "title": "Solution",
            "slug": "sol-slug",
            "steps": [{"tool_id": t1["id"], "role": "CRM"}]
        }
    ).json()
    sol_id = create_res["id"]

    patch_res = client.patch(
        f"/solutions/{sol_id}",
        json={"steps": None}
    )
    assert patch_res.status_code == 422


def test_delete_solution_keeps_tools(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    create_res = client.post(
        "/solutions/",
        json={
            "title": "Solution",
            "slug": "sol-slug",
            "steps": [{"tool_id": t1["id"], "role": "CRM"}]
        }
    ).json()
    sol_id = create_res["id"]

    del_res = client.delete(f"/solutions/{sol_id}")
    assert del_res.status_code == 204

    tool_get = client.get("/tools/t1")
    assert tool_get.status_code == 200


def test_delete_tool_used_in_solution_restrict(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    t2 = client.post("/tools/", json={"name": "Tool 2", "slug": "t2"}).json()
    
    sol_res = client.post(
        "/solutions/",
        json={
            "title": "Solution",
            "slug": "sol-slug",
            "steps": [{"tool_id": t1["id"], "role": "CRM"}]
        }
    ).json()

    del_used = client.delete(f"/tools/{t1['id']}")
    assert del_used.status_code == 409

    get_sol = client.get("/solutions/sol-slug")
    assert get_sol.status_code == 200
    assert len(get_sol.json()["steps"]) == 1

    del_unused = client.delete(f"/tools/{t2['id']}")
    assert del_unused.status_code == 204