const searchInput = document.getElementById("search");
const freePlanCheckbox = document.getElementById("free-plan");
const apiCheckbox = document.getElementById("api");
const pricingSelect = document.getElementById("pricing");
const statusEl = document.getElementById("status");
const gridEl = document.getElementById("tools-grid");

let debounceTimer = null;

function renderTools(tools) {
    gridEl.innerHTML = "";
    if (!tools || tools.length === 0) {
        statusEl.textContent = "No tools found";
        return;
    }
    statusEl.textContent = "";

    tools.forEach(tool => {
        const card = document.createElement("div");
        card.className = "tool-card";

        // Card top header (Avatar, Title, Pricing Pill)
        const cardHeader = document.createElement("div");
        cardHeader.className = "card-header";

        const titleArea = document.createElement("div");
        titleArea.className = "card-title-area";

        // Avatar letter
        const avatar = document.createElement("div");
        avatar.className = "tool-avatar";
        avatar.textContent = tool.name ? tool.name.charAt(0).toUpperCase() : "?";
        titleArea.appendChild(avatar);

        const textBlock = document.createElement("div");
        const titleHeading = document.createElement("h3");
        const titleLink = document.createElement("a");
        titleLink.href = `tool.html?slug=${encodeURIComponent(tool.slug)}`;
        titleLink.textContent = tool.name;
        titleHeading.appendChild(titleLink);
        textBlock.appendChild(titleHeading);

        // Subtitle category
        if (tool.categories && tool.categories.length > 0) {
            const sub = document.createElement("div");
            sub.className = "tool-category-sub";
            sub.textContent = tool.categories[0].name;
            textBlock.appendChild(sub);
        }

        titleArea.appendChild(textBlock);
        cardHeader.appendChild(titleArea);

        // Pricing model pill badge
        if (tool.pricing_model) {
            const pill = document.createElement("span");
            pill.className = "pricing-pill";
            pill.textContent = tool.pricing_model;
            cardHeader.appendChild(pill);
        }

        card.appendChild(cardHeader);

        // Description
        if (tool.short_description) {
            const desc = document.createElement("p");
            desc.textContent = tool.short_description;
            card.appendChild(desc);
        }

        // Category & feature badges at bottom
        const badgesContainer = document.createElement("div");
        badgesContainer.className = "badges";

        if (tool.categories && tool.categories.length > 0) {
            tool.categories.forEach(cat => {
                const badge = document.createElement("span");
                badge.className = "badge";
                badge.textContent = cat.name;
                badgesContainer.appendChild(badge);
            });
        }

        if (tool.has_free_plan) {
            const badge = document.createElement("span");
            badge.className = "badge";
            badge.textContent = "Free plan";
            badgesContainer.appendChild(badge);
        }

        if (tool.api_available) {
            const badge = document.createElement("span");
            badge.className = "badge";
            badge.textContent = "API";
            badgesContainer.appendChild(badge);
        }

        card.appendChild(badgesContainer);
        gridEl.appendChild(card);
    });
}

async function loadTools() {
    statusEl.textContent = "Loading...";
    gridEl.innerHTML = "";

    const filters = {
        search: searchInput.value.trim(),
        free_plan: freePlanCheckbox.checked ? true : undefined,
        api_available: apiCheckbox.checked ? true : undefined,
        pricing_model: pricingSelect.value || undefined
    };

    try {
        const tools = await getTools(filters);
        renderTools(tools);
    } catch (error) {
        statusEl.textContent = "Could not load tools. Is the server running?";
        console.error(error);
    }
}

searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadTools, 300);
});

freePlanCheckbox.addEventListener("change", loadTools);
apiCheckbox.addEventListener("change", loadTools);
pricingSelect.addEventListener("change", loadTools);

loadTools();