
/* =========================================
   ROOTLEARN — PYTHON LEARNING PATH
   ========================================= */

/*
  Demo data for the first frontend version.
  Later, Flask will load topic and progress data
  from the SQLite database.
*/

const pythonTopics = [
    {
        id: "PY01",
        title: "Variables",
        description: "Learn how to store, name, and reuse information in Python.",
        prerequisites: [],
        objectives: [
            "Understand what a variable represents.",
            "Create variables using meaningful names.",
            "Assign and update values."
        ],
        example: 'name = "Alex"\nage = 20',
        status: "not-started"
    },
    {
        id: "PY02",
        title: "Data Types",
        description: "Understand the different kinds of values Python can work with.",
        prerequisites: ["PY01"],
        objectives: [
            "Recognize strings, integers, floats, and booleans.",
            "Use the type() function.",
            "Understand basic type conversion."
        ],
        example: 'age = 20\nprice = 19.5\nis_student = True',
        status: "not-started"
    },
    {
        id: "PY03",
        title: "Operators",
        description: "Use operators to calculate values and compare expressions.",
        prerequisites: ["PY01", "PY02"],
        objectives: [
            "Use arithmetic operators.",
            "Compare values using comparison operators.",
            "Understand logical operators."
        ],
        example: "total = 10 + 5\nis_valid = total > 12",
        status: "not-started"
    },
    {
        id: "PY04",
        title: "Conditional Statements",
        description: "Make programs choose different actions based on conditions.",
        prerequisites: ["PY03"],
        objectives: [
            "Write if and else statements.",
            "Use elif for multiple conditions.",
            "Understand indentation in conditional blocks."
        ],
        example: 'score = 75\n\nif score >= 50:\n    print("Passed")\nelse:\n    print("Try again")',
        status: "not-started"
    },
    {
        id: "PY05",
        title: "Loops",
        description: "Repeat instructions efficiently using Python loops.",
        prerequisites: ["PY01", "PY03", "PY04"],
        objectives: [
            "Use for loops to iterate over sequences.",
            "Use while loops for repeated conditions.",
            "Understand break and continue."
        ],
        example: "for number in range(3):\n    print(number)",
        status: "not-started"
    },
    {
        id: "PY06",
        title: "Functions",
        description: "Organize reusable instructions into named blocks of code.",
        prerequisites: ["PY01", "PY02"],
        objectives: [
            "Define a function using def.",
            "Pass arguments and parameters.",
            "Return results from functions."
        ],
        example: "def greet(name):\n    return f'Hello, {name}!'",
        status: "not-started"
    },
    {
        id: "PY07",
        title: "Lists and Tuples",
        description: "Store and access collections of values in an organized way.",
        prerequisites: ["PY01", "PY02"],
        objectives: [
            "Create lists and tuples.",
            "Access elements using indexes.",
            "Understand mutable and immutable collections."
        ],
        example: 'fruits = ["apple", "mango"]\ncoordinates = (10, 20)',
        status: "not-started"
    },
    {
        id: "PY08",
        title: "Dictionaries and Sets",
        description: "Work with key-value pairs and collections of unique items.",
        prerequisites: ["PY02", "PY07"],
        objectives: [
            "Create dictionaries using key-value pairs.",
            "Retrieve and update dictionary values.",
            "Use sets to store unique elements."
        ],
        example: 'student = {"name": "Alex", "age": 20}\nunique_numbers = {1, 2, 3}',
        status: "not-started"
    },
    {
        id: "PY09",
        title: "Strings",
        description: "Manipulate text using indexing, methods, and formatting.",
        prerequisites: ["PY01", "PY05"],
        objectives: [
            "Access characters and string slices.",
            "Use common string methods.",
            "Format strings with f-strings."
        ],
        example: 'message = "hello python"\nprint(message.upper())',
        status: "not-started"
    },
    {
        id: "PY10",
        title: "Object-Oriented Programming",
        description: "Model data and behavior using classes and objects.",
        prerequisites: ["PY01", "PY02", "PY06"],
        objectives: [
            "Understand classes and objects.",
            "Create attributes and methods.",
            "Understand constructors and basic inheritance."
        ],
        example: 'class Student:\n    def __init__(self, name):\n        self.name = name',
        status: "not-started"
    }
];

const topicGrid = document.getElementById("topicGrid");
const topicSearch = document.getElementById("topicSearch");
const emptyState = document.getElementById("topicEmptyState");
const topicFilters = document.querySelectorAll(".topic-filter");

let activeFilter = "all";

/* Safely encode text before inserting it into HTML. */
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}

/* Find a topic's display name from its ID. */
function getTopicTitle(topicId) {
    const topic = pythonTopics.find(item => item.id === topicId);
    return topic ? topic.title : "Unknown topic";
}

/* Update the summary counts. */
function updateTopicSummary() {
    const completed = pythonTopics.filter(
        topic => topic.status === "completed"
    ).length;

    const inProgress = pythonTopics.filter(
        topic => topic.status === "in-progress"
    ).length;

    document.getElementById("totalTopics").textContent =
        pythonTopics.length;

    document.getElementById("completedTopics").textContent =
        completed;

    document.getElementById("inProgressTopics").textContent =
        inProgress;
}

/* Create the markup for an individual topic card. */
function createTopicCard(topic) {
    const statusLabels = {
        "not-started": "Not started",
        "in-progress": "In progress",
        "completed": "Completed"
    };

    const prerequisitesText = topic.prerequisites.length
        ? topic.prerequisites.map(getTopicTitle).join(", ")
        : "Start here — no prerequisites";

    return `
        <button
            type="button"
            class="topic-card"
            data-topic-id="${escapeHTML(topic.id)}"
            aria-label="Explore ${escapeHTML(topic.title)}">

            <span class="topic-card-top">
                <span class="topic-number">${escapeHTML(topic.id)}</span>

                <span class="topic-status status-${escapeHTML(topic.status)}">
                    ${escapeHTML(statusLabels[topic.status])}
                </span>
            </span>

            <h3>${escapeHTML(topic.title)}</h3>

            <p class="topic-description">
                ${escapeHTML(topic.description)}
            </p>

            <span class="topic-card-bottom">
                <span class="topic-prerequisite">
                    <strong>Prerequisites:</strong>
                    ${escapeHTML(prerequisitesText)}
                </span>

                <span class="topic-open" aria-hidden="true">↗</span>
            </span>
        </button>
    `;
}

/* Apply the search query and selected status filter. */
function renderTopics() {
    const query = topicSearch.value.trim().toLowerCase();

    const filteredTopics = pythonTopics.filter(topic => {
        const searchableText = [
            topic.id,
            topic.title,
            topic.description,
            ...topic.prerequisites.map(getTopicTitle)
        ].join(" ").toLowerCase();

        const matchesSearch = searchableText.includes(query);

        const matchesFilter =
            activeFilter === "all" ||
            topic.status === activeFilter;

        return matchesSearch && matchesFilter;
    });

    topicGrid.innerHTML = filteredTopics.map(createTopicCard).join("");
    emptyState.hidden = filteredTopics.length > 0;
}

/* Show topic information in a dialog-like modal. */
function openTopicDetails(topicId) {
    const topic = pythonTopics.find(item => item.id === topicId);

    if (!topic) return;

    const existingModal = document.getElementById("topicDetailsModal");

    if (existingModal) {
        existingModal.remove();
    }

    const prerequisiteNames = topic.prerequisites.length
        ? topic.prerequisites.map(getTopicTitle)
        : ["No prerequisites — a great place to begin!"];

    const modal = document.createElement("div");
    modal.id = "topicDetailsModal";
    modal.className = "topic-modal-backdrop";

    modal.innerHTML = `
        <section
            class="topic-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="topicModalTitle">

            <button
                type="button"
                class="topic-modal-close"
                aria-label="Close topic details">×</button>

            <span class="eyebrow">${escapeHTML(topic.id)} · PYTHON FOUNDATIONS</span>

            <h2 id="topicModalTitle">${escapeHTML(topic.title)}</h2>

            <p class="topic-modal-description">
                ${escapeHTML(topic.description)}
            </p>

            <h3>What you'll learn</h3>

            <ul class="topic-objectives">
                ${topic.objectives.map(objective =>
                    `<li>${escapeHTML(objective)}</li>`
                ).join("")}
            </ul>

            <h3>Prerequisite concepts</h3>

            <ul class="topic-prerequisites">
                ${prerequisiteNames.map(name =>
                    `<li>${escapeHTML(name)}</li>`
                ).join("")}
            </ul>

            <h3>Example code</h3>

            <pre class="topic-code"><code>${escapeHTML(topic.example)}</code></pre>

            <p class="topic-modal-note">
                Your learning progress will be connected to your account
                when the backend and SQLite integration are added.
            </p>

            <button type="button" class="button button-primary topic-modal-done">
                Got it
            </button>
        </section>
    `;

    document.body.appendChild(modal);

    const closeButton = modal.querySelector(".topic-modal-close");
    const doneButton = modal.querySelector(".topic-modal-done");

    function closeModal() {
        document.removeEventListener("keydown", handleEscape);
        modal.remove();
    }

    function handleEscape(event) {
        if (event.key === "Escape") {
            closeModal();
        }
    }

    closeButton.addEventListener("click", closeModal);
    doneButton.addEventListener("click", closeModal);

    modal.addEventListener("click", event => {
        if (event.target === modal) closeModal();
    });

    document.addEventListener("keydown", handleEscape);
    closeButton.focus();
}

/* Search as the student types. */
topicSearch.addEventListener("input", renderTopics);

/* Filter topics by progress status. */
topicFilters.forEach(button => {
    button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;

        topicFilters.forEach(filterButton => {
            const isActive = filterButton === button;

            filterButton.classList.toggle("active", isActive);
            filterButton.setAttribute("aria-pressed", String(isActive));
        });

        renderTopics();
    });
});

/* Open a topic when its card is clicked. */
topicGrid.addEventListener("click", event => {
    const card = event.target.closest("[data-topic-id]");

    if (card) {
        openTopicDetails(card.dataset.topicId);
    }
});

/* Mobile sidebar controls, shared with the dashboard. */
const sidebar = document.getElementById("dashboardSidebar");
const mobileMenuButton = document.getElementById("mobileMenuButton");
const sidebarOverlay = document.getElementById("sidebarOverlay");

function closeSidebar() {
    if (sidebar) sidebar.classList.remove("sidebar-open");
    if (sidebarOverlay) sidebarOverlay.classList.remove("overlay-visible");

    if (mobileMenuButton) {
        mobileMenuButton.setAttribute("aria-expanded", "false");
    }
}

if (mobileMenuButton && sidebar && sidebarOverlay) {
    mobileMenuButton.addEventListener("click", () => {
        const isOpen = sidebar.classList.toggle("sidebar-open");

        sidebarOverlay.classList.toggle("overlay-visible", isOpen);
        mobileMenuButton.setAttribute("aria-expanded", String(isOpen));
    });

    sidebarOverlay.addEventListener("click", closeSidebar);
}

/* Set the footer year. */
const yearElement = document.getElementById("learningYear");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

/* Initial page render. */
updateTopicSummary();
renderTopics();
