"""
theme.py - shared look & feel (Neon Circuit Arena) used by every page.
Contains the base CSS (fonts, dark background, glass cards, orbs) and the animated
circuit-board background.
"""
import random

BASE_CSS = """<style>
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

/* ---------- shared hero text ---------- */
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

</style>"""


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


import streamlit as st


def html(block: str):
    """Render HTML safely: strip indentation/blank lines so Markdown never
    mistakes the block for a code fence."""
    clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


def page_frame():
    """Inject the shared CSS + animated background (call first on every page)."""
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    html(f'<div class="bgwrap">{circuit_background()}</div>')
