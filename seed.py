import json
import httpx

with open('seed_tools.json', encoding='utf-8') as f:
    tools = json.load(f)

for tool in tools:
    response = httpx.post("http://127.0.0.1:8000/tools/", json=tool)
    print(tool["slug"], response.status_code)