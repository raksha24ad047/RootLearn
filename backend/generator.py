import json
import os
import sqlite3
import time
from google import genai
from google.genai import types


CURRICULUM_JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "subject_summary": {"type": "STRING"},
        "topics": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "code": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "difficulty_level": {
                        "type": "STRING",
                        "enum": ["Beginner", "Intermediate", "Advanced"],
                    },
                    "prerequisite_codes": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                    "questions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "question_text": {"type": "STRING"},
                                "option_a": {"type": "STRING"},
                                "option_b": {"type": "STRING"},
                                "option_c": {"type": "STRING"},
                                "option_d": {"type": "STRING"},
                                "correct_option": {
                                    "type": "STRING",
                                    "enum": ["A", "B", "C", "D"],
                                },
                                "explanation": {"type": "STRING"},
                                "difficulty_level": {
                                    "type": "STRING",
                                    "enum": ["Beginner", "Intermediate", "Advanced"],
                                },
                            },
                            "required": [
                                "question_text",
                                "option_a",
                                "option_b",
                                "option_c",
                                "option_d",
                                "correct_option",
                                "explanation",
                                "difficulty_level",
                            ],
                        },
                    },
                    "resources": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "resource_title": {"type": "STRING"},
                                "resource_type": {
                                    "type": "STRING",
                                    "enum": ["Notes", "Video", "Practice", "Article", "Other"],
                                },
                                "resource_url": {"type": "STRING"},
                                "resource_description": {"type": "STRING"},
                            },
                            "required": [
                                "resource_title",
                                "resource_type",
                                "resource_url",
                                "resource_description",
                            ],
                        },
                    },
                },
                "required": [
                    "code",
                    "name",
                    "description",
                    "difficulty_level",
                    "prerequisite_codes",
                    "questions",
                    "resources",
                ],
            },
        },
    },
    "required": ["subject_summary", "topics"],
}


def _build_local_fallback_curriculum(
    subject_name: str, subject_description: str, questions_per_topic: int
) -> dict:
    """Used only when Gemini endpoints are temporarily unreachable/overloaded."""
    focus = subject_description.strip() or "core principles and problem solving"
    stage_specs = [
        ("T1", f"{subject_name} Foundations", "Beginner", [], f"Core terminology, syntax/basics, and mental models for {subject_name} ({focus})."),
        ("T2", f"{subject_name} Core Mechanics", "Beginner", ["T1"], f"Essential operations, rules, and building blocks in {subject_name}."),
        ("T3", f"{subject_name} Control & Flow", "Intermediate", ["T1", "T2"], f"Structuring logic, decision paths, and state transitions in {subject_name}."),
        ("T4", f"{subject_name} Applied Problem Solving", "Intermediate", ["T2", "T3"], f"Combining {subject_name} concepts to solve realistic multi-step problems."),
        ("T5", f"{subject_name} Debugging & Best Practices", "Advanced", ["T3", "T4"], f"Identifying common mistakes, edge cases, and clean patterns in {subject_name}."),
    ]

    topics_out = []
    for code, name, diff, prereqs, desc in stage_specs:
        q_list = []
        for q_idx in range(1, questions_per_topic + 1):
            q_list.append({
                "question_text": f"[{name}] Question {q_idx}: Which approach best supports mastery of {name.lower()}?",
                "option_a": f"Practice {name.lower()} step by step and verify with small examples",
                "option_b": "Skip fundamentals and guess answers without checking edge cases",
                "option_c": "Memorize unrelated terms without understanding how they connect",
                "option_d": "Ignore errors and avoid reviewing prerequisite concepts",
                "correct_option": "A",
                "explanation": f"Building {name.lower()} through structured practice and checking examples strengthens root understanding.",
                "difficulty_level": diff,
            })

        search_q = "+".join(f"{subject_name} {name}".split())
        res_list = [
            {
                "resource_title": f"{name} — Study Guide & Overview",
                "resource_type": "Notes",
                "resource_url": f"https://www.google.com/search?q={search_q}+notes+guide",
                "resource_description": f"Structured study notes covering {name.lower()}.",
            },
            {
                "resource_title": f"{name} — Video Walkthroughs",
                "resource_type": "Video",
                "resource_url": f"https://www.youtube.com/results?search_query={search_q}",
                "resource_description": f"Visual explanations and examples for {name.lower()}.",
            },
        ]

        topics_out.append({
            "code": code,
            "name": name,
            "description": desc,
            "difficulty_level": diff,
            "prerequisite_codes": prereqs,
            "questions": q_list,
            "resources": res_list,
        })

    return {
        "subject_summary": f"Structured curriculum for {subject_name} ({focus}).",
        "topics": topics_out,
    }


def _try_gemini_curriculum(client: genai.Client, prompt: str, primary_model: str):
    models_to_try = [
        primary_model,
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]
    seen = set()

    for model in models_to_try:
        if not model or model in seen:
            continue
        seen.add(model)

        for attempt in range(2):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=CURRICULUM_JSON_SCHEMA,
                    ),
                )
                if resp and resp.text:
                    return json.loads(resp.text)
            except Exception as exc:
                err = str(exc)
                if "404" in err or "NOT_FOUND" in err:
                    break
                if ("503" in err or "UNAVAILABLE" in err or "429" in err) and attempt == 0:
                    time.sleep(0.5)
                    continue
                break

    return None


def generate_subject_data(
    conn: sqlite3.Connection,
    subject_name: str,
    subject_description: str = "",
    questions_per_topic: int = 2,
    model_name: str = "gemini-3.8-flash",
) -> dict:
    clean_subject = str(subject_name or "").strip()
    if not clean_subject:
        raise ValueError("Subject name is required.")

    q_count = max(2, min(3, int(questions_per_topic or 2)))
    prompt = (
        f"Create a concise learning curriculum for '{clean_subject}'. "
        f"Focus/level: {subject_description.strip() or 'Foundations to intermediate'}.\n"
        f"Include 5 topics ordered from foundational to advanced with short codes T1, T2, T3, T4, T5. "
        f"Set prerequisite_codes only to earlier topic codes (acyclic). "
        f"Provide {q_count} multiple-choice questions (A/B/C/D) per topic with explanation, "
        f"and 2 learning resources per topic with valid https:// URLs."
    )

    data = None
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            data = _try_gemini_curriculum(client, prompt, model_name)
        except Exception:
            data = None

    if not data or not isinstance(data.get("topics"), list) or not data["topics"]:
        data = _build_local_fallback_curriculum(clean_subject, subject_description, q_count)

    clean_desc = (subject_description or data.get("subject_summary") or "").strip()

    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO subjects (subject_name, description)
            VALUES (?, ?)
            """,
            (clean_subject, clean_desc),
        )
        subject_row = conn.execute(
            "SELECT subject_id FROM subjects WHERE subject_name = ?",
            (clean_subject,),
        ).fetchone()
        subject_id = int(subject_row["subject_id"])

        code_to_topic_id = {}
        ordered_topic_ids = []
        created_question_ids = []
        created_resource_count = 0

        for idx, topic in enumerate(data.get("topics", []), start=1):
            raw_code = str(topic.get("code") or f"T{idx}").strip().upper()
            db_topic_code = f"S{subject_id}_{raw_code}_{idx}"

            conn.execute(
                """
                INSERT INTO topics (
                    subject_id, topic_code, topic_name, description,
                    difficulty_level, display_order
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    subject_id,
                    db_topic_code,
                    topic["name"].strip(),
                    topic["description"].strip(),
                    topic.get("difficulty_level") or "Beginner",
                    idx,
                ),
            )
            topic_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            code_to_topic_id[raw_code] = topic_id
            ordered_topic_ids.append(topic_id)

            for q in topic.get("questions", []):
                conn.execute(
                    """
                    INSERT INTO questions (
                        topic_id, question_text, option_a, option_b, option_c, option_d,
                        correct_option, explanation, difficulty_level, is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        topic_id,
                        q["question_text"].strip(),
                        q["option_a"].strip(),
                        q["option_b"].strip(),
                        q["option_c"].strip(),
                        q["option_d"].strip(),
                        q["correct_option"],
                        q["explanation"].strip(),
                        q.get("difficulty_level") or topic.get("difficulty_level") or "Beginner",
                    ),
                )
                qid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
                created_question_ids.append(qid)

            for r in topic.get("resources", []):
                url = str(r.get("resource_url") or "").strip()
                if not url.startswith(("http://", "https://")):
                    url = "https://www.google.com/search?q=" + "+".join(
                        f"{clean_subject} {topic['name']}".split()
                    )
                conn.execute(
                    """
                    INSERT INTO learning_resources (
                        topic_id, resource_title, resource_type,
                        resource_url, resource_description, is_active
                    )
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (
                        topic_id,
                        r["resource_title"].strip(),
                        r.get("resource_type") or "Notes",
                        url,
                        r["resource_description"].strip(),
                    ),
                )
                created_resource_count += 1

        for idx, topic in enumerate(data.get("topics", []), start=1):
            raw_code = str(topic.get("code") or f"T{idx}").strip().upper()
            topic_id = code_to_topic_id.get(raw_code)
            if not topic_id:
                continue

            for prereq_code in topic.get("prerequisite_codes", []):
                prereq_id = code_to_topic_id.get(str(prereq_code).strip().upper())
                if prereq_id and prereq_id != topic_id:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO prerequisites (topic_id, prerequisite_topic_id)
                        VALUES (?, ?)
                        """,
                        (topic_id, prereq_id),
                    )

        conn.execute(
            """
            INSERT INTO tests (test_name, subject_id, test_type, description, is_active)
            VALUES (?, ?, 'Diagnostic', ?, 1)
            """,
            (
                f"{clean_subject} Diagnostic Test",
                subject_id,
                f"Diagnostic assessment covering {clean_subject} and prerequisite concepts.",
            ),
        )
        test_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

        for order_num, qid in enumerate(created_question_ids, start=1):
            conn.execute(
                """
                INSERT INTO test_questions (test_id, question_id, question_order)
                VALUES (?, ?, ?)
                """,
                (test_id, qid, order_num),
            )

    return {
        "subject_id": subject_id,
        "subject_name": clean_subject,
        "test_id": test_id,
        "topics_created": len(ordered_topic_ids),
        "questions_created": len(created_question_ids),
        "resources_created": created_resource_count,
    }