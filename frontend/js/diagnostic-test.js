
const API_BASE = "/api";

let questions = [];
let currentQuestionIndex = 0;
const selectedAnswers = {};

const intro = document.getElementById("testIntro");
const testArea = document.getElementById("testArea");
const confirmation = document.getElementById("submitConfirmation");
const results = document.getElementById("testResults");

const startButton = document.getElementById("startTestBtn");
const previousButton = document.getElementById("previousQuestionBtn");
const nextButton = document.getElementById("nextQuestionBtn");
const submitButton = document.getElementById("submitTestBtn");
const reviewButton = document.getElementById("reviewAnswersBtn");
const confirmSubmitButton = document.getElementById("confirmSubmitBtn");

const questionNumber = document.getElementById("questionNumber");
const questionTopic = document.getElementById("questionTopic");
const questionText = document.getElementById("questionText");
const answerOptions = document.getElementById("answerOptions");
const questionError = document.getElementById("questionError");
const answeredCounter = document.getElementById("answeredCounter");
const testProgress = document.getElementById("testProgress");
const testStatus = document.getElementById("testStatus");

async function loadQuestions() {
    startButton.disabled = true;
    startButton.textContent = "Loading questions...";

    try {
        const response = await fetch(`${API_BASE}/diagnostic/questions`);

        if (!response.ok) {
            throw new Error("The server could not load the questions.");
        }

        const data = await response.json();

        if (
            data.status !== "success" ||
            !Array.isArray(data.questions) ||
            data.questions.length === 0
        ) {
            throw new Error("No diagnostic questions were found.");
        }

        questions = data.questions;

        startButton.textContent = "Start diagnostic test";
        startButton.disabled = false;

        const count = document.getElementById("testQuestionCount");

        if (count) {
            count.textContent = questions.length;
        }

        testStatus.textContent = `${questions.length} questions are ready.`;

    } catch (error) {
        console.error("Question loading failed:", error);

        startButton.disabled = false;
        startButton.textContent = "Try loading questions again";
        testStatus.textContent =
            "Couldn't load questions. Please check the server and try again.";
    }
}

function startTest() {
    if (!questions.length) {
        loadQuestions();
        return;
    }

    currentQuestionIndex = 0;

    intro.hidden = true;
    testArea.hidden = false;
    confirmation.hidden = true;
    results.hidden = true;

    renderQuestion();
}

function renderQuestion() {
    const question = questions[currentQuestionIndex];

    if (!question) return;

    questionNumber.textContent =
        `Question ${currentQuestionIndex + 1} of ${questions.length}`;

    questionTopic.textContent = question.topic_name;
    questionText.textContent = question.question_text;
    questionError.hidden = true;

    answerOptions.replaceChildren();

    const options = [
        ["A", question.option_a],
        ["B", question.option_b],
        ["C", question.option_c],
        ["D", question.option_d]
    ];

    options.forEach(([letter, optionText]) => {
        const label = document.createElement("label");
        label.className = "answer-option";

        const input = document.createElement("input");
        input.type = "radio";
        input.name = "questionAnswer";
        input.value = letter;

        input.checked =
            selectedAnswers[String(question.question_id)] === letter;

        const text = document.createElement("span");
        text.textContent = `${letter}. ${optionText}`;

        if (input.checked) {
            label.classList.add("selected");
        }

        input.addEventListener("change", () => {
            selectedAnswers[String(question.question_id)] = letter;

            answerOptions
                .querySelectorAll(".answer-option")
                .forEach(option => option.classList.remove("selected"));

            label.classList.add("selected");
            questionError.hidden = true;

            updateProgress();
        });

        label.append(input, text);
        answerOptions.appendChild(label);
    });

    previousButton.disabled = currentQuestionIndex === 0;

    nextButton.hidden =
        currentQuestionIndex === questions.length - 1;

    submitButton.hidden =
        currentQuestionIndex !== questions.length - 1;

    updateProgress();
}

function updateProgress() {
    const answered = questions.filter(
        question => selectedAnswers[String(question.question_id)]
    ).length;

    const percentage = questions.length
        ? (answered / questions.length) * 100
        : 0;

    answeredCounter.textContent =
        `${answered} of ${questions.length} answered`;

    testProgress.style.width = `${percentage}%`;
}

function goToPreviousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        renderQuestion();
    }
}

function goToNextQuestion() {
    const question = questions[currentQuestionIndex];

    if (!selectedAnswers[String(question.question_id)]) {
        questionError.textContent =
            "Please select an answer before continuing.";
        questionError.hidden = false;
        return;
    }

    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        renderQuestion();
    }
}

function showSubmissionConfirmation() {
    const unanswered = questions.filter(
        question => !selectedAnswers[String(question.question_id)]
    );

    if (unanswered.length > 0) {
        questionError.textContent =
            `You still have ${unanswered.length} unanswered question(s).`;
        questionError.hidden = false;
        return;
    }

    testArea.hidden = true;
    confirmation.hidden = false;
}

function reviewAnswers() {
    confirmation.hidden = true;
    testArea.hidden = false;

    currentQuestionIndex = 0;
    renderQuestion();
}

function displayResults(data) {
    confirmation.hidden = true;
    intro.hidden = true;
    testArea.hidden = true;
    results.hidden = false;

    document.getElementById("overallScore").textContent =
        `${data.correct}/${data.total_questions}`;

    document.getElementById("overallFeedback").textContent =
        data.percentage >= 80
            ? "Excellent work! You have a strong foundation in these topics."
            : data.percentage >= 50
                ? "Good start! A little focused practice can strengthen your foundation."
                : "This is your starting point. Let's identify the concepts to practise next.";

    document.getElementById("correctCount").textContent = data.correct;
    document.getElementById("incorrectCount").textContent = data.incorrect;

    const topicList = document.getElementById("topicResultsList");
    topicList.replaceChildren();

    data.topic_results.forEach((topic, index) => {
        const card = document.createElement("article");
        card.className = "topic-result-card";

        const heading = document.createElement("div");
        heading.className = "topic-result-heading";

        const name = document.createElement("h3");
        name.textContent = topic.topic_name;

        const percentage = document.createElement("strong");
        percentage.textContent = `${topic.percentage}%`;

        heading.append(name, percentage);

        const track = document.createElement("div");
        track.className = "topic-result-track";

        const fill = document.createElement("div");
        fill.className = "topic-result-fill";
        fill.style.width = `${topic.percentage}%`;

        track.appendChild(fill);

        const detail = document.createElement("p");
        detail.textContent =
            `${topic.correct} of ${topic.total} correct`;

        card.append(heading, track, detail);

        if (index < 3) {
            const tag = document.createElement("span");
            tag.className = "topic-result-tag";
            tag.textContent = index === 0
                ? "Needs most attention"
                : index === 1
                    ? "Practise next"
                    : "Review recommended";

            card.appendChild(tag);
        }

        topicList.appendChild(card);
    });

    testStatus.textContent =
        "Your diagnostic results have been calculated.";

    // Pass the weakest topic to the learning resources page.
    const weakestTopic = data.weakest_topics?.[0];

    const mapButton = document.getElementById("openMapBtn");
    const resourcesButton = document.getElementById("openResourcesBtn");

    if (mapButton) {
        mapButton.onclick = () => {
            window.location.href = "prerequisite-map";
        };
    }

    if (resourcesButton) {
        resourcesButton.onclick = () => {
            const target = weakestTopic
               ? `/learning-resources?topic=${encodeURIComponent(weakestTopic.topic_id)}`
: "/learning-resources";

            window.location.href = target;
        };
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function submitDiagnostic() {
    confirmSubmitButton.disabled = true;
    confirmSubmitButton.textContent = "Calculating results...";

    try {
        const response = await fetch(`${API_BASE}/diagnostic/submit`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                answers: selectedAnswers
            })
        });

        const data = await response.json();

        if (!response.ok || data.status !== "success") {
            throw new Error(
                data.message || "Could not calculate your results."
            );
        }

        displayResults(data);

    } catch (error) {
        console.error("Diagnostic submission failed:", error);

        testStatus.textContent =
            error.message || "Something went wrong while submitting.";

        confirmation.hidden = false;

    } finally {
        confirmSubmitButton.disabled = false;
        confirmSubmitButton.textContent = "View my results";
    }
}

startButton.addEventListener("click", startTest);
previousButton.addEventListener("click", goToPreviousQuestion);
nextButton.addEventListener("click", goToNextQuestion);
submitButton.addEventListener("click", showSubmissionConfirmation);
reviewButton.addEventListener("click", reviewAnswers);
confirmSubmitButton.addEventListener("click", submitDiagnostic);




loadQuestions();
