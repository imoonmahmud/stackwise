def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_create_tool_success(client):
    response = client.post(
        "/tools/",
        json={
            "name": "Docker",
            "slug": "docker",
            "short_description": "Containerization platform"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["slug"] == "docker"
    assert data["name"] == "Docker"


def test_create_tool_duplicate_slug(client):
    payload = {
        "name": "Docker",
        "slug": "docker",
        "short_description": "Containerization platform"
    }

    res1 = client.post("/tools/", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/tools/", json=payload)
    assert res2.status_code == 409


def test_create_tool_missing_slug(client):
    response = client.post(
        "/tools/",
        json={
            "name": "Docker",
            "short_description": "Missing slug field"
        }
    )
    assert response.status_code == 422


def test_get_tool_not_found(client):
    response = client.get("/tools/nope")
    assert response.status_code == 404


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


def test_search_by_name(client):
    client.post(
        "/tools/",
        json={"name": "PostgreSQL", "slug": "postgresql", "short_description": "Relational DB"}
    )
    client.post(
        "/tools/",
        json={"name": "Redis", "slug": "redis", "short_description": "In-memory datastore"}
    )

    res = client.get("/tools/?search=Postgre")
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]["name"] == "PostgreSQL"

def test_search_case_insensitive(client):
    client.post(
        "/tools/",
        json={"name": "Docker", "slug": "docker", "short_description": "Container platform"}
    )

    res = client.get("/tools/?search=docKER")
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]['name'] == 'Docker'

def test_search_no_match(client):
    client.post(
        "/tools/",
        json={"name": "FastAPI", "slug": "fastapi", "short_description": "Python web framework"}
    )

    response = client.get("/tools/?search=nonexistentterm")
    assert response.status_code == 200
    assert response.json() == []

def test_search_sql_injection_safe(client):
    client.post(
        "/tools/",
        json={"name": "SafeTool", "slug": "safetool", "short_description": "Normal tool"}
    )

    injection_payload = "' OR '1'='1'; DROP TABLE tools; --"
    response = client.get(f"/tools/?search={injection_payload}")
    assert response.status_code == 200

    check_response = client.get("/tools/")
    assert check_response.status_code == 200
    assert len(check_response.json()) == 1
    assert check_response.json()[0]["name"] == "SafeTool"


def test_search_percent_is_literal(client):
    client.post(
        "/tools/",
        json={"name": "n8n", "slug": "n8n", "short_description": "Workflow automation"}
    )
    client.post(
        "/tools/",
        json={"name": "Make", "slug": "make", "short_description": "Visual automation"}
    )

    res = client.get('/tools/?search=%25')

    assert res.status_code == 200
    assert res.json() == []