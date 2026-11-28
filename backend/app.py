import os
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from generator import generate_subject_data

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "rootlearn-dev-secret-key")

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


def ensure_active_user(connection: sqlite3.Connection) -> int:
    """Return the logged-in user_id, or a default learner row for testing."""
    user_id = session.get("user_id")
    if user_id:
        row = connection.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()
        if row:
            return int(row["user_id"])

    guest = connection.execute(
        "SELECT user_id FROM users WHERE email = ?",
        ("learner@rootlearn.local",),
    ).fetchone()
    if guest:
        return int(guest["user_id"])

    with connection:
        connection.execute(
            """
            INSERT INTO users (full_name, email, password_hash, is_active)
            VALUES (?, ?, ?, 1)
            """,
            ("Learner", "learner@rootlearn.local", generate_password_hash("rootlearn123")),
        )
        return int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])


def render_page(filename: str):
    return send_from_directory(str(PAGES_DIR), filename)


# --------------------------------------------------
# PAGE ROUTES (All served from Flask on port 5000)
# --------------------------------------------------

@app.route("/")
@app.route("/index.html")
def home():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/dashboard")
@app.route("/dashboard.html")
@app.route("/pages/dashboard.html")
def dashboard_page():
    return render_page("dashboard.html")


@app.route("/diagnostic")
@app.route("/diagnostic-test")
@app.route("/diagnostic-test.html")
@app.route("/pages/diagnostic-test.html")
def diagnostic_page():
    return render_page("diagnostic-test.html")


@app.route("/prerequisite-map")
@app.route("/prerequisite-map.html")
@app.route("/pages/prerequisite-map.html")
def prerequisite_map_page():
    return render_page("prerequisite-map.html")


@app.route("/learning-resources")
@app.route("/learning-resources.html")
@app.route("/pages/learning-resources.html")
def learning_resources_page():
    return render_page("learning-resources.html")


@app.route("/learning-path")
@app.route("/learning-path.html")
@app.route("/pages/learning-path.html")
def learning_path_page():
    return render_page("learning-path.html")


@app.route("/retest")
@app.route("/retest.html")
@app.route("/pages/retest.html")
def retest_page():
    return render_page("retest.html")


@app.route("/login")
@app.route("/login.html")
@app.route("/pages/login.html")
def login_page():
    return render_page("login.html")


@app.route("/register")
@app.route("/register.html")
@app.route("/pages/register.html")
def register_page():
    return render_page("register.html")


# --------------------------------------------------
# FRONTEND CSS, JAVASCRIPT AND ASSETS
# --------------------------------------------------

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(str(FRONTEND_DIR / "css"), filename)


@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(str(FRONTEND_DIR / "js"), filename)


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(str(FRONTEND_DIR / "assets"), filename)


# --------------------------------------------------
# AUTH API
# --------------------------------------------------

@app.route("/api/auth/me")
def current_user():
    try:
        with get_db_connection() as connection:
            uid = session.get("user_id")
            if not uid:
                return jsonify({"status": "guest", "user": None})
            row = connection.execute(
                "SELECT user_id, full_name, email FROM users WHERE user_id = ? AND is_active = 1",
                (uid,),
            ).fetchone()
            if not row:
                session.pop("user_id", None)
                return jsonify({"status": "guest", "user": None})
            return jsonify({"status": "authenticated", "user": dict(row)})
    except sqlite3.Error:
        app.logger.exception("Auth check failed")
        return jsonify({"status": "error", "message": "Could not verify user session."}), 500


@app.route("/api/auth/register", methods=["POST"])
def register_user():
    payload = request.get_json(silent=True) or {}
    full_name = str(payload.get("full_name") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")

    if len(full_name) < 2:
        return jsonify({"status": "error", "message": "Full name must be at least 2 characters."}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"status": "error", "message": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters."}), 400

    try:
        with get_db_connection() as connection:
            existing = connection.execute(
                "SELECT user_id FROM users WHERE email = ?",
                (email,),
            ).fetchone()
            if existing:
                return jsonify({"status": "error", "message": "Email is already registered."}), 409

            with connection:
                connection.execute(
                    """
                    INSERT INTO users (full_name, email, password_hash, is_active)
                    VALUES (?, ?, ?, 1)
                    """,
                    (full_name, email, generate_password_hash(password)),
                )
                user_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])

            session["user_id"] = user_id

        return jsonify({
            "status": "success",
            "user": {"user_id": user_id, "full_name": full_name, "email": email},
        }), 201
    except sqlite3.Error:
        app.logger.exception("Registration failed")
        return jsonify({"status": "error", "message": "Could not register account."}), 500


@app.route("/api/auth/login", methods=["POST"])
def login_user():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")

    try:
        with get_db_connection() as connection:
            user = connection.execute(
                """
                SELECT user_id, full_name, email, password_hash, is_active
                FROM users
                WHERE email = ?
                """,
                (email,),
            ).fetchone()
            if (
                not user
                or not user["is_active"]
                or not check_password_hash(user["password_hash"], password)
            ):
                return jsonify({"status": "error", "message": "Invalid email or password."}), 401

            session["user_id"] = int(user["user_id"])

        return jsonify({
            "status": "success",
            "user": {
                "user_id": int(user["user_id"]),
                "full_name": user["full_name"],
                "email": user["email"],
            },
        })
    except sqlite3.Error:
        app.logger.exception("Login failed")
        return jsonify({"status": "error", "message": "Could not log in."}), 500


@app.route("/api/auth/logout", methods=["POST"])
def logout_user():
    session.pop("user_id", None)
    return jsonify({"status": "success"})


# --------------------------------------------------
# SUBJECTS & CURRICULUM SETUP API
# --------------------------------------------------

@app.route("/api/subjects")
def get_subjects():
    try:
        with get_db_connection() as connection:
            rows = connection.execute(
                """
                SELECT subject_id, subject_name, description
                FROM subjects
                ORDER BY subject_id
                """
            ).fetchall()
        return jsonify({"status": "success", "subjects": [dict(r) for r in rows]})
    except sqlite3.Error:
        app.logger.exception("Could not load subjects")
        return jsonify({"status": "error", "message": "Could not load subjects."}), 500


@app.route("/api/subjects/generate", methods=["POST"])
def create_subject_with_ai():
    payload = request.get_json(silent=True) or {}
    subject_name = str(payload.get("subject_name") or "").strip()
    subject_description = str(payload.get("subject_description") or "").strip()
    questions_per_topic = int(payload.get("questions_per_topic") or 2)
    questions_per_topic = max(2, min(3, questions_per_topic))

    if not subject_name:
        return jsonify({
            "status": "error",
            "message": "Please enter a subject name.",
        }), 400

    try:
        with get_db_connection() as connection:
            summary = generate_subject_data(
                conn=connection,
                subject_name=subject_name,
                subject_description=subject_description,
                questions_per_topic=questions_per_topic,
            )

        return jsonify({
            "status": "success",
            "message": f"Added {summary['subject_name']} with topics, prerequisites, diagnostic questions, and resources.",
            **summary,
        }), 201

    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except RuntimeError:
        app.logger.exception("Curriculum generation service error")
        return jsonify({
            "status": "error",
            "message": "The curriculum service is busy right now. Please try again in a moment.",
        }), 503
    except Exception:
        app.logger.exception("Subject generation failed")
        return jsonify({
            "status": "error",
            "message": "Could not create the subject right now. Please try again.",
        }), 500


# --------------------------------------------------
# HEALTH, TOPICS, PREREQUISITES & RESOURCES API
# --------------------------------------------------

@app.route("/api/health")
def health_check():
    try:
        with get_db_connection() as connection:
            topics_count = connection.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            questions_count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "topics_count": topics_count,
            "questions_count": questions_count,
        })
    except sqlite3.Error:
        app.logger.exception("Health check failed")
        return jsonify({"status": "error", "message": "Could not connect to the database."}), 500


@app.route("/api/topics")
def get_topics():
    subject_id = request.args.get("subject_id", type=int)
    try:
        with get_db_connection() as connection:
            if subject_id:
                topics = connection.execute(
                    """
                    SELECT topic_id, subject_id, topic_code, topic_name, description, difficulty_level, display_order
                    FROM topics
                    WHERE subject_id = ?
                    ORDER BY display_order, topic_id
                    """,
                    (subject_id,),
                ).fetchall()
            else:
                topics = connection.execute(
                    """
                    SELECT topic_id, subject_id, topic_code, topic_name, description, difficulty_level, display_order
                    FROM topics
                    ORDER BY display_order, topic_id
                    """
                ).fetchall()
        return jsonify({"status": "success", "topics": [dict(topic) for topic in topics]})
    except sqlite3.Error:
        app.logger.exception("Could not load topics")
        return jsonify({"status": "error", "message": "Could not load topics."}), 500


@app.route("/api/prerequisite-map")
def get_prerequisite_map():
    subject_id = request.args.get("subject_id", type=int)
    try:
        with get_db_connection() as connection:
            user_id = ensure_active_user(connection)
            if subject_id:
                topics = connection.execute(
                    """
                    SELECT topic_id, subject_id, topic_code, topic_name, description, difficulty_level, display_order
                    FROM topics
                    WHERE subject_id = ?
                    ORDER BY display_order, topic_id
                    """,
                    (subject_id,),
                ).fetchall()
            else:
                topics = connection.execute(
                    """
                    SELECT topic_id, subject_id, topic_code, topic_name, description, difficulty_level, display_order
                    FROM topics
                    ORDER BY display_order, topic_id
                    """
                ).fetchall()

            edges = connection.execute(
                """
                SELECT topic_id, prerequisite_topic_id
                FROM prerequisites
                """
            ).fetchall()
            perf_rows = connection.execute(
                """
                SELECT tp.topic_id, tp.score_percentage, tp.performance_status
                FROM topic_performance tp
                JOIN attempts a ON a.attempt_id = tp.attempt_id
                WHERE a.user_id = ? AND a.status = 'Completed'
                ORDER BY tp.performance_id ASC
                """,
                (user_id,),
            ).fetchall()

        prereq_map = {}
        for edge in edges:
            prereq_map.setdefault(edge["topic_id"], []).append(edge["prerequisite_topic_id"])

        latest_perf = {r["topic_id"]: dict(r) for r in perf_rows}
        nodes = []
        for t in topics:
            perf = latest_perf.get(t["topic_id"])
            nodes.append({
                "id": t["topic_id"],
                "subject_id": t["subject_id"],
                "code": t["topic_code"],
                "name": t["topic_name"],
                "description": t["description"] or "",
                "difficulty_level": t["difficulty_level"] or "Beginner",
                "prerequisites": prereq_map.get(t["topic_id"], []),
                "status": perf["performance_status"] if perf else "Not Assessed",
                "score": perf["score_percentage"] if perf else None,
            })

        return jsonify({"status": "success", "topics": nodes})
    except sqlite3.Error:
        app.logger.exception("Could not load prerequisite map")
        return jsonify({"status": "error", "message": "Could not load prerequisite map."}), 500


@app.route("/api/learning-resources")
def get_learning_resources():
    subject_id = request.args.get("subject_id", type=int)
    try:
        with get_db_connection() as connection:
            if subject_id:
                resources = connection.execute(
                    """
                    SELECT
                        lr.resource_id,
                        lr.topic_id,
                        t.subject_id,
                        t.topic_name,
                        lr.resource_title,
                        lr.resource_type,
                        lr.resource_url,
                        lr.resource_description
                    FROM learning_resources AS lr
                    JOIN topics AS t
                        ON t.topic_id = lr.topic_id
                    WHERE lr.is_active = 1 AND t.subject_id = ?
                    ORDER BY t.topic_id, lr.resource_id
                    """,
                    (subject_id,),
                ).fetchall()
            else:
                resources = connection.execute(
                    """
                    SELECT
                        lr.resource_id,
                        lr.topic_id,
                        t.subject_id,
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
                    """
                ).fetchall()
        return jsonify({
            "status": "success",
            "total_resources": len(resources),
            "resources": [dict(resource) for resource in resources],
        })
    except sqlite3.Error:
        app.logger.exception("Could not load learning resources")
        return jsonify({"status": "error", "message": "Could not load learning resources."}), 500


# --------------------------------------------------
# DIAGNOSTIC QUESTIONS & SUBMISSION (SAVES TO SQLITE)
# --------------------------------------------------

@app.route("/api/diagnostic/questions")
def get_diagnostic_questions():
    subject_id = request.args.get("subject_id", type=int)
    try:
        with get_db_connection() as connection:
            if subject_id:
                questions = connection.execute(
                    """
                    SELECT
                        q.question_id,
                        q.topic_id,
                        t.subject_id,
                        t.topic_name,
                        test.test_id,
                        test.test_name,
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
                      AND test.is_active = 1
                      AND q.is_active = 1
                      AND t.subject_id = ?
                    ORDER BY tq.test_id, tq.question_order
                    """,
                    (subject_id,),
                ).fetchall()
            else:
                questions = connection.execute(
                    """
                    SELECT
                        q.question_id,
                        q.topic_id,
                        t.subject_id,
                        t.topic_name,
                        test.test_id,
                        test.test_name,
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
                    WHERE test.test_type = 'Diagnostic' AND test.is_active = 1 AND q.is_active = 1
                    ORDER BY tq.test_id, tq.question_order
                    """
                ).fetchall()
        return jsonify({
            "status": "success",
            "total_questions": len(questions),
            "questions": [dict(question) for question in questions],
        })
    except sqlite3.Error:
        app.logger.exception("Could not load diagnostic questions")
        return jsonify({"status": "error", "message": "Could not load diagnostic questions."}), 500


@app.route("/api/diagnostic/submit", methods=["POST"])
def submit_diagnostic():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})
    subject_id = data.get("subject_id")

    if not isinstance(answers, dict):
        return jsonify({"status": "error", "message": "Invalid answers format."}), 400

    try:
        with get_db_connection() as connection:
            if subject_id:
                questions = connection.execute(
                    """
                    SELECT
                        q.question_id,
                        q.topic_id,
                        t.topic_name,
                        test.test_id,
                        q.correct_option
                    FROM test_questions AS tq
                    JOIN questions AS q
                        ON q.question_id = tq.question_id
                    JOIN topics AS t
                        ON t.topic_id = q.topic_id
                    JOIN tests AS test
                        ON test.test_id = tq.test_id
                    WHERE test.test_type = 'Diagnostic'
                      AND test.is_active = 1
                      AND q.is_active = 1
                      AND t.subject_id = ?
                    ORDER BY tq.test_id, tq.question_order
                    """,
                    (int(subject_id),),
                ).fetchall()
            else:
                questions = connection.execute(
                    """
                    SELECT
                        q.question_id,
                        q.topic_id,
                        t.topic_name,
                        test.test_id,
                        q.correct_option
                    FROM test_questions AS tq
                    JOIN questions AS q
                        ON q.question_id = tq.question_id
                    JOIN topics AS t
                        ON t.topic_id = q.topic_id
                    JOIN tests AS test
                        ON test.test_id = tq.test_id
                    WHERE test.test_type = 'Diagnostic' AND test.is_active = 1 AND q.is_active = 1
                    ORDER BY tq.test_id, tq.question_order
                    """
                ).fetchall()

            if not questions:
                return jsonify({"status": "error", "message": "No diagnostic questions found."}), 404

            test_id = int(questions[0]["test_id"])
            user_id = ensure_active_user(connection)
            prev_attempt = connection.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) FROM attempts WHERE user_id = ? AND test_id = ?",
                (user_id, test_id),
            ).fetchone()[0]

            score = 0
            topic_results = {}
            answered_count = 0
            evaluated_answers = []

            for question in questions:
                qid = int(question["question_id"])
                topic_id = int(question["topic_id"])
                topic_name = question["topic_name"]
                correct_option = str(question["correct_option"]).strip().upper()
                raw_sel = str(answers.get(str(qid), "")).strip().upper()
                selected_answer = raw_sel if raw_sel in ("A", "B", "C", "D") else None

                if selected_answer:
                    answered_count += 1

                if topic_id not in topic_results:
                    topic_results[topic_id] = {
                        "topic_id": topic_id,
                        "topic_name": topic_name,
                        "correct": 0,
                        "total": 0,
                    }

                topic_results[topic_id]["total"] += 1
                is_correct = 1 if (selected_answer and selected_answer == correct_option) else 0
                if is_correct:
                    score += 1
                    topic_results[topic_id]["correct"] += 1

                evaluated_answers.append((qid, selected_answer, is_correct))

            overall_pct = round((score / len(questions)) * 100, 1)

            with connection:
                connection.execute(
                    """
                    INSERT INTO attempts (
                        user_id, test_id, attempt_number, completed_at,
                        total_questions, correct_answers, score_percentage, status
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, 'Completed')
                    """,
                    (user_id, test_id, prev_attempt + 1, len(questions), score, overall_pct),
                )
                attempt_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])

                for qid, sel_opt, corr_flag in evaluated_answers:
                    connection.execute(
                        """
                        INSERT INTO attempt_answers (
                            attempt_id, question_id, selected_option, is_correct, answered_at
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (attempt_id, qid, sel_opt, corr_flag),
                    )

                connection.execute(
                    """
                    UPDATE learning_gaps
                    SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND status = 'Open'
                    """,
                    (user_id,),
                )

                results = []
                weak_topic_ids = set()

                for topic in topic_results.values():
                    total = topic["total"]
                    correct = topic["correct"]
                    pct = round((correct / total) * 100) if total else 0
                    perf_status = "Strong" if pct >= 75 else "Developing" if pct >= 50 else "Needs Attention"
                    if pct < 60:
                        weak_topic_ids.add(topic["topic_id"])

                    connection.execute(
                        """
                        INSERT INTO topic_performance (
                            attempt_id, topic_id, total_questions, correct_answers,
                            score_percentage, performance_status
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (attempt_id, topic["topic_id"], total, correct, pct, perf_status),
                    )

                    results.append({
                        **topic,
                        "incorrect": total - correct,
                        "percentage": pct,
                        "status": perf_status,
                    })

                prereq_rows = connection.execute(
                    "SELECT topic_id, prerequisite_topic_id FROM prerequisites"
                ).fetchall()
                prereq_map = {}
                for pr in prereq_rows:
                    prereq_map.setdefault(pr["topic_id"], []).append(pr["prerequisite_topic_id"])

                for w_tid in weak_topic_ids:
                    w_name = topic_results[w_tid]["topic_name"]
                    connection.execute(
                        """
                        INSERT INTO learning_gaps (
                            user_id, topic_id, attempt_id, gap_type, description, severity, status
                        ) VALUES (?, ?, ?, 'Direct', ?, 'High', 'Open')
                        """,
                        (
                            user_id,
                            w_tid,
                            attempt_id,
                            f"Scored {topic_results[w_tid]['correct']}/{topic_results[w_tid]['total']} on {w_name}.",
                        ),
                    )
                    for p_tid in prereq_map.get(w_tid, []):
                        if p_tid in topic_results:
                            p_pct = round(
                                (topic_results[p_tid]["correct"] / topic_results[p_tid]["total"]) * 100
                            )
                            if p_pct < 75:
                                p_name = topic_results[p_tid]["topic_name"]
                                connection.execute(
                                    """
                                    INSERT INTO learning_gaps (
                                        user_id, topic_id, attempt_id, gap_type, description, severity, status
                                    ) VALUES (?, ?, ?, 'Prerequisite', ?, 'Moderate', 'Open')
                                    """,
                                    (
                                        user_id,
                                        p_tid,
                                        attempt_id,
                                        f"Foundation '{p_name}' is holding back '{w_name}'.",
                                    ),
                                )

                connection.execute(
                    "INSERT INTO progress (user_id, attempt_id, overall_score, notes) VALUES (?, ?, ?, ?)",
                    (user_id, attempt_id, overall_pct, f"Diagnostic attempt #{prev_attempt + 1}"),
                )

        results.sort(key=lambda item: (item["percentage"], item["topic_name"]))

        return jsonify({
            "status": "success",
            "attempt_id": attempt_id,
            "total_questions": len(questions),
            "answered": answered_count,
            "correct": score,
            "incorrect": len(questions) - score,
            "percentage": round((score / len(questions)) * 100),
            "topic_results": results,
            "weakest_topics": results[:3],
        })

    except Exception:
        app.logger.exception("Diagnostic scoring failed")
        return jsonify({
            "status": "error",
            "message": "Unable to calculate and save diagnostic results.",
        }), 500


# --------------------------------------------------
# RETEST QUESTIONS & SUBMISSION (SAVES TO SQLITE)
# --------------------------------------------------

@app.route("/api/retest/questions")
def get_retest_questions():
    subject_id = request.args.get("subject_id", type=int)
    try:
        with get_db_connection() as connection:
            user_id = ensure_active_user(connection)
            if subject_id:
                gap_topics = connection.execute(
                    """
                    SELECT DISTINCT t.topic_id, t.topic_name
                    FROM learning_gaps lg
                    JOIN topics t ON t.topic_id = lg.topic_id
                    WHERE lg.user_id = ? AND lg.status = 'Open' AND t.subject_id = ?
                    """,
                    (user_id, subject_id),
                ).fetchall()
                test_row = connection.execute(
                    """
                    SELECT test_id, test_name
                    FROM tests
                    WHERE is_active = 1 AND subject_id = ?
                    ORDER BY test_id
                    LIMIT 1
                    """,
                    (subject_id,),
                ).fetchone() or connection.execute(
                    """
                    SELECT test_id, test_name
                    FROM tests
                    WHERE is_active = 1
                    ORDER BY test_id
                    LIMIT 1
                    """
                ).fetchone()
            else:
                gap_topics = connection.execute(
                    """
                    SELECT DISTINCT t.topic_id, t.topic_name
                    FROM learning_gaps lg
                    JOIN topics t ON t.topic_id = lg.topic_id
                    WHERE lg.user_id = ? AND lg.status = 'Open'
                    """,
                    (user_id,),
                ).fetchall()
                test_row = connection.execute(
                    """
                    SELECT test_id, test_name
                    FROM tests
                    WHERE is_active = 1
                    ORDER BY test_id
                    LIMIT 1
                    """
                ).fetchone()

            if not test_row:
                return jsonify({"status": "error", "message": "No active test found in tests table."}), 404

            focus_ids = [r["topic_id"] for r in gap_topics]
            focus_names = [r["topic_name"] for r in gap_topics]

            if focus_ids:
                placeholders = ",".join("?" for _ in focus_ids)
                questions = connection.execute(
                    f"""
                    SELECT DISTINCT
                        q.question_id,
                        q.topic_id,
                        t.topic_name,
                        ? AS test_id,
                        q.question_text,
                        q.option_a,
                        q.option_b,
                        q.option_c,
                        q.option_d
                    FROM questions q
                    JOIN topics t ON t.topic_id = q.topic_id
                    WHERE q.is_active = 1 AND q.topic_id IN ({placeholders})
                    ORDER BY t.display_order, q.question_id
                    """,
                    (test_row["test_id"], *focus_ids),
                ).fetchall()
            else:
                questions = connection.execute(
                    """
                    SELECT
                        q.question_id,
                        q.topic_id,
                        t.topic_name,
                        ? AS test_id,
                        q.question_text,
                        q.option_a,
                        q.option_b,
                        q.option_c,
                        q.option_d
                    FROM test_questions tq
                    JOIN questions q ON q.question_id = tq.question_id
                    JOIN topics t ON t.topic_id = q.topic_id
                    WHERE tq.test_id = ? AND q.is_active = 1
                    ORDER BY tq.question_order, q.question_id
                    """,
                    (test_row["test_id"], test_row["test_id"]),
                ).fetchall()

        return jsonify({
            "status": "success",
            "test_id": test_row["test_id"],
            "focus_topics": focus_names,
            "total_questions": len(questions),
            "questions": [dict(q) for q in questions],
        })
    except sqlite3.Error as exc:
        app.logger.exception("Could not load retest questions")
        return jsonify({"status": "error", "message": f"Database error: {exc}"}), 500


@app.route("/api/retest/submit", methods=["POST"])
def submit_retest():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})
    if not isinstance(answers, dict) or not answers:
        return jsonify({
            "status": "error",
            "message": "Please answer at least one question before submitting.",
        }), 400

    try:
        q_ids = [int(k) for k in answers.keys() if str(k).isdigit()]
        if not q_ids:
            return jsonify({"status": "error", "message": "Invalid question IDs."}), 400

        placeholders = ",".join("?" for _ in q_ids)
        with get_db_connection() as connection:
            user_id = ensure_active_user(connection)
            test_row = connection.execute(
                """
                SELECT test_id FROM tests
                WHERE is_active = 1
                ORDER BY test_id
                LIMIT 1
                """
            ).fetchone()
            test_id = int(test_row["test_id"]) if test_row else 1

            q_rows = connection.execute(
                f"""
                SELECT q.question_id, q.topic_id, t.topic_name, q.correct_option
                FROM questions q
                JOIN topics t ON t.topic_id = q.topic_id
                WHERE q.question_id IN ({placeholders}) AND q.is_active = 1
                """,
                q_ids,
            ).fetchall()

            if not q_rows:
                return jsonify({"status": "error", "message": "No matching questions found."}), 404

            prev_attempt = connection.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) FROM attempts WHERE user_id = ? AND test_id = ?",
                (user_id, test_id),
            ).fetchone()[0]

            score = 0
            topic_results = {}
            evaluated = []

            for row in q_rows:
                qid = int(row["question_id"])
                tid = int(row["topic_id"])
                tname = row["topic_name"]
                correct_opt = str(row["correct_option"]).strip().upper()
                raw_sel = str(answers.get(str(qid), "")).strip().upper()
                sel_opt = raw_sel if raw_sel in ("A", "B", "C", "D") else None

                if tid not in topic_results:
                    topic_results[tid] = {
                        "topic_id": tid,
                        "topic_name": tname,
                        "correct": 0,
                        "total": 0,
                    }
                topic_results[tid]["total"] += 1

                is_corr = 1 if (sel_opt and sel_opt == correct_opt) else 0
                if is_corr:
                    score += 1
                    topic_results[tid]["correct"] += 1
                evaluated.append((qid, sel_opt, is_corr))

            overall_pct = round((score / len(q_rows)) * 100, 1)
            resolved_gaps = 0

            with connection:
                connection.execute(
                    """
                    INSERT INTO attempts (
                        user_id, test_id, attempt_number, completed_at,
                        total_questions, correct_answers, score_percentage, status
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, 'Completed')
                    """,
                    (user_id, test_id, prev_attempt + 1, len(q_rows), score, overall_pct),
                )
                attempt_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])

                for qid, sel_opt, is_corr in evaluated:
                    connection.execute(
                        """
                        INSERT INTO attempt_answers (
                            attempt_id, question_id, selected_option, is_correct, answered_at
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (attempt_id, qid, sel_opt, is_corr),
                    )

                results = []
                for tid, tr in topic_results.items():
                    pct = round((tr["correct"] / tr["total"]) * 100) if tr["total"] else 0
                    status_label = (
                        "Strong" if pct >= 75 else "Developing" if pct >= 50 else "Needs Attention"
                    )
                    connection.execute(
                        """
                        INSERT INTO topic_performance (
                            attempt_id, topic_id, total_questions, correct_answers,
                            score_percentage, performance_status
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (attempt_id, tid, tr["total"], tr["correct"], pct, status_label),
                    )
                    if pct >= 60:
                        cur = connection.execute(
                            """
                            UPDATE learning_gaps
                            SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP
                            WHERE user_id = ? AND topic_id = ? AND status = 'Open'
                            """,
                            (user_id, tid),
                        )
                        resolved_gaps += cur.rowcount

                    results.append({
                        **tr,
                        "incorrect": tr["total"] - tr["correct"],
                        "percentage": pct,
                        "status": status_label,
                    })

                connection.execute(
                    "INSERT INTO progress (user_id, attempt_id, overall_score, notes) VALUES (?, ?, ?, ?)",
                    (user_id, attempt_id, overall_pct, f"Retest attempt #{prev_attempt + 1}"),
                )

            results.sort(key=lambda x: (x["percentage"], x["topic_name"]))

        return jsonify({
            "status": "success",
            "attempt_id": attempt_id,
            "total_questions": len(q_rows),
            "correct": score,
            "percentage": round(overall_pct),
            "resolved_gaps": resolved_gaps,
            "topic_results": results,
        })
    except Exception:
        app.logger.exception("Retest submission failed")
        return jsonify({"status": "error", "message": "Could not submit retest."}), 500


# --------------------------------------------------
# DASHBOARD SUMMARY API (Reads saved state from SQLite)
# --------------------------------------------------

@app.route("/api/dashboard/summary")
def get_dashboard_summary():
    subject_id = request.args.get("subject_id", type=int)
    try:
        with get_db_connection() as connection:
            user_id = ensure_active_user(connection)
            user_row = connection.execute(
                "SELECT full_name FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            tests_completed = connection.execute(
                "SELECT COUNT(*) FROM attempts WHERE user_id = ? AND status = 'Completed'",
                (user_id,),
            ).fetchone()[0]

            latest_attempt = connection.execute(
                """
                SELECT attempt_id, score_percentage
                FROM attempts
                WHERE user_id = ? AND status = 'Completed'
                ORDER BY attempt_id DESC LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            overall_progress = round(latest_attempt["score_percentage"]) if latest_attempt else 0

            if latest_attempt:
                if subject_id:
                    topics = [
                        dict(r)
                        for r in connection.execute(
                            """
                            SELECT t.topic_id, t.subject_id, t.topic_name,
                                   COALESCE(ROUND(tp.score_percentage), 0) AS progress,
                                   COALESCE(tp.performance_status, 'Not Assessed') AS status
                            FROM topics t
                            LEFT JOIN topic_performance tp
                              ON tp.topic_id = t.topic_id AND tp.attempt_id = ?
                            WHERE t.subject_id = ?
                            ORDER BY t.display_order, t.topic_id
                            """,
                            (latest_attempt["attempt_id"], subject_id),
                        ).fetchall()
                    ]
                else:
                    topics = [
                        dict(r)
                        for r in connection.execute(
                            """
                            SELECT t.topic_id, t.subject_id, t.topic_name,
                                   COALESCE(ROUND(tp.score_percentage), 0) AS progress,
                                   COALESCE(tp.performance_status, 'Not Assessed') AS status
                            FROM topics t
                            LEFT JOIN topic_performance tp
                              ON tp.topic_id = t.topic_id AND tp.attempt_id = ?
                            ORDER BY t.display_order, t.topic_id
                            """,
                            (latest_attempt["attempt_id"],),
                        ).fetchall()
                    ]
            else:
                if subject_id:
                    topics = [
                        {
                            "topic_id": r["topic_id"],
                            "subject_id": r["subject_id"],
                            "topic_name": r["topic_name"],
                            "progress": 0,
                            "status": "Not Assessed",
                        }
                        for r in connection.execute(
                            "SELECT topic_id, subject_id, topic_name FROM topics WHERE subject_id = ? ORDER BY display_order, topic_id",
                            (subject_id,),
                        ).fetchall()
                    ]
                else:
                    topics = [
                        {
                            "topic_id": r["topic_id"],
                            "subject_id": r["subject_id"],
                            "topic_name": r["topic_name"],
                            "progress": 0,
                            "status": "Not Assessed",
                        }
                        for r in connection.execute(
                            "SELECT topic_id, subject_id, topic_name FROM topics ORDER BY display_order, topic_id"
                        ).fetchall()
                    ]

            if subject_id:
                gaps = [
                    dict(g)
                    for g in connection.execute(
                        """
                        SELECT lg.gap_id, t.topic_name AS topic, lg.description AS reason, lg.gap_type
                        FROM learning_gaps lg
                        JOIN topics t ON t.topic_id = lg.topic_id
                        WHERE lg.user_id = ? AND lg.status = 'Open' AND t.subject_id = ?
                        ORDER BY CASE lg.gap_type WHEN 'Prerequisite' THEN 0 ELSE 1 END, lg.gap_id DESC
                        """,
                        (user_id, subject_id),
                    ).fetchall()
                ]
            else:
                gaps = [
                    dict(g)
                    for g in connection.execute(
                        """
                        SELECT lg.gap_id, t.topic_name AS topic, lg.description AS reason, lg.gap_type
                        FROM learning_gaps lg
                        JOIN topics t ON t.topic_id = lg.topic_id
                        WHERE lg.user_id = ? AND lg.status = 'Open'
                        ORDER BY CASE lg.gap_type WHEN 'Prerequisite' THEN 0 ELSE 1 END, lg.gap_id DESC
                        """,
                        (user_id,),
                    ).fetchall()
                ]

            activities = [
                {
                    "title": f"{a['test_name']} — {round(a['score_percentage'] or 0)}%",
                    "description": f"Attempt #{a['attempt_number']} saved to SQLite.",
                }
                for a in connection.execute(
                    """
                    SELECT a.attempt_number, a.score_percentage, t.test_name
                    FROM attempts a
                    JOIN tests t ON t.test_id = a.test_id
                    WHERE a.user_id = ? AND a.status = 'Completed'
                    ORDER BY a.attempt_id DESC LIMIT 5
                    """,
                    (user_id,),
                ).fetchall()
            ]

        return jsonify({
            "status": "success",
            "student": {
                "name": user_row["full_name"] if user_row else "Learner",
                "testsCompleted": tests_completed,
                "topicsStudied": len(topics),
                "overallProgress": overall_progress,
            },
            "topics": topics,
            "learningGaps": gaps,
            "activities": activities,
        })
    except sqlite3.Error:
        app.logger.exception("Dashboard summary failed")
        return jsonify({"status": "error", "message": "Could not load dashboard summary."}), 500


# --------------------------------------------------
# START ROOTLEARN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)