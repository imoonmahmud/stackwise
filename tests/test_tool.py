def test_get_tools_empty(client):
    res = client.get('/tools/')
    assert res.status_code == 200
    assert res.json() == []

def test_get_tools_sorted(client):
    client.post(
        "/tools/",
        json={
            "name": "Zapier",
            "slug": "zapier",
            "short_description": "Automation platform"
        }
    )

    client.post(
        "/tools/",
        json={
            "name": "Make",
            "slug": "make",
            "short_description": "Visual automation platform"
        }
    )

    res = client.get('/tools/')
    assert res.status_code == 200

    tools = res.json()
    assert len(tools) == 2

    assert tools[0]['name'] == 'Make'
    assert tools[1]['name'] == 'Zapier'


def test_get_tool_slug_success(client):
    res = client.post(
        "/tools/",
        json={
            "name": "GitHub",
            "slug": "github",
            "short_description": "Code hosting platform"
        }
    )
    assert res.status_code == 201

    get_res = client.get('tools/github')
    assert get_res.status_code == 200
    assert get_res.json()['name'] == 'GitHub'

def test_update_tool_partial(client):
    create_res = client.post(
        "/tools/",
        json={
            "name": "Postman",
            "slug": "postman",
            "short_description": "Old description"
        }
    )
    tool_id = create_res.json()['id']

    patch_res = client.patch(
        f"tools/{tool_id}",
        json={'short_description': 'New description'}
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data['short_description'] == 'New description'
    assert data['name'] == 'Postman'
    assert data['slug'] == 'postman'


def test_update_tool_null_name(client):
    create_res = client.post(
        "/tools/",
        json={
            "name": "Linear",
            "slug": "linear",
            "short_description": "Issue tracking"
        }
    )
    tool_id = create_res.json()['id']

    patch_res = client.patch(
        f"/tools/{tool_id}",
        json={"name": None}
    )
    assert patch_res.status_code == 200


def test_update_tool_duplicate_slug(client):
    client.post(
        "/tools/",
        json={"name": "Tool A", "slug": "tool-a", "short_description": "Desc A"}
    )
    res2 = client.post(
        "/tools/",
        json={"name": "Tool B", "slug": "tool-b", "short_description": "Desc B"}
    )
    tool_b_id = res2.json()["id"]

    patch_res = client.patch(
        f"/tools/{tool_b_id}",
        json={"slug": "tool-a"}
    )

    assert patch_res.status_code == 409

def test_update_tool_not_found(client):
    patch_res = client.patch(
        "/tools/9999",
        json={"name": "Ghost Tool"}
    )
    assert patch_res.status_code == 404

def test_delete_tool_success(client):
    create_res = client.post(
        "/tools/",
        json={
            "name": "Vercel",
            "slug": "vercel",
            "short_description": "Deployment platform"
        }
    )
    tool_id = create_res.json()["id"]

    delete_res = client.delete(f"/tools/{tool_id}")
    assert delete_res.status_code == 204

    get_res = client.get("/tools/vercel")
    assert get_res.status_code == 404

def test_delete_tool_not_found(client):
    delete_res = client.delete("/tools/9999")
    assert delete_res.status_code == 404