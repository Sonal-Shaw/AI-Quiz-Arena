"""
bank.py - loads question_bank.xlsx and turns every row into a ready-to-use question.

Expected columns (exactly as in your Excel file):
    id, topic, type, difficulty, question, option_a..option_d, answer, explanation, hint

Question kinds handled
    choice : MCQ, Scenario, Problem-Solving, True/False, Assertion–Reason  (answer = A/B/C/D)
    fill   : Fill in the Blank                                           (answer = text)
    match  : Match the Following                                         (answer = "1 → b; 2 → a; ...")
"""
import re
import random
from pathlib import Path

import pandas as pd
import streamlit as st

BANK_PATH = Path(__file__).parent / "data" / "question_bank.xlsx"
DIAG_DIR = Path(__file__).parent / "data" / "diagrams"      # optional q<id>.svg picture for tree/graph questions
LEVELS = ["Easy", "Medium", "Hard"]

# Assignment topic  ->  label(s) used in the Excel "topic" column
REQUIRED_TOPICS = {
    "Foundations and Applications of AI": ["Foundations and Applications of AI"],
    "Turing Test": ["Turing Test"],
    "Rational Agents": ["Rational Agents"],
    "Intelligent Agents": ["Intelligent Agents"],
    "Agents and Environments": ["Agents and Environments"],
    "Good Behaviour": ["Good Behaviour"],
    "Nature of Environments": ["Nature of Environments"],
    "Problems and Problem Spaces": ["Problems and Problem Spaces"],
    "State Space Search": ["State Space Search"],
    "Production Systems": ["Production Systems"],
    "Problem Characteristics": ["Problem Characteristics"],
    "Issues in Search Program Design": ["Issues in Search Program Design"],
    "BFS": ["BFS"],
    "DFS": ["DFS"],
    "Iterative Deepening": ["Iterative Deepening"],
    "Hill Climbing and its Variations": ["Hill Climbing", "Hill Climbing and Variations"],
    "Heuristic Search": ["Heuristic Search"],
    "Best First Search": ["Best First Search"],
    "Constraint Satisfaction Problems (CSP)": ["Constraint Satisfaction Problems"],
    "Means-End Analysis": ["Means-End Analysis"],
}

# question types that count as "real-world / scenario" and "search / state-space"
REAL_WORLD_TYPES = {"Scenario"}
SEARCH_TOPICS = {"State Space Search", "BFS", "DFS", "Iterative Deepening", "Hill Climbing",
                 "Hill Climbing and Variations", "Heuristic Search", "Best First Search",
                 "Means-End Analysis", "Problems and Problem Spaces"}

# options that must always stay at the bottom when options are shuffled
_PIN_LAST = ("all three", "all of", "none of")


def _clean(v):
    return None if pd.isna(v) else str(v).strip()


def _parse_match(text: str, answer: str):
    """Split the 'Match the Following' text into left items / right options / key."""
    try:
        head, right = re.split(r"\.\s+a\.\s", text, maxsplit=1)
        intro, left = head.split(":", 1)
        left_items = re.findall(r"(\d)\.\s*(.+?)(?=\s+\d\.|$)", left.strip())
        right_items = re.findall(r"([a-d])\.\s*(.+?)(?=\s+[a-d]\.\s|$)", "a. " + right)
        key = dict(re.findall(r"(\d)\s*→\s*([a-d])", answer))
        if len(left_items) >= 2 and len(right_items) >= 2 and len(key) == len(left_items):
            return {"intro": intro.strip() + ":", "left": left_items, "right": right_items, "key": key}
    except ValueError:
        pass
    return None


@st.cache_resource(show_spinner=False)
def load_bank():
    df = pd.read_excel(BANK_PATH, sheet_name="Question Bank")
    questions = []
    for _, r in df.iterrows():
        q = {
            "id": int(r["id"]),
            "topic": _clean(r["topic"]),
            "type": _clean(r["type"]),
            "difficulty": _clean(r["difficulty"]),
            "text": _clean(r["question"]),
            "explanation": _clean(r["explanation"]) or "",
            "hint": _clean(r["hint"]) or "Think about the key idea behind this topic.",
            "answer_raw": _clean(r["answer"]),
        }
        svg = DIAG_DIR / f"q{q['id']}.svg"
        q["diagram"] = svg.read_text(encoding="utf-8") if svg.exists() else None
        opts = [_clean(r[c]) for c in ("option_a", "option_b", "option_c", "option_d")]
        opts = [o for o in opts if o]

        if q["type"] == "Fill in the Blank":
            q.update(kind="fill", answer_text=q["answer_raw"])
        elif q["type"] == "Match the Following":
            m = _parse_match(q["text"], q["answer_raw"])
            if m:
                q.update(kind="match", match=m, answer_text=q["answer_raw"])
            else:                                   # safe fallback
                q.update(kind="choice", options=opts, correct=0, answer_text=q["answer_raw"])
        else:
            idx = ord(q["answer_raw"].upper()) - 65
            q.update(kind="choice", options=opts, correct=idx, answer_text=opts[idx])
            # shuffle only where the order carries no meaning
            q["shuffle"] = q["type"] in {"MCQ", "Scenario", "Problem-Solving"} and len(opts) >= 3
        questions.append(q)
    return questions


def option_order(q) -> list:
    """Return option indices in display order (shuffled for MCQ-like questions)."""
    order = list(range(len(q["options"])))
    if q.get("shuffle"):
        pinned = [i for i in order if q["options"][i].lower().startswith(_PIN_LAST)]
        free = [i for i in order if i not in pinned]
        random.shuffle(free)
        order = free + pinned
    return order


def normalise(text: str) -> str:
    """Lower-case, drop punctuation/articles and plural 's' so 'The State-Space' == 'state spaces'."""
    t = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower().replace("-", " "))
    words = [w for w in t.split() if w not in {"the", "a", "an"}]
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words)


def check_fill(q, user_text: str) -> bool:
    return normalise(user_text) == normalise(q["answer_text"])


# ---------------------------------------------------------------- stats for the home page
def bank_stats(questions):
    types = {q["type"] for q in questions}
    levels = [lv for lv in LEVELS if any(q["difficulty"] == lv for q in questions)]
    labels = {q["topic"] for q in questions}
    covered = sum(1 for names in REQUIRED_TOPICS.values() if any(n in labels for n in names))
    counts = {"All Levels": len(questions)}
    for lv in LEVELS:
        counts[lv] = sum(1 for q in questions if q["difficulty"] == lv)
    return {"total": len(questions), "topics": covered, "formats": len(types),
            "levels": len(levels), "counts": counts}
