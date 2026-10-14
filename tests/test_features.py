def test_create_feature_and_list(client):
    res = client.post("/features/", json={"name": "Webhooks", "slug": "webhooks"})
    assert res.status_code == 201
    
    dup_res = client.post("/features/", json={"name": "Webhooks", "slug": "webhooks-other"})
    assert dup_res.status_code == 409

    client.post("/features/", json={"name": "AI agents", "slug": "ai-agents"})
    list_res = client.get("/features/")
    assert list_res.status_code == 200
    data = list_res.json()
    assert len(data) == 2
    assert data[0]["name"] == "AI agents"
    assert data[1]["name"] == "Webhooks"


def test_create_tool_with_unknown_feature_id(client):
    res = client.post(
        "/tools/",
        json={"name": "Bad Tool", "slug": "bad-tool", "feature_ids": [999]}
    )
    assert res.status_code == 404
    
    list_res = client.get("/tools/")
    assert list_res.json()["items"] == []


def test_update_tool_features(client):
    f1 = client.post("/features/", json={"name": "Feature 1", "slug": "f1"}).json()
    f2 = client.post("/features/", json={"name": "Feature 2", "slug": "f2"}).json()

    tool = client.post(
        "/tools/",
        json={"name": "Tool A", "slug": "tool-a", "feature_ids": [f1["id"]]}
    ).json()

    update_res = client.patch(
        f"/tools/{tool['id']}",
        json={"feature_ids": [f2["id"]]}
    )
    assert update_res.status_code == 200
    assert len(update_res.json()["features"]) == 1
    assert update_res.json()["features"][0]["slug"] == "f2"

    update_keep = client.patch(
        f"/tools/{tool['id']}",
        json={"name": "Tool A Updated"}
    )
    assert update_keep.status_code == 200
    assert len(update_keep.json()["features"]) == 1
    assert update_keep.json()["features"][0]["slug"] == "f2"

    update_clear = client.patch(
        f"/tools/{tool['id']}",
        json={"feature_ids": []}
    )
    assert update_clear.status_code == 200
    assert update_clear.json()["features"] == []


def test_delete_tool_keeps_feature(client):
    feat = client.post("/features/", json={"name": "Persistent Feature", "slug": "persist"}).json()
    tool = client.post(
        "/tools/",
        json={"name": "Temp Tool", "slug": "temp-tool", "feature_ids": [feat["id"]]}
    ).json()

    del_res = client.delete(f"/tools/{tool['id']}")
    assert del_res.status_code == 204

    feat_res = client.get("/features/")
    assert feat_res.status_code == 200
    assert any(f["slug"] == "persist" for f in feat_res.json())


def test_filter_with_one_and_two_features(client):
    f1 = client.post("/features/", json={"name": "Feat A", "slug": "feat-a"}).json()
    f2 = client.post("/features/", json={"name": "Feat B", "slug": "feat-b"}).json()

    client.post(
        "/tools/",
        json={"name": "Tool One", "slug": "tool-one", "feature_ids": [f1["id"]]}
    )
    client.post(
        "/tools/",
        json={"name": "Tool Both", "slug": "tool-both", "feature_ids": [f1["id"], f2["id"]]}
    )

    res_one = client.get("/tools/?feature=feat-a")
    assert res_one.status_code == 200
    assert len(res_one.json()["items"]) == 2

    res_two = client.get("/tools/?feature=feat-a&feature=feat-b")
    assert res_two.status_code == 200
    data = res_two.json()["items"]
    assert len(data) == 1
    assert data[0]["slug"] == "tool-both"


def test_filter_with_unknown_feature(client):
    res = client.get("/tools/?feature=unknown-feature")
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_tool_with_multiple_categories_and_features_returned_once(client):
    c1 = client.post("/categories/", json={"name": "Cat 1", "slug": "cat-1"}).json()
    c2 = client.post("/categories/", json={"name": "Cat 2", "slug": "cat-2"}).json()
    f1 = client.post("/features/", json={"name": "Feat 1", "slug": "feat-1"}).json()
    f2 = client.post("/features/", json={"name": "Feat 2", "slug": "feat-2"}).json()

    client.post(
        "/tools/",
        json={
            "name": "Complex Tool",
            "slug": "complex-tool",
            "category_ids": [c1["id"], c2["id"]],
            "feature_ids": [f1["id"], f2["id"]]
        }
    )

    res = client.get("/tools/")
    assert res.status_code == 200
    data = res.json()["items"]
    matching = [t for t in data if t["slug"] == "complex-tool"]
    assert len(matching) == 1