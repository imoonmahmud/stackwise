const API_URL = "http://127.0.0.1:8000";

async function getJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
}

async function getTools(filters = {}) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && value !== "") {
            params.append(key, value);
        }
    }
    const query = params.toString();
    const url = query ? `${API_URL}/tools/?${query}` : `${API_URL}/tools/`;
    return await getJSON(url);
}

async function getTool(slug) {
    try {
        return await getJSON(`${API_URL}/tools/${slug}`);
    } catch (error) {
        if (error.message.includes("404")) {
            throw new Error("Tool not found");
        }
        throw error;
    }
}