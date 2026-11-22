/* ==========================================
   ROOTLEARN — DASHBOARD FUNCTIONALITY
   Sample data for frontend development
========================================== */

"use strict";

/* ==========================================
   1. SAMPLE STUDENT DATA

   This is demonstration data.
   Later, the Flask backend will provide
   real data from the database.
========================================== */

const dashboardData = {
    student: {
        name: "Student",
        testsCompleted: 4,
        topicsStudied: 6,
        overallProgress: 68
    },

    topics: [
        {
            id: 1,
            name: "Variables",
            description: "Store and work with information",
            progress: 90,
            status: "Strong"
        },
        {
            id: 2,
            name: "Data Types",
            description: "Understand different kinds of data",
            progress: 78,
            status: "Good progress"
        },
        {
            id: 3,
            name: "Conditional Statements",
            description: "Make decisions using if and else",
            progress: 52,
            status: "Needs practice"
        },
        {
            id: 4,
            name: "Loops",
            description: "Repeat instructions efficiently",
            progress: 42,
            status: "Focus here"
        },
        {
            id: 5,
            name: "Functions",
            description: "Organize code into reusable blocks",
            progress: 35,
            status: "Needs practice"
        }
    ],

    learningGaps: [
        {
            topic: "Loops",
            reason: "Practice repeating instructions and understanding loop conditions.",
            level: "High priority"
        },
        {
            topic: "Functions",
            reason: "Review parameters, arguments, and return values.",
            level: "Needs attention"
        },
        {
            topic: "Conditional Statements",
            reason: "Strengthen your understanding of conditions and branching.",
            level: "Practice more"
        }
    ],

    activities: [
        {
            icon: "✓",
            title: "Diagnostic assessment",
            description: "Completed a sample Python assessment."
        },
        {
            icon: "▤",
            title: "Data Types",
            description: "Reviewed the fundamentals of Python data types."
        },
        {
            icon: "↗",
            title: "Learning progress updated",
            description: "Your sample progress overview is ready."
        }
    ]
};


/* ==========================================
   2. HELPER FUNCTIONS
========================================== */

function getElement(id) {
    return document.getElementById(id);
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, function (character) {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}

function showToast(message) {
    const toast = getElement("dashboardToast");

    if (!toast) {
        return;
    }

    toast.textContent = message;
    toast.classList.add("show");

    clearTimeout(showToast.timeout);

    showToast.timeout = setTimeout(function () {
        toast.classList.remove("show");
    }, 3500);
}


/* ==========================================
   3. UPDATE STUDENT OVERVIEW
========================================== */

function renderStudentOverview() {
    const student = dashboardData.student;

    getElement("testsCompleted").textContent =
        student.testsCompleted;

    getElement("topicsStudied").textContent =
        student.topicsStudied;

    getElement("overallProgress").textContent =
        student.overallProgress;

    getElement("gapsCount").textContent =
        dashboardData.learningGaps.length;

    const progressBar = getElement("overallProgressBar");

    if (progressBar) {
        progressBar.setAttribute(
            "aria-valuenow",
            student.overallProgress
        );

        const fill = progressBar.querySelector("span");

        if (fill) {
            fill.style.width = student.overallProgress + "%";
        }
    }

    const gapCount = document.querySelector(".sidebar-count");

    if (gapCount) {
        gapCount.textContent =
            dashboardData.learningGaps.length;
    }
}


/* ==========================================
   4. RENDER LEARNING PATH
========================================== */

function renderLearningPath() {
    const container = getElement("learningPathList");

    if (!container) {
        return;
    }

    container.innerHTML = dashboardData.topics.map(function (topic, index) {
        let statusClass = "";
        let statusText = topic.status;

        if (topic.progress >= 75) {
            statusClass = "status-strong";
        } else if (topic.progress < 55) {
            statusClass = "status-focus";
        }

        return `
            <article class="learning-topic">

                <div class="topic-number">
                    ${String(index + 1).padStart(2, "0")}
                </div>

                <div class="learning-topic-copy">
                    <h3>${escapeHTML(topic.name)}</h3>
                    <p>${escapeHTML(topic.description)}</p>
                </div>

                <span class="topic-status ${statusClass}">
                    ${escapeHTML(statusText)}
                </span>

            </article>
        `;
    }).join("");
}


/* ==========================================
   5. RENDER LEARNING GAPS
========================================== */

function renderLearningGaps() {
    const container = getElement("learningGapsList");

    if (!container) {
        return;
    }

    container.innerHTML = dashboardData.learningGaps.map(
        function (gap) {
            return `
                <article class="gap-item">

                    <div class="gap-marker" aria-hidden="true">
                        ↗
                    </div>

                    <div class="gap-item-copy">
                        <h3>${escapeHTML(gap.topic)}</h3>

                        <p>${escapeHTML(gap.reason)}</p>

                        <span class="gap-level">
                            ${escapeHTML(gap.level)}
                        </span>
                    </div>

                </article>
            `;
        }
    ).join("");
}


/* ==========================================
   6. RENDER TOPIC PROGRESS
========================================== */

function renderTopicProgress() {
    const container = getElement("topicProgressList");

    if (!container) {
        return;
    }

    container.innerHTML = dashboardData.topics.map(
        function (topic) {
            const needsPractice = topic.progress < 60;

            return `
                <div class="topic-progress-item">

                    <div class="topic-progress-heading">
                        <span>${escapeHTML(topic.name)}</span>
                        <span>${topic.progress}%</span>
                    </div>

                    <div
                        class="topic-progress-track"
                        role="progressbar"
                        aria-label="${escapeHTML(topic.name)} understanding"
                        aria-valuemin="0"
                        aria-valuemax="100"
                        aria-valuenow="${topic.progress}"
                    >
                        <div
                            class="topic-progress-fill ${
                                needsPractice ? "needs-practice" : ""
                            }"
                            style="width: ${topic.progress}%"
                        ></div>
                    </div>

                </div>
            `;
        }
    ).join("");
}


/* ==========================================
   7. RENDER RECENT ACTIVITY
========================================== */

function renderRecentActivity() {
    const container = getElement("recentActivityList");

    if (!container) {
        return;
    }

    container.innerHTML = dashboardData.activities.map(
        function (activity) {
            return `
                <article class="activity-item">

                    <div class="activity-icon" aria-hidden="true">
                        ${escapeHTML(activity.icon)}
                    </div>

                    <div class="activity-copy">
                        <h3>${escapeHTML(activity.title)}</h3>
                        <p>${escapeHTML(activity.description)}</p>
                    </div>

                </article>
            `;
        }
    ).join("");
}


/* ==========================================
   8. MOBILE SIDEBAR
========================================== */

function setupMobileNavigation() {
    const sidebar = getElement("dashboardSidebar");
    const menuButton = getElement("mobileMenuButton");

    if (!sidebar || !menuButton) {
        return;
    }

    function closeMenu() {
        sidebar.classList.remove("sidebar-open");

        menuButton.setAttribute(
            "aria-expanded",
            "false"
        );
    }

    menuButton.addEventListener("click", function () {
        const isOpen = sidebar.classList.toggle("sidebar-open");

        menuButton.setAttribute(
            "aria-expanded",
            String(isOpen)
        );
    });

    sidebar.querySelectorAll(".sidebar-link").forEach(
        function (link) {
            link.addEventListener("click", closeMenu);
        }
    );

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeMenu();
        }
    });

    document.addEventListener("click", function (event) {
        const clickedInsideSidebar = sidebar.contains(event.target);
        const clickedMenuButton = menuButton.contains(event.target);

        if (!clickedInsideSidebar && !clickedMenuButton) {
            closeMenu();
        }
    });
}


/* ==========================================
   9. SIDEBAR ACTIVE NAVIGATION
========================================== */

function setupActiveNavigation() {
    const links = document.querySelectorAll(".sidebar-link");

    links.forEach(function (link) {
        link.addEventListener("click", function () {
            links.forEach(function (item) {
                item.classList.remove("active");
            });

            link.classList.add("active");
        });
    });
}


/* ==========================================
   10. DIAGNOSTIC BUTTON — DEMO ONLY
========================================== */


function setupDiagnosticButton() {
    const button = getElement("startDiagnosticButton");

    if (!button) {
        return;
    }

    button.addEventListener("click", function () {
        window.location.href = "/diagnostic";
    });
}


/* ==========================================
   11. EXPLORE TOPICS BUTTON
========================================== */

function setupExploreTopicsButton() {
    const button = getElement("viewTopicsButton");

    if (!button) {
        return;
    }

    button.addEventListener("click", function (event) {
        event.preventDefault();

        showToast(
            "Topic exploration will be connected to the learning " +
            "module in the next stage."
        );
    });
}


/* ==========================================
   12. INITIALIZE DASHBOARD
========================================== */

function initializeDashboard() {
    const year = getElement("dashboardYear");

    if (year) {
        year.textContent = new Date().getFullYear();
    }

    renderStudentOverview();
    renderLearningPath();
    renderLearningGaps();
    renderTopicProgress();
    renderRecentActivity();

    setupMobileNavigation();
    setupActiveNavigation();
    setupDiagnosticButton();
    setupExploreTopicsButton();
}

document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);