import pytest

def test_create_comparison_success(client):
    t1 = client.post("/tools/", json={"name": "Make", "slug": "make"}).json()
    t2 = client.post("/tools/", json={"name": "Zapier", "slug": "zapier"}).json()
    t3 = client.post("/tools/", json={"name": "n8n", "slug": "n8n"}).json()

    res = client.post(
        "/comparisons/",
        json={
            "tool_ids": [t1["id"], t3["id"], t2["id"]],
            "summary": "Workflow automation comparison"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["slug"] == "make-vs-n8n-vs-zapier"
    assert [t["id"] for t in data["tools"]] == [t1["id"], t3["id"], t2["id"]]


def test_create_comparison_duplicate_set_409(client):
    t1 = client.post("/tools/", json={"name": "Tool A", "slug": "tool-a"}).json()
    t2 = client.post("/tools/", json={"name": "Tool B", "slug": "tool-b"}).json()

    res1 = client.post("/comparisons/", json={"tool_ids": [t1["id"], t2["id"]]})
    assert res1.status_code == 201

    res2 = client.post("/comparisons/", json={"tool_ids": [t2["id"], t1["id"]]})
    assert res2.status_code == 409


@pytest.mark.parametrize("tool_ids", [[1], [1, 2, 3, 4, 5], [1, 1]])
def test_create_comparison_invalid_tool_ids(client, tool_ids):
    response = client.post("/comparisons/", json={"tool_ids": tool_ids})
    assert response.status_code == 422


def test_create_comparison_unknown_tool_404(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    
    res = client.post("/comparisons/", json={"tool_ids": [t1["id"], 9999]})
    assert res.status_code == 404
    
    list_res = client.get("/comparisons/")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0


def test_build_comparison_table_and_starting_price(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1", "pricing_model": "Subscription"}).json()
    client.post(f"/tools/{t1['id']}/pricing-plans", json={"name": "Free", "price": "0.00", "is_free": True})
    client.post(f"/tools/{t1['id']}/pricing-plans", json={"name": "Pro", "price": "19.99", "is_free": False})

    t2 = client.post("/tools/", json={"name": "Tool 2", "slug": "t2", "pricing_model": "Freemium"}).json()
    client.post(f"/tools/{t2['id']}/pricing-plans", json={"name": "Only Free", "price": "0.00", "is_free": True})

    res = client.post("/comparisons/", json={"tool_ids": [t1["id"], t2["id"]]})
    assert res.status_code == 201
    data = res.json()

    rows_map = {row["label"]: row["values"] for row in data["rows"]}
    assert rows_map["Pricing model"] == ["Subscription", "Freemium"]
    assert rows_map["Starting price"] == ["$19.99", None]


def test_patch_tool_plan_updates_comparison(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    plan = client.post(f"/tools/{t1['id']}/pricing-plans", json={"name": "Pro", "price": "10.00", "is_free": False}).json()
    t2 = client.post("/tools/", json={"name": "Tool 2", "slug": "t2"}).json()

    comp = client.post("/comparisons/", json={"tool_ids": [t1["id"], t2["id"]]}).json()
    
    client.patch(f"/pricing-plans/{plan['id']}", json={"price": "25.00"})

    get_res = client.get(f"/comparisons/{comp['slug']}")
    assert get_res.status_code == 200
    rows_map = {row["label"]: row["values"] for row in get_res.json()["rows"]}
    assert rows_map["Starting price"][0] == "$25.00"


def test_delete_comparison_and_tool_restrict(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    t2 = client.post("/tools/", json={"name": "Tool 2", "slug": "t2"}).json()

    comp = client.post("/comparisons/", json={"tool_ids": [t1["id"], t2["id"]]}).json()

    del_tool = client.delete(f"/tools/{t1['id']}")
    assert del_tool.status_code == 409