
/* =====================================================
   ROOTLEARN — LEARNING RESOURCES
   Loads resources from the Flask API and SQLite database.
   ===================================================== */

const API_BASE = "/api";

const resourceGrid = document.getElementById("resourceGrid");
const resourceMessage = document.getElementById("resourceMessage");
const resourceCount = document.getElementById("resourceCount");
const topicFilters = document.getElementById("topicFilters");
const resourceSearch = document.getElementById("resourceSearch");

let allResources = [];
let allTopics = [];
let selectedTopic = "all";

const RESOURCE_TYPES = {
    notes: {
        label: "Notes",
        icon: "▤",
        action: "Read notes"
    },
    video: {
        label: "Video",
        icon: "▷",
        action: "Watch video"
    },
    practice: {
        label: "Practice",
        icon: "✳",
        action: "Start practising"
    }
};

function showResourceMessage(message, isError = false) {
    resourceMessage.textContent = message;
    resourceMessage.classList.toggle("error", isError);
}

function getResourceType(type) {
    const normalized = String(type || "").toLowerCase();

    if (normalized.includes("note") || normalized.includes("article")) {
        return RESOURCE_TYPES.notes;
    }

    if (normalized.includes("video")) {
        return RESOURCE_TYPES.video;
    }

    if (normalized.includes("practice") || normalized.includes("exercise")) {
        return RESOURCE_TYPES.practice;
    }

    return {
        label: type || "Resource",
        icon: "↗",
        action: "Open resource"
    };
}

function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        element.textContent = text;
    }

    return element;
}

function createResourceCard(resource) {
    const card = createElement("article", "resource-card");

    const top = createElement("div", "resource-card-top");
    const type = getResourceType(resource.resource_type);

    const icon = createElement("span", "resource-icon", type.icon);
    icon.setAttribute("aria-hidden", "true");

    const typeLabel = createElement("span", "resource-type", type.label);

    top.append(icon, typeLabel);

    const title = createElement(
        "h3",
        "",
        resource.resource_title || "Learning resource"
    );

    const topic = createElement(
        "p",
        "resource-topic",
        resource.topic_name || "Python"
    );

    const description = createElement(
        "p",
        "resource-description",
        resource.resource_description || "Explore this learning resource."
    );

    card.append(top, title, topic, description);

    const url = String(resource.resource_url || "").trim();

    if (url) {
        try {
            const parsedURL = new URL(url, window.location.origin);

            if (["http:", "https:"].includes(parsedURL.protocol)) {
                const link = createElement("a", "", type.action);
                link.href = parsedURL.href;
                link.target = "_blank";
                link.rel = "noopener noreferrer";

                const arrow = createElement("span", "", "↗");
                arrow.setAttribute("aria-hidden", "true");
                link.appendChild(arrow);

                card.appendChild(link);
            }
        } catch (error) {
            console.warn("A resource URL could not be displayed.");
        }
    }

    return card;
}

function renderTopicFilters() {
    topicFilters.replaceChildren();

    const allButton = createElement("button", "topic-filter", "All topics");
    allButton.type = "button";
    allButton.dataset.topic = "all";

    topicFilters.appendChild(allButton);

    allTopics.forEach((topic) => {
        const button = createElement(
            "button",
            "topic-filter",
            topic.topic_name
        );

        button.type = "button";
        button.dataset.topic = String(topic.topic_id);

        topicFilters.appendChild(button);
    });

    updateTopicFilterStates();
}

function updateTopicFilterStates() {
    topicFilters.querySelectorAll(".topic-filter").forEach((button) => {
        const active = button.dataset.topic === String(selectedTopic);

        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
    });
}

function renderResources() {
    const searchTerm = resourceSearch.value.trim().toLowerCase();

    const filteredResources = allResources.filter((resource) => {
        const matchesTopic =
            selectedTopic === "all" ||
            String(resource.topic_id) === String(selectedTopic);

        const searchableText = [
            resource.resource_title,
            resource.resource_type,
            resource.resource_description,
            resource.topic_name
        ].join(" ").toLowerCase();

        const matchesSearch = searchableText.includes(searchTerm);

        return matchesTopic && matchesSearch;
    });

    resourceGrid.replaceChildren();

    filteredResources.forEach((resource) => {
        resourceGrid.appendChild(createResourceCard(resource));
    });

    resourceCount.textContent =
        `${filteredResources.length} resource${filteredResources.length === 1 ? "" : "s"}`;

    if (filteredResources.length === 0) {
        showResourceMessage(
            "No matching resources found. Try another topic or search term."
        );
    } else {
        showResourceMessage("");
    }
}

async function loadLearningResources() {
    showResourceMessage("Loading your learning library...");

    try {
        const [resourcesResponse, topicsResponse] = await Promise.all([
            fetch(`${API_BASE}/learning-resources`),
            fetch(`${API_BASE}/topics`)
        ]);

        if (!resourcesResponse.ok || !topicsResponse.ok) {
            throw new Error("The learning library API is not available yet.");
        }

        const resourcesData = await resourcesResponse.json();
        const topicsData = await topicsResponse.json();

        allResources = Array.isArray(resourcesData)
            ? resourcesData
            : resourcesData.resources || [];

        allTopics = Array.isArray(topicsData)
            ? topicsData
            : topicsData.topics || [];

        if (!Array.isArray(allResources) || !Array.isArray(allTopics)) {
            throw new Error("The server returned an unexpected data format.");
        }

        renderTopicFilters();

        const params = new URLSearchParams(window.location.search);
        const requestedTopic = params.get("topic");

        if (
            requestedTopic &&
            allTopics.some(
                (topic) => String(topic.topic_id) === requestedTopic
            )
        ) {
            selectedTopic = requestedTopic;
        }

        updateTopicFilterStates();
        renderResources();

    } catch (error) {
        console.error("Learning resources could not be loaded:", error);

        resourceCount.textContent = "Library unavailable";

        showResourceMessage(
            "We couldn't load your learning resources yet. " +
            "Please check that the RootLearn Flask server is running " +
            "and that its learning-resources and topics API routes are configured.",
            true
        );
    }
}

topicFilters.addEventListener("click", (event) => {
    const button = event.target.closest(".topic-filter");

    if (!button) {
        return;
    }

    selectedTopic = button.dataset.topic;
    updateTopicFilterStates();
    renderResources();
});

resourceSearch.addEventListener("input", renderResources);

loadLearningResources();
