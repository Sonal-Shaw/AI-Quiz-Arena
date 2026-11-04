"""
quiz_page.py - the interactive quiz screen.

Features: random questions, per-question countdown timer, progress indicator,
instant feedback + explanation, hints, 50-50 lifeline, skip, score & streak bonus.
"""
import base64
import html as H
import os
import random
import time

import streamlit as st

from bank import load_bank, option_order, check_fill
from theme import html, page_frame

# ------------------------------------------------------------------ game settings
ROUND_SIZE = int(os.environ.get("QUIZ_ROUND_SIZE", 10))   # questions per round (50 = whole bank)
HINTS_PER_ROUND = 3
FIFTY_PER_ROUND = 1
SKIPS_PER_ROUND = 2
BASE_POINTS = {"Easy": 10, "Medium": 20, "Hard": 30}
TIME_LIMIT = {                       # seconds
    "True/False": 20, "MCQ": 30, "Fill in the Blank": 30, "Scenario": 45,
    "Assertion–Reason": 45, "Match the Following": 60, "Problem-Solving": 60,
}
TIME_SCALE = float(os.environ.get("QUIZ_TIME_SCALE", 1))   # leave at 1 (only used for testing)
HINT_PENALTY = 0.25                  # fraction of base points lost if a hint was used
TIME_BONUS = 0.50                    # up to +50 % of base points for answering fast
STREAK_BONUS = 5                     # +5 per extra correct answer in a row (max 4 steps)


def get_q(qid):
    return next(q for q in load_bank() if q["id"] == qid)


# ------------------------------------------------------------------ round / question state
def new_round(level: str, name: str):
    bank = load_bank()
    pool = [q["id"] for q in bank if level == "All Levels" or q["difficulty"] == level]
    random.shuffle(pool)
    n = min(ROUND_SIZE, len(pool))
    st.session_state.quiz = {
        "name": name, "level": level, "queue": pool[:n], "reserve": pool[n:], "i": 0,
        "score": 0, "streak": 0, "best_streak": 0, "records": [],
        "hints_left": HINTS_PER_ROUND, "fifty_left": FIFTY_PER_ROUND,
        "skips_left": SKIPS_PER_ROUND, "skips_used": 0, "t_start": time.time(), "saved": False,
    }
    _load_question()


def _load_question():
    quiz = st.session_state.quiz
    q = get_q(quiz["queue"][quiz["i"]])
    st.session_state.cur = {
        "qid": q["id"], "order": option_order(q) if q["kind"] == "choice" else [],
        "t0": time.time(), "limit": max(3, TIME_LIMIT.get(q["type"], 30) * TIME_SCALE),
        "answered": False, "hint": False, "elim": [], "outcome": None,
    }


# ------------------------------------------------------------------ grading + scoring
def _grade(q, payload):
    """Return (fraction_correct 0..1, what_user_answered, correct_answer_text)."""
    if payload is None:
        return 0.0, "—", q["answer_text"]
    if q["kind"] == "choice":
        return (1.0 if payload == q["correct"] else 0.0), q["options"][payload], q["answer_text"]
    if q["kind"] == "fill":
        return (1.0 if check_fill(q, payload) else 0.0), (payload or "—"), q["answer_text"]
    key = q["match"]["key"]                                   # match
    right = dict(q["match"]["right"])
    good = sum(1 for k, v in key.items() if payload.get(k) == v)
    mine = "; ".join(f"{k} → {payload.get(k) or '?'}" for k in key)
    return good / len(key), mine, q["answer_text"]


def register(payload, timed_out=False):
    quiz, cur = st.session_state.quiz, st.session_state.cur
    if cur["answered"]:
        return
    q = get_q(cur["qid"])
    spent = time.time() - cur["t0"]
    left = max(0.0, cur["limit"] - spent)
    frac, mine, correct_txt = _grade(q, None if timed_out else payload)

    base = BASE_POINTS.get(q["difficulty"], 10) * frac
    bonus = round(base * TIME_BONUS * left / cur["limit"]) if frac > 0 else 0
    penalty = round(base * HINT_PENALTY) if (frac > 0 and cur["hint"]) else 0
    full = frac == 1.0
    quiz["streak"] = quiz["streak"] + 1 if full else 0
    quiz["best_streak"] = max(quiz["best_streak"], quiz["streak"])
    streak_pts = STREAK_BONUS * min(quiz["streak"] - 1, 4) if full and quiz["streak"] >= 2 else 0
    points = max(0, round(base) + bonus - penalty) + streak_pts if frac > 0 else 0
    quiz["score"] += points

    status = "timeout" if timed_out else ("correct" if full else ("partial" if frac > 0 else "wrong"))
    cur["outcome"] = {"status": status, "points": points, "base": round(base), "bonus": bonus,
                      "penalty": penalty, "streak_pts": streak_pts, "left": left,
                      "mine": mine, "correct_txt": correct_txt, "payload": payload, "frac": frac}
    cur["answered"] = True
    quiz["records"].append({
        "id": q["id"], "topic": q["topic"], "type": q["type"], "difficulty": q["difficulty"],
        "question": q["text"], "mine": mine, "correct_txt": correct_txt, "explanation": q["explanation"],
        "status": status, "points": points, "time": round(spent, 1), "hint": cur["hint"],
    })


# ------------------------------------------------------------------ button callbacks
def answer_choice(idx):
    register(idx)


def answer_fill():
    cur = st.session_state.cur
    register((st.session_state.get(f"fill_{cur['qid']}") or "").strip())


def answer_match():
    cur = st.session_state.cur
    q = get_q(cur["qid"])
    picked = {}
    for num, _ in q["match"]["left"]:
        v = st.session_state.get(f"m_{cur['qid']}_{num}", "Select…")
        picked[num] = v.split(".")[0] if v != "Select…" else None
    register(picked)


def use_hint():
    quiz, cur = st.session_state.quiz, st.session_state.cur
    if quiz["hints_left"] > 0 and not cur["hint"]:
        quiz["hints_left"] -= 1
        cur["hint"] = True


def use_fifty():
    quiz, cur = st.session_state.quiz, st.session_state.cur
    q = get_q(cur["qid"])
    if quiz["fifty_left"] > 0 and not cur["elim"] and q["kind"] == "choice" and len(q["options"]) >= 3:
        wrong = [i for i in range(len(q["options"])) if i != q["correct"]]
        cur["elim"] = random.sample(wrong, 2)
        quiz["fifty_left"] -= 1


def do_skip():
    quiz = st.session_state.quiz
    if quiz["skips_left"] > 0 and quiz["reserve"]:
        quiz["queue"][quiz["i"]] = quiz["reserve"].pop(0)
        quiz["skips_left"] -= 1
        quiz["skips_used"] += 1
        _load_question()


def go_next():
    quiz = st.session_state.quiz
    if quiz["i"] + 1 >= len(quiz["queue"]):
        quiz["t_total"] = time.time() - quiz["t_start"]
        st.session_state.page = "result"
    else:
        quiz["i"] += 1
        _load_question()


def quit_quiz():
    st.session_state.page = "home"


# ------------------------------------------------------------------ CSS
QUIZ_CSS = """<style>
.block-container { max-width: 920px !important; }
[data-testid="stVerticalBlock"] { gap: .75rem !important; }

/* HUD */
.hud { margin-bottom: 14px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; padding: 14px 10px; text-align: center; }
.hud .k { display: block; font-size: .85rem; color: #9fb0d8; }
.hud .v { display: block; margin-top: 2px; font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 1.15rem; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hud .v.score { font-size: 1.5rem; background: linear-gradient(90deg, #67e8f9, #a78bfa, #f0abfc); -webkit-background-clip: text; background-clip: text; color: transparent; }

/* progress segments */
.seg { display: flex; gap: 6px; margin-top: 0; }
.seg i { flex: 1; height: 8px; border-radius: 6px; background: rgba(255,255,255,.10); }
.seg i.correct { background: #34d399; box-shadow: 0 0 10px rgba(52,211,153,.7); }
.seg i.partial { background: #fbbf24; box-shadow: 0 0 10px rgba(251,191,36,.6); }
.seg i.wrong { background: #f43f5e; box-shadow: 0 0 10px rgba(244,63,94,.7); }
.seg i.timeout { background: #f97316; box-shadow: 0 0 10px rgba(249,115,22,.7); }
.seg i.cur { background: #22d3ee; box-shadow: 0 0 12px rgba(34,211,238,.9); animation: blink 1.4s ease-in-out infinite; }
@keyframes blink { 50% { opacity: .45; } }
.segtxt { margin: 10px 0 16px; font-size: .95rem; color: #aab9df; text-align: center; }

/* timer */
.timer { display: flex; align-items: center; gap: 14px; margin: 2px 0 18px; }
.tbar { flex: 1; height: 12px; border-radius: 8px; background: rgba(255,255,255,.08); overflow: hidden; }
.tbar i { display: block; height: 100%; border-radius: 8px; transition: width 1s linear, background .5s; }
.tnum { min-width: 64px; text-align: right; font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 1.35rem; color: #fff; }
.tnum.warn { color: #f43f5e; animation: blink .8s ease-in-out infinite; }

/* question card */
.qcard { padding: 26px 28px 28px; margin-bottom: 20px; }
.meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.pill { padding: 5px 13px; border-radius: 999px; font-size: .85rem; font-weight: 600; color: #dde6ff; background: rgba(255,255,255,.06); border: 1px solid rgba(125,211,252,.25); }
.pill.lvl-Easy { color: #6ee7b7; border-color: rgba(52,211,153,.5); } .pill.lvl-Medium { color: #fcd34d; border-color: rgba(251,191,36,.5); }
.pill.lvl-Hard { color: #fda4af; border-color: rgba(244,63,94,.5); } .pill.pts { color: #67e8f9; border-color: rgba(34,211,238,.5); }
.qtext { font-size: 1.3rem; line-height: 1.6; font-weight: 600; color: #fff; }
.qtext b { color: #67e8f9; }

/* hint */
.hintcard { margin-bottom: 16px; padding: 14px 20px; border-radius: 14px; font-size: 1.05rem; color: #fde68a; background: rgba(251,191,36,.08); border: 1px solid rgba(251,191,36,.4); }

/* option buttons (before answering) */
[class*="st-key-opt_"] button { width: 100%; height: auto !important; min-height: 64px; justify-content: flex-start !important; padding: 16px 22px !important;
  border-radius: 16px !important; background: rgba(255,255,255,.05) !important; border: 1px solid rgba(125,211,252,.30) !important; transition: all .25s; }
[class*="st-key-opt_"] button div { justify-content: flex-start !important; text-align: left !important; width: 100%; }
[class*="st-key-opt_"] button p { margin: 0; font-family: 'Sora', sans-serif; font-size: 1.12rem; font-weight: 600; color: #eaf0ff !important; text-align: left; }
[class*="st-key-opt_"] button:hover:not(:disabled) { transform: translateX(6px); border-color: #22d3ee !important; background: rgba(34,211,238,.10) !important; box-shadow: 0 0 22px rgba(34,211,238,.35); }
[class*="st-key-opt_"] button:disabled { opacity: .3; }
[class*="st-key-opt_"] button:disabled p { text-decoration: line-through; }

/* answered option cards */
.opt { display: flex; align-items: center; gap: 14px; padding: 16px 22px; min-height: 64px; border-radius: 16px; font-size: 1.12rem; font-weight: 600; color: #eaf0ff;
  background: rgba(255,255,255,.04); border: 1px solid rgba(125,211,252,.18); margin-bottom: 12px; }
.opt .mk { margin-left: auto; font-weight: 800; font-size: 1.2rem; }
.opt.ok { background: rgba(52,211,153,.14); border-color: #34d399; box-shadow: 0 0 24px rgba(52,211,153,.35); }
.opt.ok .mk { color: #34d399; }
.opt.bad { background: rgba(244,63,94,.14); border-color: #f43f5e; box-shadow: 0 0 24px rgba(244,63,94,.35); }
.opt.bad .mk { color: #f43f5e; }
.opt.dim { opacity: .4; }

/* tool buttons */
[class*="st-key-tool_"] { margin-top: 8px; }
[class*="st-key-tool_"] button { width: 100%; height: 48px; border-radius: 999px !important; background: rgba(255,255,255,.05) !important;
  border: 1px solid rgba(167,139,250,.45) !important; transition: all .25s; }
[class*="st-key-tool_"] button p { font-family: 'Sora', sans-serif; font-size: .98rem; font-weight: 600; color: #e4ebff !important; }
[class*="st-key-tool_"] button:hover:not(:disabled) { border-color: #a78bfa !important; box-shadow: 0 0 20px rgba(167,139,250,.5); transform: translateY(-2px); }
[class*="st-key-tool_"] button:disabled { opacity: .35; }

/* feedback */
.fb { padding: 22px 26px; margin: 6px 0 18px; }
.fb.correct { box-shadow: 0 0 34px rgba(52,211,153,.30); } .fb.wrong, .fb.timeout { box-shadow: 0 0 34px rgba(244,63,94,.28); } .fb.partial { box-shadow: 0 0 34px rgba(251,191,36,.28); }
.fb-h { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 1.35rem; }
.fb.correct .fb-h { color: #34d399; } .fb.wrong .fb-h { color: #f43f5e; } .fb.timeout .fb-h { color: #fb923c; } .fb.partial .fb-h { color: #fbbf24; }
.fb-h .pts { font-size: 1.2rem; color: #67e8f9; }
.fb-a { margin-top: 12px; font-size: 1.05rem; color: #dde6ff; } .fb-a b { color: #fff; }
.fb-e { margin-top: 10px; font-size: 1.05rem; line-height: 1.65; color: #B6C2E2; }
.fb-b { margin-top: 12px; font-size: .9rem; color: #8a9bc6; }

/* primary buttons (submit / next) */
button[kind="primary"], button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
  height: 60px; border: none !important; border-radius: 999px !important; color: #fff !important;
  background: linear-gradient(90deg, #22d3ee, #8b5cf6 55%, #ec4899) !important; box-shadow: 0 0 22px rgba(34,211,238,.4), 0 0 46px rgba(139,92,246,.3); transition: transform .25s, box-shadow .25s; }
button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; font-weight: 800; letter-spacing: 2px; color: #fff !important; }
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover { transform: scale(1.02); box-shadow: 0 0 34px rgba(34,211,238,.8), 0 0 70px rgba(236,72,153,.5); }

/* fill / match widgets */
div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
div[data-testid="stTextInput"] div[data-baseweb="input"], div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background: rgba(255,255,255,.05) !important; border: 1px solid rgba(125,211,252,.32) !important; border-radius: 14px !important; }
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within { border-color: #22d3ee !important; box-shadow: 0 0 0 3px rgba(34,211,238,.18), 0 0 24px rgba(34,211,238,.3) !important; }
div[data-testid="stTextInput"] input { color: #fff !important; font-size: 1.2rem !important; height: 58px !important; padding: 0 18px !important; background: transparent !important; text-align: center !important; }
div[data-testid="stTextInput"] input::placeholder { color: #8a9bc6 !important; }
div[data-testid="stSelectbox"] label p { font-family: 'Sora', sans-serif; font-size: 1.1rem; font-weight: 700; color: #fff; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] * { font-size: 1.02rem; color: #eaf0ff; }

[class*="st-key-exit"] button { background: transparent !important; border: none !important; color: #8a9bc6 !important; }
[class*="st-key-exit"] button:hover { color: #fff !important; }

@media (max-width: 600px) { .hud { grid-template-columns: repeat(2, 1fr); } .qtext { font-size: 1.12rem; } .qcard { padding: 20px 18px; } }
</style>"""


# ------------------------------------------------------------------ small renderers
def _fmt_question(q) -> str:
    text = q["text"]
    if q["kind"] == "match":
        text = q["match"]["intro"]
    safe = H.escape(text)
    if q["type"] == "Assertion–Reason":
        safe = safe.replace("Assertion:", "<b>Assertion:</b>").replace("Reason:", "<br><b>Reason:</b>")
    return safe.replace("__________", "<b>________</b>")


def _progress(quiz, cur):
    segs = []
    for j in range(len(quiz["queue"])):
        if j < quiz["i"]:
            segs.append(f'<i class="{quiz["records"][j]["status"]}"></i>')
        elif j == quiz["i"]:
            segs.append(f'<i class="{cur["outcome"]["status"]}"></i>' if cur["answered"] else '<i class="cur"></i>')
        else:
            segs.append("<i></i>")
    return f'<div class="seg">{"".join(segs)}</div><div class="segtxt">Question {quiz["i"] + 1} of {len(quiz["queue"])}</div>'


@st.fragment(run_every=1)
def timer_view():
    """Counts down once per second; auto-submits as 'time up' at zero."""
    cur = st.session_state.get("cur")
    if not cur:
        return
    if cur["answered"]:
        left = cur["outcome"]["left"]
    else:
        left = cur["limit"] - (time.time() - cur["t0"])
        if left <= 0:
            register(None, timed_out=True)
            st.rerun()
    pct = max(0, min(100, 100 * left / cur["limit"]))
    color = "#22d3ee" if pct > 50 else ("#fbbf24" if pct > 25 else "#f43f5e")
    warn = " warn" if (not cur["answered"] and left <= 5) else ""
    html(f'<div class="timer"><div class="tbar"><i style="width:{pct:.0f}%;background:{color};box-shadow:0 0 12px {color}"></i></div>'
         f'<div class="tnum{warn}">{max(0, left):.0f}s</div></div>')


def _answer_choice_ui(q, cur, quiz):
    order = cur["order"]
    two = len(order) == 2
    if cur["answered"]:
        sel = cur["outcome"]["payload"]
        for p, oi in enumerate(order):
            cls = "ok" if oi == q["correct"] else ("bad" if oi == sel else "dim")
            mk = "✓" if oi == q["correct"] else ("✗" if oi == sel else "")
            lead = "" if two else f'<b style="color:#8a9bc6">{chr(65 + p)}</b>'
            html(f'<div class="opt {cls}">{lead}<span>{H.escape(q["options"][oi])}</span><span class="mk">{mk}</span></div>')
        return
    cols = st.columns(2) if two else None
    for p, oi in enumerate(order):
        label = q["options"][oi] if two else f"**{chr(65 + p)}**\u2003{q['options'][oi]}"
        host = cols[p] if two else st
        if oi in cur["elim"]:
            host.button(label, key=f"opt_{q['id']}_{p}", disabled=True, use_container_width=True)
        else:
            host.button(label, key=f"opt_{q['id']}_{p}", on_click=answer_choice, args=(oi,), use_container_width=True)


def _answer_fill_ui(q, cur):
    if cur["answered"]:
        o = cur["outcome"]
        cls = "ok" if o["status"] == "correct" else "bad"
        html(f'<div class="opt {cls}"><span>Your answer: <b>{H.escape(str(o["mine"]))}</b></span>'
             f'<span class="mk">{"✓" if cls == "ok" else "✗"}</span></div>')
        return
    with st.form(key=f"form_{q['id']}"):
        st.text_input("Your answer", key=f"fill_{q['id']}", placeholder="Type your answer and press Enter",
                      label_visibility="collapsed")
        st.form_submit_button("Submit answer", type="primary", on_click=answer_fill, use_container_width=True)


def _answer_match_ui(q, cur):
    m = q["match"]
    if cur["answered"]:
        got = cur["outcome"]["payload"] or {}
        right = dict(m["right"])
        for num, name in m["left"]:
            ok = got.get(num) == m["key"][num]
            mine = f'{got.get(num)}. {right[got[num]]}' if got.get(num) else "no answer"
            html(f'<div class="opt {"ok" if ok else "bad"}"><span><b>{num}. {H.escape(name)}</b> → {H.escape(mine)}'
                 f'{"" if ok else "  (correct: " + m["key"][num] + ". " + H.escape(right[m["key"][num]]) + ")"}</span>'
                 f'<span class="mk">{"✓" if ok else "✗"}</span></div>')
        return
    choices = ["Select…"] + [f"{k}. {t}" for k, t in m["right"]]
    with st.form(key=f"form_{q['id']}"):
        for num, name in m["left"]:
            st.selectbox(f"{num}. {name}", choices, key=f"m_{q['id']}_{num}")
        st.form_submit_button("Submit answer", type="primary", on_click=answer_match, use_container_width=True)


# ------------------------------------------------------------------ page
def render_quiz():
    page_frame()
    st.html(QUIZ_CSS)

    quiz, cur = st.session_state.get("quiz"), st.session_state.get("cur")
    if not quiz or not cur:                                    # e.g. page refreshed
        st.session_state.page = "home"
        st.rerun()
    q = get_q(cur["qid"])

    html(f"""<div class="hud glass">
      <div><span class="k">Player</span><span class="v">{H.escape(quiz["name"])}</span></div>
      <div><span class="k">Level</span><span class="v">{quiz["level"]}</span></div>
      <div><span class="k">Streak</span><span class="v">{quiz["streak"]}</span></div>
      <div><span class="k">Score</span><span class="v score">{quiz["score"]}</span></div></div>""")
    html(_progress(quiz, cur))
    timer_view()

    html(f"""<div class="qcard glass">
      <div class="meta"><span class="pill">{H.escape(q["topic"])}</span><span class="pill">{H.escape(q["type"])}</span>
      <span class="pill lvl-{q["difficulty"]}">{q["difficulty"]}</span>
      <span class="pill pts">up to {BASE_POINTS.get(q["difficulty"], 10) * 3 // 2} pts</span></div>
      <div class="qtext">{_fmt_question(q)}</div></div>""")

    if q.get("diagram"):                                       # tree / graph picture (data/diagrams/q<id>.svg)
        b64 = base64.b64encode(q["diagram"].encode("utf-8")).decode()
        html(f'<div style="text-align:center;margin:4px 0 16px"><img alt="Diagram for the question" '
             f'src="data:image/svg+xml;base64,{b64}" style="max-width:100%;height:auto;border-radius:14px"/></div>')

    if cur["hint"]:
        html(f'<div class="hintcard"><b>Hint:</b> {H.escape(q["hint"])}</div>')

    if q["kind"] == "choice":
        _answer_choice_ui(q, cur, quiz)
    elif q["kind"] == "fill":
        _answer_fill_ui(q, cur)
    else:
        _answer_match_ui(q, cur)

    if not cur["answered"]:
        can_fifty = q["kind"] == "choice" and len(q["options"]) >= 3 and not cur["elim"] and quiz["fifty_left"] > 0
        c1, c2, c3 = st.columns(3)
        c1.button(f"Hint  ·  {quiz['hints_left']} left", key="tool_hint", on_click=use_hint,
                  disabled=cur["hint"] or quiz["hints_left"] == 0, use_container_width=True)
        c2.button(f"50-50  ·  {quiz['fifty_left']} left", key="tool_fifty", on_click=use_fifty,
                  disabled=not can_fifty, use_container_width=True)
        c3.button(f"Skip  ·  {quiz['skips_left']} left", key="tool_skip", on_click=do_skip,
                  disabled=quiz["skips_left"] == 0 or not quiz["reserve"], use_container_width=True)
    else:
        o = cur["outcome"]
        title = {"correct": "Correct!", "wrong": "Not quite", "timeout": "Time's up", "partial": "Partly correct"}[o["status"]]
        show_ans = "" if o["status"] == "correct" else f'<div class="fb-a">Correct answer: <b>{H.escape(o["correct_txt"])}</b></div>'
        parts = [f'{o["base"]} base']
        if o["bonus"]:
            parts.append(f'+ {o["bonus"]} speed bonus')
        if o["penalty"]:
            parts.append(f'− {o["penalty"]} hint')
        if o["streak_pts"]:
            parts.append(f'+ {o["streak_pts"]} streak')
        html(f"""<div class="fb glass {o["status"]}"><div class="fb-h"><span>{title}</span><span class="pts">+{o["points"]} pts</span></div>
          {show_ans}<div class="fb-e">{H.escape(q["explanation"])}</div>
          <div class="fb-b">{"  ".join(parts)}</div></div>""")
        last = quiz["i"] + 1 >= len(quiz["queue"])
        st.button("See my results" if last else "Next question", key="next", type="primary",
                  on_click=go_next, use_container_width=True)

    st.button("Exit to home", key="exit_btn", on_click=quit_quiz)
