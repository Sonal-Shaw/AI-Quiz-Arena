"""
result_page.py - final score screen, topic breakdown, answer review and leaderboard.

The leaderboard is stored in leaderboard.csv (next to this file), so it survives restarts
when you run the app on your own computer.
"""
import csv
import datetime as dt
import html as H
from collections import OrderedDict
from pathlib import Path

import streamlit as st

from theme import html, page_frame

LB_PATH = Path(__file__).parent / "leaderboard.csv"
FIELDS = ["name", "score", "correct", "total", "accuracy", "level", "time_s", "date"]


# ------------------------------------------------------------------ leaderboard storage
def load_leaderboard():
    if not LB_PATH.exists():
        return []
    with open(LB_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["score"], r["correct"], r["total"] = int(r["score"]), int(r["correct"]), int(r["total"])
        r["accuracy"], r["time_s"] = float(r["accuracy"]), float(r["time_s"])
    rows.sort(key=lambda r: (-r["score"], -r["accuracy"], r["time_s"]))
    return rows


def save_entry(entry: dict):
    new_file = not LB_PATH.exists()
    with open(LB_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(entry)


# ------------------------------------------------------------------ actions
def play_again():
    from quiz_page import new_round
    quiz = st.session_state.quiz
    new_round(quiz["level"], quiz["name"])
    st.session_state.page = "quiz"


def go_home():
    st.session_state.page = "home"


# ------------------------------------------------------------------ CSS
RESULT_CSS = """<style>
.block-container { max-width: 1000px !important; }
[data-testid="stVerticalBlock"] { gap: .75rem !important; }
.rhero { text-align: center; padding: 38px 24px 34px; overflow: hidden; margin-bottom: 18px; }
.rtitle { font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: clamp(2rem, 5vw, 3.4rem); letter-spacing: 3px; margin: 18px 0 6px;
  background: linear-gradient(90deg, #ffffff 0%, #67e8f9 35%, #a78bfa 70%, #f0abfc 100%); -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: glowPulse 3s ease-in-out infinite; }
.rank { display: inline-block; margin-top: 4px; padding: 8px 22px; border-radius: 999px; font-weight: 700; font-size: 1.1rem; color: #fde68a;
  background: rgba(251,191,36,.10); border: 1px solid rgba(251,191,36,.55); box-shadow: 0 0 22px rgba(251,191,36,.3); }
.ringwrap { display: flex; justify-content: center; margin: 26px 0 8px; }
.ring { --p: 0; width: 210px; height: 210px; border-radius: 50%; display: grid; place-items: center;
  background: conic-gradient(#22d3ee calc(var(--p) * 1%), #8b5cf6 calc(var(--p) * 1% + 10%), rgba(255,255,255,.08) 0);
  animation: fillring 1.6s ease-out backwards; box-shadow: 0 0 40px rgba(34,211,238,.35); }
.ring::before { content: ""; width: 168px; height: 168px; border-radius: 50%; background: #0a0e24; grid-area: 1/1; }
.ring .in { grid-area: 1/1; text-align: center; z-index: 1; }
.ring .big { font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 2.6rem; color: #fff; }
.ring .small { font-size: .95rem; color: #aab9df; }
@property --p { syntax: '<number>'; inherits: false; initial-value: 0; }
@keyframes fillring { from { --p: 0; } }
.scorepts { font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 1.6rem; color: #fff; margin-top: 8px; }
.scorepts span { background: linear-gradient(90deg, #67e8f9, #a78bfa, #f0abfc); -webkit-background-clip: text; background-clip: text; color: transparent; }
.g6r { margin-bottom: 8px; display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; }
.mini { padding: 18px 8px; text-align: center; }
.mini .v { font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 1.6rem; color: #fff; }
.mini .l { margin-top: 4px; font-size: .9rem; color: #aab9df; }
.mini.c1 .v { color: #34d399; } .mini.c2 .v { color: #f43f5e; } .mini.c3 .v { color: #fb923c; } .mini.c4 .v { color: #67e8f9; } .mini.c5 .v { color: #fbbf24; }
.panel { padding: 26px 26px 22px; margin-bottom: 8px; }
.trow { display: grid; grid-template-columns: 1.2fr 2fr 60px; gap: 14px; align-items: center; margin-bottom: 14px; font-size: 1rem; color: #dde6ff; }
.tbar2 { height: 10px; border-radius: 8px; background: rgba(255,255,255,.08); overflow: hidden; }
.tbar2 i { display: block; height: 100%; border-radius: 8px; background: linear-gradient(90deg, #22d3ee, #8b5cf6); }
.tbar2 i.low { background: linear-gradient(90deg, #f43f5e, #fb923c); }
.trow .fr { text-align: right; font-weight: 700; color: #fff; }
.lb { width: 100%; border-collapse: separate; border-spacing: 0 8px; }
.lb th { padding: 4px 14px; text-align: left; font-size: .9rem; font-weight: 600; color: #8a9bc6; }
.lb th, .lb td { border: none !important; }
.lb td { padding: 13px 14px; font-size: 1.02rem; color: #e4ebff; background: rgba(255,255,255,.045); }
.lb td:first-child { border-radius: 12px 0 0 12px; font-weight: 800; } .lb td:last-child { border-radius: 0 12px 12px 0; }
.lb tr.me td { background: rgba(34,211,238,.14); box-shadow: inset 0 1px 0 rgba(34,211,238,.6), inset 0 -1px 0 rgba(34,211,238,.6); color: #fff; }
.lb .sc { font-family: 'Orbitron', sans-serif; font-weight: 800; color: #67e8f9; }
.medal { display: inline-grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; font-weight: 800; color: #050714; }
.m1 { background: linear-gradient(135deg, #fde68a, #f59e0b); } .m2 { background: linear-gradient(135deg, #f1f5f9, #94a3b8); } .m3 { background: linear-gradient(135deg, #fdba74, #c2410c); }
.m0 { background: rgba(255,255,255,.1); color: #dde6ff; }
.rev-h { font-size: 1.05rem; font-weight: 700; color: #fff; }
.rev { font-size: 1rem; line-height: 1.7; color: #B6C2E2; } .rev b { color: #fff; }
.good { color: #34d399; } .badc { color: #f43f5e; }

button[kind="primary"], button[data-testid="stBaseButton-primary"] { height: 60px; border: none !important; border-radius: 999px !important; color: #fff !important;
  background: linear-gradient(90deg, #22d3ee, #8b5cf6 55%, #ec4899) !important; box-shadow: 0 0 22px rgba(34,211,238,.4), 0 0 46px rgba(139,92,246,.3); transition: transform .25s; }
button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p { font-family: 'Orbitron', sans-serif; font-size: 1.05rem; font-weight: 800; letter-spacing: 2px; color: #fff !important; }
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { transform: scale(1.02); }
[class*="st-key-home"] button { height: 60px; border-radius: 999px !important; background: rgba(255,255,255,.05) !important; border: 1px solid rgba(167,139,250,.5) !important; }
[class*="st-key-home"] button p { font-family: 'Orbitron', sans-serif; font-size: 1.05rem; font-weight: 800; letter-spacing: 2px; color: #fff !important; }
div[data-testid="stExpander"] { border: 1px solid rgba(125,211,252,.2) !important; border-radius: 14px !important; background: rgba(255,255,255,.03) !important; }
div[data-testid="stExpander"] summary p { font-size: 1rem; font-weight: 600; color: #e4ebff; }
@media (max-width: 800px) { .g6r { grid-template-columns: repeat(3, 1fr); } .trow { grid-template-columns: 1fr; gap: 6px; } .lb th:nth-child(n+5), .lb td:nth-child(n+5) { display: none; } }
</style>"""


def _rank_title(acc: float) -> str:
    if acc >= 90:
        return "AI Grandmaster"
    if acc >= 75:
        return "Search Expert"
    if acc >= 50:
        return "Rational Agent"
    return "Keep Exploring"


# ------------------------------------------------------------------ page
def render_result():
    page_frame()
    st.markdown(RESULT_CSS, unsafe_allow_html=True)

    quiz = st.session_state.get("quiz")
    if not quiz or not quiz["records"]:
        st.session_state.page = "home"
        st.rerun()

    recs = quiz["records"]
    total = len(recs)
    correct = sum(r["status"] == "correct" for r in recs)
    wrong = sum(r["status"] in ("wrong", "partial") for r in recs)
    timeout = sum(r["status"] == "timeout" for r in recs)
    acc = round(100 * correct / total, 1)
    avg_t = sum(r["time"] for r in recs) / total
    elapsed = round(quiz.get("t_total", sum(r["time"] for r in recs)), 1)

    # save once per round
    if not quiz["saved"]:
        entry = {"name": quiz["name"], "score": quiz["score"], "correct": correct, "total": total,
                 "accuracy": acc, "level": quiz["level"], "time_s": elapsed,
                 "date": dt.datetime.now().strftime("%d %b %Y %H:%M")}
        save_entry(entry)
        quiz["saved"] = True
        quiz["entry_date"] = entry["date"]
        if acc >= 70:
            st.balloons()

    # ---- hero
    html(f"""<div class="rhero glass fu"><i class="nt a"></i><i class="nt b"></i>
      <span class="badge">QUIZ COMPLETE</span>
      <div class="rtitle">WELL PLAYED, {H.escape(quiz["name"]).upper()}</div>
      <span class="rank">{_rank_title(acc)}</span>
      <div class="ringwrap"><div class="ring" style="--p:{acc}"><div class="in"><div class="big">{acc:.0f}%</div><div class="small">{correct} of {total} correct</div></div></div></div>
      <div class="scorepts">Total score: <span>{quiz["score"]} pts</span></div>
      <div class="divider"></div></div>""")

    # ---- mini stats
    cells = [("c1", correct, "Correct"), ("c2", wrong, "Wrong"), ("c3", timeout, "Timed out"),
             ("c4", quiz["skips_used"], "Skips used"), ("c5", quiz["best_streak"], "Best streak"),
             ("", f"{avg_t:.0f}s", "Avg. time")]
    html('<div class="g6r">' + "".join(
        f'<div class="mini glass {c}"><div class="v">{v}</div><div class="l">{l}</div></div>' for c, v, l in cells) + "</div>")

    # ---- topic breakdown
    by_topic = OrderedDict()
    for r in recs:
        t = by_topic.setdefault(r["topic"], [0, 0])
        t[1] += 1
        t[0] += r["status"] == "correct"
    rows = "".join(
        f'<div class="trow"><span>{H.escape(t)}</span><div class="tbar2"><i class="{"low" if c / n < .5 else ""}" style="width:{100 * c / n:.0f}%"></i></div>'
        f'<span class="fr">{c}/{n}</span></div>' for t, (c, n) in by_topic.items())
    weak = [t for t, (c, n) in by_topic.items() if c < n]
    tip = (f'<div class="rev" style="margin-top:6px">Revise: <b>{", ".join(H.escape(t) for t in weak)}</b></div>'
           if weak else '<div class="rev" style="margin-top:6px"><b class="good">Perfect round — every topic answered correctly.</b></div>')
    html(f'<div class="sec fu">Topic performance</div><div class="panel glass">{rows}{tip}</div>')

    # ---- leaderboard
    lb = load_leaderboard()[:10]
    body = []
    for i, r in enumerate(lb, 1):
        me = r["name"] == quiz["name"] and r["date"] == quiz.get("entry_date") and r["score"] == quiz["score"]
        medal = f'<span class="medal m{i if i <= 3 else 0}">{i}</span>'
        body.append(f'<tr class="{"me" if me else ""}"><td>{medal}</td><td>{H.escape(r["name"])}{" (you)" if me else ""}</td>'
                    f'<td class="sc">{r["score"]}</td><td>{r["accuracy"]:.0f}%</td><td>{H.escape(r["level"])}</td><td>{r["date"]}</td></tr>')
    html(f"""<div class="sec fu">Leaderboard</div><div class="panel glass"><table class="lb">
      <tr><th>Rank</th><th>Player</th><th>Score</th><th>Accuracy</th><th>Level</th><th>Date</th></tr>{"".join(body)}</table></div>""")

    # ---- answer review
    html('<div class="sec fu">Review your answers</div>')
    icon = {"correct": "✓", "wrong": "✗", "partial": "◐", "timeout": "⏱"}
    for n, r in enumerate(recs, 1):
        with st.expander(f'{icon[r["status"]]}  Q{n}.  {r["question"][:90]}{"…" if len(r["question"]) > 90 else ""}'):
            cls = "good" if r["status"] == "correct" else "badc"
            html(f'<div class="rev"><b>{H.escape(r["topic"])}</b> · {r["type"]} · {r["difficulty"]}<br>'
                 f'<b>Question:</b> {H.escape(r["question"])}<br>'
                 f'<b>Your answer:</b> <span class="{cls}">{H.escape(str(r["mine"]))}</span><br>'
                 f'<b>Correct answer:</b> <span class="good">{H.escape(r["correct_txt"])}</span><br>'
                 f'<b>Why:</b> {H.escape(r["explanation"])}<br><b>Points:</b> {r["points"]} · Time: {r["time"]}s</div>')

    # ---- actions
    st.write("")
    c1, c2 = st.columns(2)
    c1.button("Play again", key="again", type="primary", on_click=play_again, use_container_width=True)
    c2.button("Back to home", key="home_btn", on_click=go_home, use_container_width=True)
