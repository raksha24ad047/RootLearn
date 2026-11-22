
/* =========================================
   ROOTLEARN — PREREQUISITE MAP
   Interactive topic dependency graph
========================================= */

document.addEventListener("DOMContentLoaded", () => {
    const networkElement = document.getElementById("prerequisiteNetwork");
    const searchInput = document.getElementById("topicSearch");
    const showAllButton = document.getElementById("showAllBtn");
    const resetButton = document.getElementById("resetMapBtn");
    const topicCount = document.getElementById("topicCount");

    const detailPlaceholder = document.getElementById("detailPlaceholder");
    const detailContent = document.getElementById("detailContent");

    const topicLevel = document.getElementById("topicLevel");
    const selectedTopicName = document.getElementById("selectedTopicName");
    const selectedTopicDescription = document.getElementById("selectedTopicDescription");
    const prerequisiteList = document.getElementById("prerequisiteList");
    const dependentList = document.getElementById("dependentList");
    const viewResourcesButton = document.getElementById("viewResourcesBtn");

    /*
       Temporary topic data.
       These IDs match the topic IDs in rootlearn.db.
       We will fetch this data from Flask later.
    */

    const topics = [
        {
            id: 1,
            name: "Variables",
            level: "Beginner",
            description: "Learn how to store values in named variables and use them in your programs.",
            prerequisites: []
        },
        {
            id: 2,
            name: "Data Types",
            level: "Beginner",
            description: "Understand integers, floating-point numbers, strings, booleans, and other Python values.",
            prerequisites: [1]
        },
        {
            id: 3,
            name: "Operators",
            level: "Beginner",
            description: "Use arithmetic, comparison, and logical operators to work with values and expressions.",
            prerequisites: [1, 2]
        },
        {
            id: 4,
            name: "Conditional Statements",
            level: "Beginner",
            description: "Make decisions in your programs using if, elif, and else statements.",
            prerequisites: [3]
        },
        {
            id: 5,
            name: "Loops",
            level: "Beginner",
            description: "Repeat operations using for loops, while loops, and iteration.",
            prerequisites: [1, 3, 4]
        },
        {
            id: 6,
            name: "Functions",
            level: "Intermediate",
            description: "Organise reusable code into functions with parameters and return values.",
            prerequisites: [1, 2]
        },
        {
            id: 7,
            name: "Lists and Tuples",
            level: "Beginner",
            description: "Store ordered collections of values and learn indexing, slicing, and sequence operations.",
            prerequisites: [1, 2]
        },
        {
            id: 8,
            name: "Dictionaries and Sets",
            level: "Intermediate",
            description: "Organise data with key-value mappings and collections of unique elements.",
            prerequisites: [2, 7]
        },
        {
            id: 9,
            name: "Strings",
            level: "Beginner",
            description: "Work with text, string methods, indexing, slicing, and text manipulation.",
            prerequisites: [1]
        },
        {
            id: 10,
            name: "Object-Oriented Programming",
            level: "Intermediate",
            description: "Learn classes, objects, attributes, methods, and the foundations of inheritance.",
            prerequisites: [1, 2, 6]
        }
    ];

    /*
       Create the graph nodes and edges.
       An arrow points FROM a prerequisite TO the topic
       that depends on it.
    */

    const nodes = new vis.DataSet(
        topics.map(topic => ({
            id: topic.id,
            label: topic.name,
            title: `${topic.name} — ${topic.level}`,
            shape: "box",
            margin: 13,
            borderWidth: 1,
            borderWidthSelected: 3,
            color: {
                background: topic.level === "Beginner" ? "#F7E8DF" : "#EBD7D3",
                border: topic.level === "Beginner" ? "#C76D52" : "#633B52",
                highlight: {
                    background: "#633B52",
                    border: "#633B52"
                },
                hover: {
                    background: "#F1D3C5",
                    border: "#C76D52"
                }
            },
            font: {
                color: "#28242B",
                size: 15,
                face: "Arial",
                bold: true
            },
            shapeProperties: {
                borderRadius: 10
            }
        }))
    );

    const edges = new vis.DataSet(
        topics.flatMap(topic =>
            topic.prerequisites.map(prerequisiteId => ({
                from: prerequisiteId,
                to: topic.id,
                arrows: {
                    to: {
                        enabled: true,
                        scaleFactor: 0.7
                    }
                },
                color: {
                    color: "#C8B7BC",
                    highlight: "#C76D52",
                    hover: "#C76D52"
                },
                width: 1.5,
                smooth: {
                    enabled: true,
                    type: "cubicBezier",
                    roundness: 0.25
                }
            }))
        )
    );

    const data = {
        nodes,
        edges
    };

    const options = {
        autoResize: true,
        interaction: {
            hover: true,
            tooltipDelay: 150,
            navigationButtons: true,
            keyboard: {
                enabled: true
            }
        },
        physics: {
            enabled: true,
            stabilization: {
                iterations: 180,
                fit: true
            },
            barnesHut: {
                gravitationalConstant: -4500,
                centralGravity: 0.25,
                springLength: 155,
                springConstant: 0.035,
                damping: 0.15
            }
        },
        nodes: {
            chosen: true
        },
        edges: {
            selectionWidth: 2,
            hoverWidth: 2
        },
        layout: {
            improvedLayout: true
        }
    };

    /*
       Create the interactive network.
    */

    if (typeof vis === "undefined") {
        networkElement.innerHTML =
            "<p style='padding:24px;color:#633B52;'>The map library could not load. Please check your internet connection and reload the page.</p>";
        return;
    }

    const network = new vis.Network(networkElement, data, options);

    /*
       Helper functions.
    */

    function getTopic(topicId) {
        return topics.find(topic => topic.id === topicId);
    }

    function createTopicChip(topicName) {
        const chip = document.createElement("span");
        chip.className = "topic-chip";
        chip.textContent = topicName;
        return chip;
    }

    function displayTopicList(container, topicIds, emptyMessage) {
        container.replaceChildren();

        if (topicIds.length === 0) {
            const message = document.createElement("p");
            message.className = "empty-chip-message";
            message.textContent = emptyMessage;
            container.appendChild(message);
            return;
        }

        topicIds.forEach(id => {
            const topic = getTopic(id);

            if (topic) {
                container.appendChild(createTopicChip(topic.name));
            }
        });
    }

    /*
       Display the selected topic and its relationships.
    */

    function showTopicDetails(topicId) {
        const topic = getTopic(topicId);

        if (!topic) return;

        detailPlaceholder.hidden = true;
        detailContent.hidden = false;

        topicLevel.textContent = topic.level;
        selectedTopicName.textContent = topic.name;
        selectedTopicDescription.textContent = topic.description;

        const dependentTopics = topics
            .filter(item => item.prerequisites.includes(topic.id))
            .map(item => item.id);

        displayTopicList(
            prerequisiteList,
            topic.prerequisites,
            "No prerequisites — this is a starting topic."
        );

        displayTopicList(
            dependentList,
            dependentTopics,
            "No other topic currently depends directly on this topic."
        );

        viewResourcesButton.onclick = () => {
            window.location.href =
                `learning-resources.html?topic=${encodeURIComponent(topic.name)}`;
        };
    }

    /*
       Highlight the selected topic and its direct connections.
    */

    network.on("selectNode", event => {
        if (event.nodes.length > 0) {
            const selectedId = event.nodes[0];

            showTopicDetails(selectedId);

            const connectedNodeIds = network.getConnectedNodes(selectedId);

            const visibleNodes = new Set([
                selectedId,
                ...connectedNodeIds
            ]);

            nodes.update(
                nodes.get().map(node => ({
                    id: node.id,
                    color: {
                        background: visibleNodes.has(node.id)
                            ? (node.id === selectedId ? "#633B52" : "#F7E8DF")
                            : "#F0ECE8",
                        border: visibleNodes.has(node.id)
                            ? (node.id === selectedId ? "#633B52" : "#C76D52")
                            : "#DDD5D0"
                    },
                    font: {
                        color: node.id === selectedId ? "#FFFFFF" : "#28242B"
                    }
                }))
            );

            edges.update(
                edges.get().map(edge => ({
                    id: edge.id,
                    color: {
                        color:
                            edge.from === selectedId || edge.to === selectedId
                                ? "#C76D52"
                                : "#DDD5D0"
                    },
                    width:
                        edge.from === selectedId || edge.to === selectedId
                            ? 2.5
                            : 1
                }))
            );
        }
    });

    /*
       Restore the original colours.
    */

    function restoreDefaultColors() {
        nodes.update(
            topics.map(topic => ({
                id: topic.id,
                color: {
                    background: topic.level === "Beginner" ? "#F7E8DF" : "#EBD7D3",
                    border: topic.level === "Beginner" ? "#C76D52" : "#633B52",
                    highlight: {
                        background: "#633B52",
                        border: "#633B52"
                    },
                    hover: {
                        background: "#F1D3C5",
                        border: "#C76D52"
                    }
                },
                font: {
                    color: "#28242B",
                    size: 15,
                    face: "Arial",
                    bold: true
                }
            }))
        );

        edges.update(
            edges.get().map(edge => ({
                id: edge.id,
                color: {
                    color: "#C8B7BC",
                    highlight: "#C76D52",
                    hover: "#C76D52"
                },
                width: 1.5
            }))
        );
    }

    /*
       Search topics by name.
    */

    searchInput.addEventListener("input", () => {
        const searchTerm = searchInput.value.trim().toLowerCase();

        if (!searchTerm) {
            nodes.update(
                topics.map(topic => ({
                    id: topic.id,
                    hidden: false
                }))
            );

            topicCount.textContent = `${topics.length} topics`;
            return;
        }

        const matches = topics.filter(topic =>
            topic.name.toLowerCase().includes(searchTerm)
        );

        const matchingIds = new Set(matches.map(topic => topic.id));

        nodes.update(
            topics.map(topic => ({
                id: topic.id,
                hidden: !matchingIds.has(topic.id)
            }))
        );

        topicCount.textContent =
            `${matches.length} ${matches.length === 1 ? "topic" : "topics"} found`;

        if (matches.length === 1) {
            network.selectNodes([matches[0].id]);
            network.focus(matches[0].id, {
                scale: 1,
                animation: true
            });
        }
    });

    /*
       Show all topics.
    */

    showAllButton.addEventListener("click", () => {
        searchInput.value = "";

        nodes.update(
            topics.map(topic => ({
                id: topic.id,
                hidden: false
            }))
        );

        restoreDefaultColors();

        topicCount.textContent = `${topics.length} topics`;

        network.unselectAll();
        network.fit({ animation: true });

        detailContent.hidden = true;
        detailPlaceholder.hidden = false;
    });

    /*
       Reset the map.
    */

    resetButton.addEventListener("click", () => {
        searchInput.value = "";

        nodes.update(
            topics.map(topic => ({
                id: topic.id,
                hidden: false
            }))
        );

        restoreDefaultColors();

        topicCount.textContent = `${topics.length} topics`;

        network.unselectAll();
        network.fit({ animation: true });

        detailContent.hidden = true;
        detailPlaceholder.hidden = false;
    });

    /*
       Initial display.
    */

    topicCount.textContent = `${topics.length} topics`;
    network.fit({ animation: true });
});
