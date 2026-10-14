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