def create_tool(client, name="Test Tool", slug="test-tool", **kwargs):
    payload = {"name": name, "slug": slug, "short_description": "Default desc", **kwargs}
    return client.post("/tools/", json=payload).json()

def create_category(client, name="Test Category", slug="test-category", **kwargs):
    payload = {"name": name, "slug": slug, **kwargs}
    return client.post("/categories/", json=payload).json()