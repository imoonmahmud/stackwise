const params = new URLSearchParams(window.location.search);
const slug = params.get("slug");

const statusEl = document.getElementById("status");
const contentEl = document.getElementById("tool-content");
const nameEl = document.getElementById("tool-name");
const descEl = document.getElementById("tool-description");
const badgesEl = document.getElementById("tool-badges");
const pricingInfoEl = document.getElementById("pricing-info");
const freePlanInfoEl = document.getElementById("free-plan-info");
const apiInfoEl = document.getElementById("api-info");

async function initToolPage() {
    if (!slug) {
        statusEl.textContent = "No tool specified.";
        return;
    }

    try {
        const tool = await getTool(slug);
        document.title = `${tool.name} - Stackwise`;
        nameEl.textContent = tool.name;
        descEl.textContent = tool.short_description || "No description provided.";

        if (tool.categories) {
            tool.categories.forEach(cat => {
                const badge = document.createElement("span");
                badge.className = "badge category-badge";
                badge.textContent = cat.name;
                badgesEl.appendChild(badge);
            });
        }

        pricingInfoEl.textContent = `Pricing Model: ${tool.pricing_model || "Not specified"}`;
        freePlanInfoEl.textContent = `Free Plan: ${tool.has_free_plan ? "Yes" : "No"}`;
        apiInfoEl.textContent = `API Available: ${tool.api_available ? "Yes" : "No"}`;

        statusEl.style.display = "none";
        contentEl.style.display = "block";
    } catch (error) {
        statusEl.textContent = "Tool not found.";
        console.error(error);
    }
}

initToolPage();