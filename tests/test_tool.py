# tests/test_tool.py

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
    assert res.json()["items"] == []


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

    tools = res.json()["items"]
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
    results = res.json()["items"]
    assert len(results) == 1
    assert results[0]["name"] == "PostgreSQL"


def test_search_case_insensitive(client):
    client.post(
        "/tools/",
        json={"name": "Docker", "slug": "docker", "short_description": "Container platform"}
    )

    res = client.get("/tools/?search=docKER")
    assert res.status_code == 200
    results = res.json()["items"]
    assert len(results) == 1
    assert results[0]['name'] == 'Docker'


def test_search_no_match(client):
    client.post(
        "/tools/",
        json={"name": "FastAPI", "slug": "fastapi", "short_description": "Python web framework"}
    )

    response = client.get("/tools/?search=nonexistentterm")
    assert response.status_code == 200
    assert response.json()["items"] == []


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
    assert len(check_response.json()["items"]) == 1
    assert check_response.json()["items"][0]["name"] == "SafeTool"


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
    assert res.json()["items"] == []


def test_filter_free_plan_and_api(client):
    client.post("/tools/", json={"name": "n8n", "slug": "n8n", "has_free_plan": True, "api_available": True, "short_description": "Auto tool"})
    client.post("/tools/", json={"name": "Zapier", "slug": "zapier", "has_free_plan": True, "api_available": True, "short_description": "Auto tool"})
    client.post("/tools/", json={"name": "Make", "slug": "make", "has_free_plan": True, "api_available": False, "short_description": "Auto tool"})

    response = client.get("/tools/?free_plan=true&api_available=true")
    assert response.status_code == 200
    data = response.json()["items"]
    names = [t["name"] for t in data]
    assert "n8n" in names
    assert "Zapier" in names
    assert "Make" not in names


def test_filter_free_plan_false(client):
    client.post("/tools/", json={"name": "ToolFree", "slug": "toolfree", "short_description": "test", "has_free_plan": True})
    client.post("/tools/", json={"name": "ToolPaid", "slug": "toolpaid", "short_description": "test", "has_free_plan": False})

    response = client.get("/tools/?free_plan=false")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["name"] == "ToolPaid"


def test_search_and_filters_combined(client):
    client.post("/tools/", json={"name": "n8n", "slug": "n8n", "short_description": "Workflow automation", "has_free_plan": True, "api_available": True})
    client.post("/tools/", json={"name": "ManualTool", "slug": "manual", "short_description": "Workflow automation", "has_free_plan": True, "api_available": False})

    response = client.get("/tools/?search=automation&free_plan=true&api_available=true")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["name"] == "n8n"


def test_filter_invalid_boolean_raises_422(client):
    response = client.get("/tools/?free_plan=maybe")
    assert response.status_code == 422


def test_filter_pricing_model(client):
    client.post(
        "/tools/",
        json={"name": "Notion", "slug": "notion", "short_description": 'test', "pricing_model": "freemium"}
    )
    client.post(
        "/tools/",
        json={"name": "Linear", "slug": "linear", "pricing_model": "paid"}
    )

    response = client.get("/tools/?pricing_model=freemium")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["name"] == "Notion"
    assert data[0]["pricing_model"] == "freemium"


def test_filter_pricing_model_none(client):
    client.post(
        "/tools/",
        json={"name": "Slack", "slug": "slack", "pricing_model": "freemium"}
    )

    response = client.get("/tools/?pricing_model=paid")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_create_category_success(client):
    response = client.post(
        "/categories/",
        json={"name": "Automation", "slug": "automation", "description": "Workflow tools"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Automation"
    assert data["slug"] == "automation"
    assert "id" in data


def test_create_category_duplicate_name(client):
    client.post(
        "/categories/",
        json={"name": "AI", "slug": "ai", "description": "Artificial Intelligence"}
    )

    response = client.post(
        "/categories/",
        json={"name": "AI", "slug": "ai-duplicate", "description": "Duplicate test"}
    )
    assert response.status_code == 409


def test_get_categories_sorted(client):
    client.post("/categories/", json={"name": "Database", "slug": "database"})
    client.post("/categories/", json={"name": "API", "slug": "api"})
    client.post("/categories/", json={"name": "Automation", "slug": "automation"})

    response = client.get("/categories/")
    assert response.status_code == 200
    data = response.json()
    
    names = [c["name"] for c in data]
    assert names == ["API", "Automation", "Database"]


def test_create_tool_with_categories(client):
    cat1 = client.post("/categories/", json={"name": "Automation", "slug": "automation"}).json()
    cat2 = client.post("/categories/", json={"name": "AI", "slug": "ai"}).json()

    response = client.post(
        "/tools/",
        json={
            "name": "n8n",
            "slug": "n8n",
            "short_description": "Workflow tool",
            "category_ids": [cat1["id"], cat2["id"]]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["categories"]) == 2
    category_names = {c["name"] for c in data["categories"]}
    assert category_names == {"Automation", "AI"}


def test_create_tool_unknown_category(client):
    response = client.post(
        "/tools/",
        json={
            "name": "GhostTool",
            "slug": "ghost",
            "category_ids": [9999]
        }
    )
    assert response.status_code == 404

    get_response = client.get("/tools/")
    assert get_response.status_code == 200
    assert get_response.json()["items"] == []


def test_update_tool_replace_categories(client):
    cat1 = client.post("/categories/", json={"name": "DevOps", "slug": "devops"}).json()
    cat2 = client.post("/categories/", json={"name": "Cloud", "slug": "cloud"}).json()

    tool_res = client.post(
        "/tools/",
        json={"name": "Docker", "slug": "docker", "category_ids": [cat1["id"]]}
    ).json()
    tool_id = tool_res["id"]

    response = client.patch(
        f"/tools/{tool_id}",
        json={"category_ids": [cat2["id"]]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Cloud"


def test_update_tool_keep_categories(client):
    cat = client.post("/categories/", json={"name": "Security", "slug": "security"}).json()
    tool_res = client.post(
        "/tools/",
        json={"name": "Vault", "slug": "vault", "category_ids": [cat["id"]]}
    ).json()
    tool_id = tool_res["id"]

    response = client.patch(
        f"/tools/{tool_id}",
        json={"short_description": "Updated description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Security"


def test_update_tool_clear_categories(client):
    cat = client.post("/categories/", json={"name": "Monitoring", "slug": "monitoring"}).json()
    tool_res = client.post(
        "/tools/",
        json={"name": "Grafana", "slug": "grafana", "category_ids": [cat["id"]]}
    ).json()
    tool_id = tool_res["id"]

    response = client.patch(
        f"/tools/{tool_id}",
        json={"category_ids": []}
    )
    assert response.status_code == 200
    assert response.json()["categories"] == []


def test_update_tool_null_categories(client):
    tool_res = client.post(
        "/tools/",
        json={"name": "NullTest", "slug": "null-test"}
    ).json()
    tool_id = tool_res["id"]

    response = client.patch(
        f"/tools/{tool_id}",
        json={"category_ids": None}
    )
    assert response.status_code == 422


def test_delete_tool_removes_links(client):
    cat = client.post("/categories/", json={"name": "Temporary", "slug": "temp"}).json()
    tool_res = client.post(
        "/tools/",
        json={"name": "TempTool", "slug": "temp-tool", "category_ids": [cat["id"]]}
    ).json()
    tool_id = tool_res["id"]

    del_response = client.delete(f"/tools/{tool_id}")
    assert del_response.status_code == 204

    cat_response = client.get("/categories/")
    assert cat_response.status_code == 200
    categories = cat_response.json()
    assert any(c["id"] == cat["id"] for c in categories)


def test_filter_tools_by_category(client):
    cat = client.post("/categories/", json={"name": "Automation", "slug": "automation"}).json()
    client.post(
        "/tools/",
        json={"name": "n8n", "slug": "n8n", "category_ids": [cat["id"]]}
    )
    client.post(
        "/tools/",
        json={"name": "Unrelated Tool", "slug": "unrelated", "category_ids": []}
    )

    response = client.get("/tools/?category=automation")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["slug"] == "n8n"


def test_filter_tools_by_unknown_category(client):
    response = client.get("/tools/?category=nonexistent")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_get_category_by_slug_success(client):
    client.post("/categories/", json={"name": "Design", "slug": "design"})

    response = client.get("/categories/design")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Design"
    assert data["slug"] == "design"


def test_get_category_by_slug_not_found(client):
    response = client.get("/categories/nonexistent-category")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_category_tools_success(client):
    cat = client.post("/categories/", json={"name": "DevOps", "slug": "devops"}).json()
    client.post(
        "/tools/",
        json={"name": "Docker", "slug": "docker", "category_ids": [cat["id"]]}
    )

    response = client.get("/categories/devops/tools")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["name"] == "Docker"


def test_category_tools_unknown_category(client):
    response = client.get("/categories/nonexistent-category/tools")
    assert response.status_code == 404


def test_category_tools_with_filters(client):
    cat = client.post("/categories/", json={"name": "AI", "slug": "ai"}).json()
    
    client.post(
        "/tools/",
        json={"name": "ChatGPT Free", "slug": "chatgpt-free", "has_free_plan": True, "category_ids": [cat["id"]]}
    )
    client.post(
        "/tools/",
        json={"name": "Enterprise AI", "slug": "enterprise-ai", "has_free_plan": False, "category_ids": [cat["id"]]}
    )
    response = client.get("/categories/ai/tools?free_plan=true")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["slug"] == "chatgpt-free"


def test_category_with_no_tools(client):
    client.post("/categories/", json={"name": "Empty Category", "slug": "empty-cat"})

    response = client.get("/categories/empty-cat/tools")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_tool_in_two_categories_not_duplicated(client):
    cat1 = client.post("/categories/", json={"name": "Cat 1", "slug": "cat-1"}).json()
    cat2 = client.post("/categories/", json={"name": "Cat 2", "slug": "cat-2"}).json()

    client.post(
        "/tools/",
        json={"name": "MultiCat Tool", "slug": "multicat-tool", "category_ids": [cat1["id"], cat2["id"]]}
    )

    response = client.get("/tools/")
    assert response.status_code == 200
    data = response.json()["items"]
    
    matching_tools = [t for t in data if t["slug"] == "multicat-tool"]
    assert len(matching_tools) == 1


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


def test_create_plan_and_appear_in_tool(client):
    tool = client.post(
        "/tools/",
        json={"name": "Notion", "slug": "notion"}
    ).json()

    plan_res = client.post(
        f"/tools/{tool['id']}/pricing-plans",
        json={"name": "Pro", "price": "20.00", "billing_period": "monthly"}
    )
    assert plan_res.status_code == 201
    
    plan_data = plan_res.json()
    assert plan_data["price"] == "20.00"

    tool_get = client.get("/tools/notion")
    assert tool_get.status_code == 200
    tool_json = tool_get.json()
    assert len(tool_json["pricing_plans"]) == 1
    assert tool_json["pricing_plans"][0]["name"] == "Pro"
    assert tool_json["pricing_plans"][0]["price"] == "20.00"


def test_create_plan_unknown_tool(client):
    res = client.post(
        "/tools/999/pricing-plans",
        json={"name": "Pro", "price": "20.00"}
    )
    assert res.status_code == 404


def test_create_plan_negative_price_and_invalid_billing(client):
    tool = client.post(
        "/tools/",
        json={"name": "Test Tool", "slug": "test-tool"}
    ).json()

    neg_res = client.post(
        f"/tools/{tool['id']}/pricing-plans",
        json={"name": "Pro", "price": "-5.00"}
    )
    assert neg_res.status_code == 422

    inv_res = client.post(
        f"/tools/{tool['id']}/pricing-plans",
        json={"name": "Pro", "price": "10.00", "billing_period": "weekly"}
    )
    assert inv_res.status_code == 422


def test_patch_pricing_plan(client):
    tool = client.post(
        "/tools/",
        json={"name": "Airtable", "slug": "airtable"}
    ).json()

    plan = client.post(
        f"/tools/{tool['id']}/pricing-plans",
        json={"name": "Team", "price": "50.00", "billing_period": "monthly"}
    ).json()

    patch_res = client.patch(
        f"/pricing-plans/{plan['id']}",
        json={"price": "55.00"}
    )
    assert patch_res.status_code == 200
    updated_plan = patch_res.json()
    assert updated_plan["price"] == "55.00"
    assert updated_plan["name"] == "Team" 


def test_delete_plan_keeps_tool(client):
    tool = client.post(
        "/tools/",
        json={"name": "Slack", "slug": "slack"}
    ).json()

    plan = client.post(
        f"/tools/{tool['id']}/pricing-plans",
        json={"name": "Business", "price": "12.00"}
    ).json()

    del_res = client.delete(f"/pricing-plans/{plan['id']}")
    assert del_res.status_code == 204

    tool_get = client.get("/tools/slack")
    assert tool_get.status_code == 200
    assert tool_get.json()["pricing_plans"] == []


def test_delete_tool_deletes_plans_cascade(client):
    tool = client.post(
        "/tools/",
        json={"name": "Zoom", "slug": "zoom"}
    ).json()

    plan = client.post(
        f"/tools/{tool['id']}/pricing-plans",
        json={"name": "Pro", "price": "15.00"}
    ).json()

    del_tool = client.delete(f"/tools/{tool['id']}")
    assert del_tool.status_code == 204

    patch_res = client.patch(
        f"/pricing-plans/{plan['id']}",
        json={"price": "20.00"}
    )
    assert patch_res.status_code == 404


def test_plans_ordered_by_price(client):
    tool = client.post(
        "/tools/",
        json={"name": "GitHub", "slug": "github"}
    ).json()

    client.post(f"/tools/{tool['id']}/pricing-plans", json={"name": "Enterprise", "price": "100.00"})
    client.post(f"/tools/{tool['id']}/pricing-plans", json={"name": "Free", "price": "0.00"})
    client.post(f"/tools/{tool['id']}/pricing-plans", json={"name": "Team", "price": "40.00"})

    res = client.get("/tools/github")
    assert res.status_code == 200
    plans = res.json()["pricing_plans"]
    assert len(plans) == 3
    assert plans[0]["price"] == "0.00"
    assert plans[1]["price"] == "40.00"
    assert plans[2]["price"] == "100.00"


def test_pagination_defaults_and_limits(client):
    for i in range(25):
        client.post("/tools/", json={"name": f"Tool {i:02d}", "slug": f"tool-{i}"})

    res = client.get("/tools/")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 20
    assert data["total"] == 25

    res_offset = client.get("/tools/?limit=10&offset=20")
    assert res_offset.status_code == 200
    data_offset = res_offset.json()
    assert len(data_offset["items"]) == 5
    assert data_offset["total"] == 25

    res_beyond = client.get("/tools/?offset=200")
    assert res_beyond.status_code == 200
    data_beyond = res_beyond.json()
    assert data_beyond["items"] == []
    assert data_beyond["total"] == 25

    assert client.get("/tools/?limit=0").status_code == 422
    assert client.get("/tools/?limit=101").status_code == 422
    assert client.get("/tools/?offset=-1").status_code == 422

def test_sorting_and_stability(client):
    client.post("/tools/", json={"name": "Alpha", "slug": "alpha-1"})
    client.post("/tools/", json={"name": "Alpha", "slug": "alpha-2"})
    client.post("/tools/", json={"name": "Beta", "slug": "beta"})

    res_desc = client.get("/tools/?sort=-name")
    assert res_desc.status_code == 200
    items_desc = res_desc.json()["items"]
    assert items_desc[0]["name"] == "Beta"

    res_call1 = client.get("/tools/?sort=name")
    res_call2 = client.get("/tools/?sort=name")
    assert res_call1.json()["items"] == res_call2.json()["items"]


def test_filters_and_pricing_count(client):
    t1 = client.post("/tools/", json={"name": "Tool One", "slug": "t1"}).json()
    client.post(f"/tools/{t1['id']}/pricing-plans", json={"name": "Free", "price": "0.00"})
    client.post(f"/tools/{t1['id']}/pricing-plans", json={"name": "Standard", "price": "10.00"})
    client.post(f"/tools/{t1['id']}/pricing-plans", json={"name": "Pro", "price": "50.00"})

    t2 = client.post("/tools/", json={"name": "Tool Two", "slug": "t2"}).json()
    client.post(f"/tools/{t2['id']}/pricing-plans", json={"name": "Expensive", "price": "100.00"})

    res = client.get("/tools/?max_price=20.00")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Tool One"



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
    sol_id = sol_res["id"]

    del_used = client.delete(f"/tools/{t1['id']}")
    assert del_used.status_code == 409

    get_sol = client.get("/solutions/sol-slug")
    assert get_sol.status_code == 200
    assert len(get_sol.json()["steps"]) == 1

    del_unused = client.delete(f"/tools/{t2['id']}")
    assert del_unused.status_code == 204

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

def test_create_comparison_validation_bounds_422(client):
    t1 = client.post("/tools/", json={"name": "Tool 1", "slug": "t1"}).json()
    
    assert client.post("/comparisons/", json={"tool_ids": [t1["id"]]}).status_code == 422
    
    assert client.post("/comparisons/", json={"tool_ids": [t1["id"], t1["id"]]}).status_code == 422

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

    del_comp = client.delete(f"/comparisons/{comp['slug'].replace('-vs-', '')}")
    comp_list = client.get("/comparisons/").json()
    comp_id = client.get(f"/comparisons/{comp['slug']}").json() 

    del_tool = client.delete(f"/tools/{t1['id']}")
    assert del_tool.status_code == 409