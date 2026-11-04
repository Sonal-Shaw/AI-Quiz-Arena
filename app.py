"""
AI QUIZ ARENA  -  Landing page  (Neon Circuit Arena theme)
DSC401-6 Artificial Intelligence | Units I & II | Christ University

Run:  streamlit run app.py

HOW TO PLUG IN YOUR EXISTING QUIZ
---------------------------------
* The landing page stores the player's choices in st.session_state:
      st.session_state.player_name   -> str
      st.session_state.difficulty    -> "All Levels" | "Easy" | "Medium" | "Hard"
* Clicking START QUIZ sets st.session_state.page = "quiz".
* Replace render_quiz() at the bottom with your own quiz code.
"""

import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from bank import load_bank
from quiz_page import render_quiz, new_round
from result_page import render_result

st.set_page_config(
    page_title="AI Quiz Arena",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
DIFFICULTIES = ["All Levels", "Easy", "Medium", "Hard"]
st.session_state.setdefault("page", "home")
st.session_state.setdefault("player_name", "")
st.session_state.setdefault("difficulty", "All Levels")


def start_quiz():
    name = st.session_state.player_name.strip() or "Player"
    new_round(st.session_state.difficulty, name)
    st.session_state.page = "quiz"


def go_home():
    st.session_state.page = "home"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def html(block: str):
    """Render HTML safely: strip indentation/blank lines so Markdown never
    mistakes the block for a code fence."""
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    st.html(clean)


def kf(name: str, start: float, hold_until: float) -> str:
    """Keyframes: off -> on at `start` -> stays lit -> fades after `hold_until`."""
    return (
        f"@keyframes {name}{{0%,{start:.1f}%{{opacity:0}}"
        f"{start + 1.5:.1f}%,{hold_until}%{{opacity:1}}"
        f"{hold_until + 4}%,100%{{opacity:0}}}}"
    )


# --------------------------------------------------------------------------
# Background: circuit board with travelling data pulses
# --------------------------------------------------------------------------
def circuit_background() -> str:
    rnd = random.Random(11)
    W, H = 1600, 900
    base, pads, pulses = [], [], []
    for i in range(18):
        x = rnd.randrange(0, W, 50)
        y = rnd.randrange(0, H, 50)
        pts = [(x, y)]
        horizontal = rnd.random() < 0.5
        for _ in range(rnd.randint(3, 6)):
            step = rnd.choice([-1, 1]) * rnd.randint(2, 7) * 50
            if horizontal:
                x = min(max(x + step, 0), W)
            else:
                y = min(max(y + step, 0), H)
            pts.append((x, y))
            horizontal = not horizontal
        d = "M" + " L".join(f"{a} {b}" for a, b in pts)
        base.append(f'<path d="{d}"/>')
        pads.append(
            f'<circle cx="{pts[0][0]}" cy="{pts[0][1]}" r="4"/>'
            f'<circle cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="7" class="ring"/>'
        )
        if i < 10:
            col = "pc" if i % 2 == 0 else "pm"
            pulses.append(
                f'<path d="{d}" class="pulse {col}" '
                f'style="animation-duration:{rnd.uniform(5, 9):.1f}s;'
                f'animation-delay:-{rnd.uniform(0, 8):.1f}s"/>'
            )
    return (
        '<div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>'
        '<svg class="circuit" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice">'
        f'<g class="cb">{"".join(base)}</g><g class="cp">{"".join(pads)}</g>{"".join(pulses)}</svg>'
    )


# --------------------------------------------------------------------------
# Hero graph: nodes light up in BFS order (cyan) then DFS order (violet)
# --------------------------------------------------------------------------
NODES = {
    "A": (500, 36), "B": (300, 110), "C": (700, 110),
    "D": (190, 184), "E": (410, 184), "F": (590, 184), "G": (810, 184),
    "H": (120, 258), "I": (260, 258), "J": (380, 258), "K": (860, 258),
}
EDGES = [("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"), ("C", "F"),
         ("C", "G"), ("D", "H"), ("D", "I"), ("E", "J"), ("G", "K")]
PARENT = {b: a for a, b in EDGES}
BFS_ORDER = list("ABCDEFGHIJK")
DFS_ORDER = list("ABDHIEJCFGK")


def graph_svg():
    """Return (svg_markup, keyframes_css)."""
    css, parts = [], ['<svg class="graph" viewBox="0 0 1000 300" preserveAspectRatio="xMidYMid meet">']
    for a, b in EDGES:  # dim base edges
        (x1, y1), (x2, y2) = NODES[a], NODES[b]
        parts.append(f'<line class="ge" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')

    plans = (("b", BFS_ORDER, "lb", 2.0, 44), ("d", DFS_ORDER, "ld", 52.0, 94))
    for kind, order, cls, t0, hold in plans:       # lit edges
        for idx, n in enumerate(order):
            css.append(kf(f"{kind}{n}", t0 + idx * 3.5, hold))
            if n == "A":
                continue
            (x1, y1), (x2, y2) = NODES[PARENT[n]], NODES[n]
            parts.append(
                f'<line class="{cls}e" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'style="animation:{kind}{n} 16s linear infinite"/>'
            )
    for n, (x, y) in NODES.items():                 # base nodes
        parts.append(f'<circle class="gn" cx="{x}" cy="{y}" r="10"/>')
    for kind, order, cls, t0, hold in plans:       # lit nodes
        for n in order:
            x, y = NODES[n]
            parts.append(
                f'<circle class="{cls}n" cx="{x}" cy="{y}" r="10" '
                f'style="animation:{kind}{n} 16s linear infinite"/>'
            )
    parts.append("</svg>")
    return "".join(parts), "".join(css)


GRAPH_SVG, GRAPH_CSS = graph_svg()

# --------------------------------------------------------------------------
# Icons (inline SVG, 24x24, stroke = currentColor)
# --------------------------------------------------------------------------
def svg(inner: str) -> str:
    return (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )


IC = {
    "q": svg('<circle cx="12" cy="12" r="9.5"/><path d="M9.2 9.2a2.9 2.9 0 1 1 4.1 2.6c-.8.4-1.3 1-1.3 1.8"/><circle cx="12" cy="17.2" r=".7"/>'),
    "topics": svg('<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8.3 7.3 11 15.7M15.7 7.3 13 15.7M8.5 6h7"/>'),
    "layers": svg('<path d="M12 3 3 8l9 5 9-5-9-5Z"/><path d="m3 13 9 5 9-5"/>'),
    "bars": svg('<path d="M5 20v-6M12 20V9M19 20V4"/>'),
    "chip": svg('<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>'),
    "search": svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>'),
    "globe": svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>'),
}

# Custom component for the difficulty cards (works on any Streamlit version)
mode_selector = components.declare_component(
    "mode_selector", path=str(Path(__file__).parent / "mode_selector")
)


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Sora:wght@400;600;700&display=swap');

@property --n { syntax: '<integer>'; inherits: false; initial-value: 0; }

/* ---------- streamlit chrome off + page frame ---------- */
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton, [data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
html, body, .stApp { background: #050714 !important; }
.stApp {
  background:
    radial-gradient(1200px 700px at 50% -10%, #12163f 0%, transparent 60%),
    radial-gradient(900px 600px at 100% 100%, #1a0b33 0%, transparent 60%),
    #050714 !important;
  font-family: 'Sora', sans-serif; color: #B6C2E2;
}
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background: transparent !important; }
.block-container { max-width: 1100px !important; padding: 28px 20px 48px !important; position: relative; z-index: 1; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stElementContainer"], .element-container { margin: 0 !important; }

/* ---------- background layers ---------- */
.orb { position: fixed; border-radius: 50%; filter: blur(110px); opacity: .35; z-index: 0; pointer-events: none; }
.o1 { width: 520px; height: 520px; background: #22d3ee; top: -160px; left: -140px; animation: drift1 26s ease-in-out infinite alternate; }
.o2 { width: 560px; height: 560px; background: #8b5cf6; top: 25%; right: -200px; animation: drift2 32s ease-in-out infinite alternate; }
.o3 { width: 480px; height: 480px; background: #ec4899; bottom: -200px; left: 25%; opacity: .22; animation: drift1 38s ease-in-out infinite alternate-reverse; }
@keyframes drift1 { to { transform: translate(120px, 90px); } }
@keyframes drift2 { to { transform: translate(-140px, 60px); } }
.circuit { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
.cb path { fill: none; stroke: #7dd3fc; stroke-width: 1.3; opacity: .10; }
.cp circle { fill: #7dd3fc; opacity: .14; }
.cp .ring { fill: none; stroke: #7dd3fc; stroke-width: 1.2; }
.pulse { fill: none; stroke-width: 2.6; stroke-linecap: round; stroke-dasharray: 46 6000; opacity: .85; animation: pulse linear infinite; }
.pc { stroke: #22d3ee; filter: drop-shadow(0 0 5px #22d3ee); }
.pm { stroke: #ec4899; filter: drop-shadow(0 0 5px #ec4899); }
@keyframes pulse { from { stroke-dashoffset: 46; } to { stroke-dashoffset: -1800; } }

/* ---------- shared surfaces ---------- */
.glass { position: relative; background: rgba(255,255,255,.045); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-radius: 20px; box-shadow: 0 10px 40px rgba(34,211,238,.06), 0 4px 24px rgba(139,92,246,.10); }
.glass::before { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1px; pointer-events: none;
  background: linear-gradient(135deg, rgba(34,211,238,.65), rgba(139,92,246,.28) 50%, rgba(236,72,153,.55));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); mask-composite: exclude; }
.fu { animation: fadeUp .8s cubic-bezier(.2,.7,.2,1) backwards; animation-delay: calc(var(--i, 0) * .1s); }
@keyframes fadeUp { from { opacity: 0; transform: translateY(22px); } }
.nt { position: absolute; width: 34px; height: 34px; pointer-events: none; z-index: 2; }
.nt.a { top: 14px; left: 14px; border-top: 2px solid #22d3ee; border-left: 2px solid #22d3ee; border-radius: 10px 0 0 0; filter: drop-shadow(0 0 6px #22d3ee); }
.nt.b { bottom: 14px; right: 14px; border-bottom: 2px solid #ec4899; border-right: 2px solid #ec4899; border-radius: 0 0 10px 0; filter: drop-shadow(0 0 6px #ec4899); }

/* ---------- hero ---------- */
.hero { overflow: hidden; text-align: center; padding: 40px 24px 36px; }
.graph { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .30; z-index: 0; }
.ge { stroke: rgba(165,180,252,.55); stroke-width: 1.4; }
.gn { fill: #0a0f2c; stroke: rgba(165,180,252,.7); stroke-width: 1.6; }
.lbe, .lde { stroke-width: 2.6; opacity: 0; }
.lbe { stroke: #22d3ee; filter: drop-shadow(0 0 6px #22d3ee); }
.lde { stroke: #a78bfa; filter: drop-shadow(0 0 6px #a78bfa); }
.lbn, .ldn { opacity: 0; }
.lbn { fill: #22d3ee; filter: drop-shadow(0 0 10px #22d3ee); }
.ldn { fill: #a78bfa; filter: drop-shadow(0 0 10px #a78bfa); }
.hero-in { position: relative; z-index: 1; }
.badge { display: inline-block; padding: 8px 20px; border-radius: 999px; font-size: .85rem; font-weight: 700; letter-spacing: 2.5px;
  color: #67e8f9; background: rgba(34,211,238,.08); border: 1px solid rgba(34,211,238,.55); animation: badgeGlow 3s ease-in-out infinite; }
@keyframes badgeGlow { 0%,100% { box-shadow: 0 0 10px rgba(34,211,238,.25); } 50% { box-shadow: 0 0 22px rgba(34,211,238,.6); } }
.title {
  font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: clamp(2.6rem, 6vw, 4.5rem); letter-spacing: 3px; line-height: 1.1; margin: 22px 0 10px;
  background: linear-gradient(105deg, transparent 42%, rgba(255,255,255,.95) 50%, transparent 58%),
              linear-gradient(90deg, #ffffff 0%, #67e8f9 35%, #a78bfa 70%, #f0abfc 100%);
  background-size: 250% 100%, 100% 100%; background-repeat: no-repeat; background-position: 100% 0, 0 0;
  -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent;
  animation: glowPulse 3s ease-in-out infinite, shine 6s ease-in-out infinite, flicker 1.6s linear 1; }
@keyframes glowPulse {
  0%,100% { filter: drop-shadow(0 0 8px rgba(34,211,238,.55)) drop-shadow(0 0 24px rgba(139,92,246,.45)) drop-shadow(0 0 48px rgba(236,72,153,.25)); }
  50%     { filter: drop-shadow(0 0 14px rgba(34,211,238,.95)) drop-shadow(0 0 40px rgba(139,92,246,.7)) drop-shadow(0 0 80px rgba(236,72,153,.45)); } }
@keyframes shine { 0%,55% { background-position: 100% 0, 0 0; } 100% { background-position: 0% 0, 0 0; } }
@keyframes flicker { 0%{opacity:0} 8%{opacity:1} 12%{opacity:.2} 18%{opacity:1} 24%{opacity:.4} 30%,100%{opacity:1} }
.sub { font-size: 1.15rem; color: #cdd7f5; }
.divider { position: relative; overflow: hidden; height: 2px; width: min(420px, 70%); margin: 22px auto 0;
  background: linear-gradient(90deg, transparent, #22d3ee, #8b5cf6, #ec4899, transparent); }
.divider::after { content: ""; position: absolute; top: 0; left: -30%; width: 30%; height: 100%;
  background: linear-gradient(90deg, transparent, #fff, transparent); animation: travel 3s linear infinite; }
@keyframes travel { to { left: 100%; } }

/* ---------- grids ---------- */
.grid { display: grid; gap: 20px; align-items: stretch; }
.g4 { grid-template-columns: repeat(4, 1fr); }
.g3 { grid-template-columns: repeat(3, 1fr); }

/* stats */
.stat { padding: 24px 16px; text-align: center; transition: transform .3s, box-shadow .3s; }
.stat:hover { transform: translateY(-6px); box-shadow: 0 14px 50px rgba(34,211,238,.22), 0 4px 28px rgba(139,92,246,.25); }
.ico { width: 46px; height: 46px; border-radius: 14px; display: grid; place-items: center; margin: 0 auto 12px;
  color: rgb(var(--c)); background: rgba(var(--c), .12); border: 1px solid rgba(var(--c), .38); }
.num { font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 2.2rem; line-height: 1.2;
  background: linear-gradient(90deg, #67e8f9, #a78bfa, #f0abfc); -webkit-background-clip: text; background-clip: text; color: transparent;
  counter-reset: n var(--n); animation: cnt 1.8s ease-out backwards; }
.num::after { content: counter(n); }
@keyframes cnt { from { --n: 0; } }
.lbl { margin-top: 6px; font-size: .95rem; color: #B6C2E2; }

/* section headings (centred) */
.sec { display: flex; align-items: center; justify-content: center; gap: 18px; margin: 68px 0 10px; text-align: center;
  font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: clamp(1.5rem, 3.2vw, 2.1rem); letter-spacing: 2px; color: #fff; text-transform: uppercase;
  text-shadow: 0 0 18px rgba(34,211,238,.45); }
.sec::before, .sec::after { content: ""; flex: 0 1 90px; height: 2px; border-radius: 2px; }
.sec::before { background: linear-gradient(90deg, transparent, #22d3ee); box-shadow: 0 0 10px rgba(34,211,238,.7); }
.sec::after { background: linear-gradient(90deg, #ec4899, transparent); box-shadow: 0 0 10px rgba(236,72,153,.7); }
.hint { margin: 0 0 28px; text-align: center; font-size: 1.1rem; color: #aab9df; }

/* feature cards */
.feat { padding: 32px 26px; text-align: center; transition: transform .3s, box-shadow .3s; }
.feat:hover { transform: translateY(-6px); box-shadow: 0 14px 50px rgba(139,92,246,.28); }
.feat .ico { width: 56px; height: 56px; margin: 0 auto 18px; }
.feat h3 { margin: 0 0 10px; padding: 0; font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.3rem; color: #fff; }
.feat p { margin: 0; font-size: 1.02rem; line-height: 1.65; color: #B6C2E2; }

/* feature chips: 6 equal tiles */
.g6 { grid-template-columns: repeat(6, 1fr); gap: 14px; margin-top: 24px; }
.chip { display: flex; align-items: center; justify-content: center; gap: 9px; padding: 14px 10px; border-radius: 14px; white-space: nowrap;
  font-size: .95rem; font-weight: 600; color: #e4ebff; background: rgba(255,255,255,.045); border: 1px solid rgba(125,211,252,.22);
  transition: transform .25s, border-color .25s, box-shadow .25s; }
.chip:hover { transform: translateY(-3px); border-color: rgba(34,211,238,.7); box-shadow: 0 0 18px rgba(34,211,238,.3); }
.chip::before { content: ""; flex: none; width: 8px; height: 8px; border-radius: 50%; background: #22d3ee; box-shadow: 0 0 8px #22d3ee; }

/* topic panels */
.g2 { grid-template-columns: repeat(2, 1fr); }
.unit { padding: 30px 24px 32px; text-align: center; }
.unit h3 { margin: 0 0 4px; padding: 0; display: flex; align-items: center; justify-content: center; gap: 10px;
  font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 1.3rem; letter-spacing: 1.5px; color: #fff; }
.unit h3 i { width: 11px; height: 11px; border-radius: 50%; background: rgb(var(--c)); box-shadow: 0 0 12px rgb(var(--c)); }
.unit .usub { margin-bottom: 22px; font-size: 1rem; color: #aab9df; }
.tags { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
.tag { padding: 10px 17px; border-radius: 999px; font-size: .98rem; font-weight: 600; color: #e4ebff; background: rgba(255,255,255,.04);
  border: 1px solid rgba(var(--c), .5); transition: transform .25s, box-shadow .25s, background .25s; cursor: default; }
.tag:hover { transform: translateY(-3px); background: rgba(var(--c), .14); box-shadow: 0 0 20px rgba(var(--c), .5); }
.u1 { --c: 34,211,238; } .u2 { --c: 167,139,250; }

.foot { margin-top: 48px; text-align: center; font-size: .9rem; color: #7f8db3; }

/* ---------- streamlit widgets ---------- */
div[data-testid="stTextInput"] div[data-baseweb="input"], div[data-testid="stTextInput"] div[data-baseweb="base-input"] { background: transparent !important; }
div[data-testid="stTextInput"] div[data-baseweb="input"] {
  background: rgba(255,255,255,.05) !important; border: 1px solid rgba(125,211,252,.28) !important; border-radius: 14px !important; transition: all .25s; }
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within { border-color: #22d3ee !important;
  box-shadow: 0 0 0 3px rgba(34,211,238,.18), 0 0 26px rgba(34,211,238,.32) !important; }
div[data-testid="stTextInput"] input { color: #fff !important; font-family: 'Sora', sans-serif !important; font-size: 1.25rem !important;
  font-weight: 600 !important; text-align: center !important; padding: 18px 20px !important; height: 64px !important; background: transparent !important; }
div[data-testid="stTextInput"] input::placeholder { color: #8a9bc6 !important; font-weight: 400 !important; text-align: center !important; }

/* start button */
div.stButton { margin-top: 64px; }
div.stButton > button, div.stButton > button[kind] {
  position: relative; overflow: hidden; width: 100%; height: 64px; border: none !important; border-radius: 999px;
  background: linear-gradient(90deg, #22d3ee, #8b5cf6 55%, #ec4899) !important; color: #fff !important;
  box-shadow: 0 0 22px rgba(34,211,238,.45), 0 0 50px rgba(139,92,246,.35); animation: btnPulse 2.4s ease-in-out infinite;
  transition: transform .25s, box-shadow .25s; }
div.stButton > button p { font-family: 'Orbitron', sans-serif; font-size: 1.2rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; color: #fff !important; }
div.stButton > button::after { content: ""; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
  background: linear-gradient(100deg, transparent, rgba(255,255,255,.5), transparent); transform: skewX(-20deg); animation: sweep 3.2s ease-in-out infinite; }
div.stButton > button:hover { transform: scale(1.02); color: #fff !important; box-shadow: 0 0 34px rgba(34,211,238,.8), 0 0 80px rgba(236,72,153,.55); }
div.stButton > button:active { transform: scale(.98); }
div.stButton > button:focus-visible { outline: 3px solid #fff; outline-offset: 3px; }
@keyframes btnPulse { 0%,100% { box-shadow: 0 0 22px rgba(34,211,238,.45), 0 0 50px rgba(139,92,246,.35); }
                      50% { box-shadow: 0 0 34px rgba(34,211,238,.75), 0 0 80px rgba(236,72,153,.5); } }
@keyframes sweep { 0% { left: -60%; } 55%,100% { left: 130%; } }

/* ---------- graph keyframes (generated) ---------- */
__GRAPH_CSS__

/* ---------- responsive ---------- */
@media (max-width: 900px) {
  .g4 { grid-template-columns: repeat(2, 1fr); } .g3, .g2 { grid-template-columns: 1fr; } .g6 { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 600px) {
  .block-container { padding: 16px 12px 40px !important; }
  .hero { padding: 32px 14px 28px; } .badge { letter-spacing: 1.5px; font-size: .8rem; }
  .grid { gap: 14px; } .g6 { grid-template-columns: repeat(2, 1fr); }
  .sec { font-size: 1.25rem; margin-top: 48px; gap: 10px; } .sec::before, .sec::after { flex-basis: 30px; } .sub { font-size: 1rem; }
  div.stButton > button p { font-size: 1rem; letter-spacing: 2px; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""


# --------------------------------------------------------------------------
# Home page
# --------------------------------------------------------------------------
def render_home():
    st.html(
        CSS.replace("__GRAPH_CSS__", GRAPH_CSS)
    )

    html(f'<div class="bgwrap">{circuit_background()}</div>')

    # 1. HERO
    html(f"""
    <div class="hero glass fu" style="--i:0">
      <i class="nt a"></i><i class="nt b"></i>
      {GRAPH_SVG}
      <div class="hero-in">
        <span class="badge">CHRIST UNIVERSITY • DATA SCIENCE</span>
        <div class="title">AI QUIZ ARENA</div>
        <div class="sub">Master Artificial Intelligence — Units I &amp; II</div>
        <div class="divider"></div>
      </div>
    </div>
    """)

    # 2. STATS
    stats = [("34,211,238", IC["q"], len(load_bank()), "Questions"),     # live count from the Excel bank
             ("167,139,250", IC["topics"], 20, "AI Topics"),
             ("236,72,153", IC["layers"], 7, "Question Formats"),
             ("251,191,36", IC["bars"], 3, "Difficulty Levels")]
    cards = "".join(
        f'<div class="stat glass"><div class="ico" style="--c:{c}">{ic}</div>'
        f'<div class="num" style="--n:{n}"></div><div class="lbl">{lbl}</div></div>'
        for c, ic, n, lbl in stats
    )
    html(f'<div style="padding-top:28px"><div class="grid g4 fu" style="--i:1">{cards}</div></div>')

    # 3. PLAYER
    html('<div class="sec fu" style="--i:2">Player</div>'
         '<div class="hint">Your name appears on the leaderboard.</div>')
    st.text_input("Player name", key="player_name", max_chars=30,
                  placeholder="Enter your name to join the leaderboard",
                  label_visibility="collapsed")

    # 4. MODE  (custom component -> 4 equal clickable cards)
    html('<div class="sec fu" style="--i:3">Choose your mode</div>'
         '<div class="hint">Pick a difficulty and start your challenge.</div>')
    choice = mode_selector(selected=st.session_state.difficulty,
                           default=st.session_state.difficulty, key="mode_sel")
    if choice in DIFFICULTIES:
        st.session_state.difficulty = choice

    # 5. WHAT'S INSIDE
    feats = [("34,211,238", IC["chip"], "AI Concepts",
              "Agents, environments, the Turing Test and the foundations of AI."),
             ("167,139,250", IC["search"], "Search Problems",
              "BFS, DFS, heuristic search, hill climbing and CSP puzzles."),
             ("236,72,153", IC["globe"], "Real-World Scenarios",
              "Application-based questions on how AI is used in everyday life.")]
    fcards = "".join(
        f'<div class="feat glass"><div class="ico" style="--c:{c}">{ic}</div>'
        f'<h3>{t}</h3><p>{d}</p></div>'
        for c, ic, t, d in feats
    )
    chips = "".join(f'<div class="chip">{c}</div>' for c in
                    ["Timer", "Hints", "50-50 Lifeline", "Skip", "Progress Bar", "Leaderboard"])
    html(f"""
    <div class="sec fu" style="--i:4">What's inside</div>
    <div class="hint">Seven question formats across Units I and II.</div>
    <div class="grid g3 fu" style="--i:5">{fcards}</div>
    <div class="grid g6 fu" style="--i:6">{chips}</div>
    """)

    # 6. TOPICS  (two equal panels, one per unit)
    unit1 = ["Turing Test", "Rational Agents", "Intelligent Agents", "Agents &amp; Environments",
             "Good Behaviour", "Nature of Environments", "Problem Spaces",
             "State Space Search", "Production Systems"]
    unit2 = ["BFS", "DFS", "Iterative Deepening", "Hill Climbing", "Heuristic Search",
             "Best First Search", "CSP", "Means-End Analysis"]
    t1 = "".join(f'<span class="tag u1">{t}</span>' for t in unit1)
    t2 = "".join(f'<span class="tag u2">{t}</span>' for t in unit2)
    html(f"""
    <div class="sec fu" style="--i:7">Topics</div>
    <div class="hint">Everything you will be tested on.</div>
    <div class="grid g2 fu" style="--i:8">
      <div class="unit glass" style="--c:34,211,238">
        <h3><i></i>Unit I</h3><div class="usub">Foundations, agents &amp; problem spaces</div>
        <div class="tags">{t1}</div>
      </div>
      <div class="unit glass" style="--c:167,139,250">
        <h3><i></i>Unit II</h3><div class="usub">Search &amp; heuristic techniques</div>
        <div class="tags">{t2}</div>
      </div>
    </div>
    """)

    # 7. START
    st.button("Start quiz  →", on_click=start_quiz, use_container_width=True)

    # 8. FOOTER
    html('<div class="foot">Built with Streamlit • DSC401-6 Artificial Intelligence</div>')


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "quiz":
    render_quiz()
else:
    render_result()
