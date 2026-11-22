
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

# --------------------------------------------------
# ROOTLEARN PATHS AND DATABASE CONNECTION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "rootlearn.db"
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# --------------------------------------------------
# PAGE ROUTES
# All pages will use the same Flask server: port 5000
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to RootLearn!",
        "status": "Backend is running"
    })


@app.route("/dashboard")
def dashboard_page():
    return send_from_directory(
        str(PAGES_DIR),
        "dashboard.html"
    )


@app.route("/diagnostic")
def diagnostic_page():
    return send_from_directory(
        str(PAGES_DIR),
        "diagnostic-test.html"
    )


@app.route("/prerequisite-map")
def prerequisite_map_page():
    return send_from_directory(
        str(PAGES_DIR),
        "prerequisite-map.html"
    )


@app.route("/learning-resources")
@app.route("/learning-resources.html")
def learning_resources_page():
    return send_from_directory(
        str(PAGES_DIR),
        "learning-resources.html"
    )


# --------------------------------------------------
# FRONTEND CSS, JAVASCRIPT AND ASSETS
# --------------------------------------------------

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(
        str(FRONTEND_DIR / "css"),
        filename
    )


@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(
        str(FRONTEND_DIR / "js"),
        filename
    )


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(
        str(FRONTEND_DIR / "assets"),
        filename
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/api/health")
def health_check():
    try:
        with get_db_connection() as connection:
            topics_count = connection.execute(
                "SELECT COUNT(*) FROM topics"
            ).fetchone()[0]

            questions_count = connection.execute(
                "SELECT COUNT(*) FROM questions"
            ).fetchone()[0]

        return jsonify({
            "status": "healthy",
            "database": "connected",
            "topics_count": topics_count,
            "questions_count": questions_count
        })

    except sqlite3.Error:
        app.logger.exception("Health check failed")
        return jsonify({
            "status": "error",
            "message": "Could not connect to the database."
        }), 500


# --------------------------------------------------
# TOPICS API
# Used by the learning resources page
# --------------------------------------------------

@app.route("/api/topics")
def get_topics():
    try:
        with get_db_connection() as connection:
            topics = connection.execute("""
                SELECT topic_id, topic_name
                FROM topics
                ORDER BY topic_id
            """).fetchall()

        return jsonify({
            "status": "success",
            "topics": [dict(topic) for topic in topics]
        })

    except sqlite3.Error:
        app.logger.exception("Could not load topics")
        return jsonify({
            "status": "error",
            "message": "Could not load topics."
        }), 500


# --------------------------------------------------
# LEARNING RESOURCES API
# Reads resources directly from SQLite
# --------------------------------------------------

@app.route("/api/learning-resources")
def get_learning_resources():
    try:
        with get_db_connection() as connection:
            resources = connection.execute("""
                SELECT
                    lr.resource_id,
                    lr.topic_id,
                    t.topic_name,
                    lr.resource_title,
                    lr.resource_type,
                    lr.resource_url,
                    lr.resource_description
                FROM learning_resources AS lr
                JOIN topics AS t
                    ON t.topic_id = lr.topic_id
                WHERE lr.is_active = 1
                ORDER BY t.topic_id, lr.resource_id
            """).fetchall()

        return jsonify({
            "status": "success",
            "total_resources": len(resources),
            "resources": [
                dict(resource) for resource in resources
            ]
        })

    except sqlite3.Error:
        app.logger.exception("Could not load learning resources")
        return jsonify({
            "status": "error",
            "message": "Could not load learning resources."
        }), 500


# --------------------------------------------------
# DIAGNOSTIC QUESTIONS API
# Correct answers are NOT sent to the browser
# --------------------------------------------------

@app.route("/api/diagnostic/questions")
def get_diagnostic_questions():
    try:
        with get_db_connection() as connection:
            questions = connection.execute("""
                SELECT
                    q.question_id,
                    q.topic_id,
                    t.topic_name,
                    q.question_text,
                    q.option_a,
                    q.option_b,
                    q.option_c,
                    q.option_d
                FROM test_questions AS tq
                JOIN questions AS q
                    ON q.question_id = tq.question_id
                JOIN topics AS t
                    ON t.topic_id = q.topic_id
                JOIN tests AS test
                    ON test.test_id = tq.test_id
                WHERE test.test_type = 'Diagnostic'
                ORDER BY tq.test_id, tq.question_order
            """).fetchall()

        return jsonify({
            "status": "success",
            "total_questions": len(questions),
            "questions": [
                dict(question) for question in questions
            ]
        })

    except sqlite3.Error:
        app.logger.exception("Could not load diagnostic questions")
        return jsonify({
            "status": "error",
            "message": "Could not load diagnostic questions."
        }), 500


# --------------------------------------------------
# DIAGNOSTIC SUBMISSION AND SCORING API
# Existing scoring behavior preserved
# --------------------------------------------------

@app.route("/api/diagnostic/submit", methods=["POST"])
def submit_diagnostic():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})

    if not isinstance(answers, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid answers format."
        }), 400

    try:
        with get_db_connection() as connection:
            questions = connection.execute("""
                SELECT
                    q.question_id,
                    q.topic_id,
                    t.topic_name,
                    q.correct_option
                FROM test_questions AS tq
                JOIN questions AS q
                    ON q.question_id = tq.question_id
                JOIN topics AS t
                    ON t.topic_id = q.topic_id
                JOIN tests AS test
                    ON test.test_id = tq.test_id
                WHERE test.test_type = 'Diagnostic'
                ORDER BY tq.test_id, tq.question_order
            """).fetchall()

        if not questions:
            return jsonify({
                "status": "error",
                "message": "No diagnostic questions found."
            }), 404

        score = 0
        topic_results = {}
        answered_count = 0

        for question in questions:
            question_id = str(question["question_id"])
            topic_id = question["topic_id"]
            topic_name = question["topic_name"]

            correct_option = str(
                question["correct_option"]
            ).strip().upper()

            selected_answer = str(
                answers.get(question_id, "")
            ).strip().upper()

            if selected_answer:
                answered_count += 1

            if topic_id not in topic_results:
                topic_results[topic_id] = {
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "correct": 0,
                    "total": 0
                }

            topic_results[topic_id]["total"] += 1

            if (
                selected_answer
                and selected_answer == correct_option
            ):
                score += 1
                topic_results[topic_id]["correct"] += 1

        results = []

        for topic in topic_results.values():
            total = topic["total"]
            correct = topic["correct"]

            results.append({
                **topic,
                "incorrect": total - correct,
                "percentage": round(
                    (correct / total) * 100
                ) if total else 0
            })

        results.sort(key=lambda item: (
            item["percentage"],
            item["topic_name"]
        ))

        return jsonify({
            "status": "success",
            "total_questions": len(questions),
            "answered": answered_count,
            "correct": score,
            "incorrect": len(questions) - score,
            "percentage": round(
                (score / len(questions)) * 100
            ),
            "topic_results": results,
            "weakest_topics": results[:3]
        })

    except Exception:
        app.logger.exception("Diagnostic scoring failed")
        return jsonify({
            "status": "error",
            "message": "Unable to calculate diagnostic results."
        }), 500


# --------------------------------------------------
# START ROOTLEARN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
