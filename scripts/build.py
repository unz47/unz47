#!/usr/bin/env python3
"""Build the animated SVG cards shown in the profile README.

Every card is a standalone SVG: GitHub renders README images through <img>,
so animation is CSS inside the SVG and nothing may load from outside.

Run:  python3 scripts/build.py   (writes assets/*.svg)
"""

from html import escape
from pathlib import Path

from mochi import FRAMES

ASSETS = Path(__file__).resolve().parent.parent / "assets"

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Sans','Yu Gothic UI',"
        "'Noto Sans JP',Helvetica,Arial,sans-serif")

BG = "#0e1218"
PANEL = "#151a23"
LINE = "#262d3b"
TEXT = "#e7eaf0"
MUTED = "#8b94a7"
DIM = "#3a4252"
LEAF = "#8bd17c"
AMBER = "#f5b85a"
MOCHI_COLORS = {"o": "#282830", "w": "#faf9f5"}

# .ap fades in at its own delay; .cv covers typed text until it is typed;
# .cy is one frame of an n-frame cycle (see cycle()).
BASE_CSS = """
.ap{opacity:0;animation:ap .01s linear forwards}
@keyframes ap{to{opacity:1}}
@keyframes hd{to{opacity:0}}
@keyframes bl{50%{opacity:0}}
.cy{opacity:0}
""" + "".join(f"@keyframes cy{n}{{0%{{opacity:1}}{100 / n:.3f}%{{opacity:0}}}}\n" for n in range(2, 7)) + """
@media (prefers-reduced-motion:reduce){
  *{animation:none!important}
  .ap{opacity:1}.cv{display:none}.cy:first-child{opacity:1}
}
"""

SHADOW = ('<filter id="shadow" x="-20%" y="-20%" width="140%" height="170%">'
          '<feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000" flood-opacity=".45"/>'
          "</filter>")


def svg(name: str, w: int, h: int, title: str, css: str, body: str) -> None:
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">\n'
           f"<title>{escape(title)}</title>\n<style>{css}{BASE_CSS}</style>\n{body}\n</svg>\n")
    (ASSETS / name).write_text(doc)


def t(x, y, s, fill=TEXT, size=13, family=SANS, **attrs) -> str:
    """A <text>. Keyword args become attributes (underscores turn into dashes)."""
    extra = "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-family="{family}"{extra}>{escape(s)}</text>')


def ap(delay, inner) -> str:
    return f'<g class="ap" style="animation-delay:{delay:.2f}s">{inner}</g>'


def cycle(frames, period) -> str:
    """Show each frame for an equal share of `period`, in order, forever.

    Wrap the result in its own <g> so reduced motion can keep the first frame.
    """
    n = len(frames)
    return "".join(f'<g class="cy" style="animation:cy{n} {period}s step-end '
                   f'{(k - n) * period / n:.3f}s infinite">{f}</g>' for k, f in enumerate(frames))


def pixels(grid, colors, scale) -> str:
    """One pixel-art frame as row runs of rects."""
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            run = 1
            while x + run < len(row) and row[x + run] == row[x]:
                run += 1
            if row[x] in colors:
                out.append(f'<rect x="{x * scale}" y="{y * scale}" width="{run * scale}" '
                           f'height="{scale}" fill="{colors[row[x]]}"/>')
            x += run
    return "".join(out)


def mochi(x, y, scale, colors=MOCHI_COLORS) -> str:
    """Mochi running in place."""
    frames = cycle([pixels(f, colors, scale) for f in FRAMES], 0.6)
    return f'<g transform="translate({x} {y})" shape-rendering="crispEdges">{frames}</g>'


# --- header: a terminal that types `whoami` --------------------------------

CELL = 9  # monospace cell width at 15px; textLength pins every font to it


def typed(x, y, s, show, start, end, key) -> tuple[str, str]:
    """Text revealed one cell at a time by a cursor that pushes a cover off it."""
    n, w = len(s), len(s) * CELL
    css = f"@keyframes {key}{{to{{transform:translateX({w}px)}}}}"
    body = ap(show, t(x, y, s, size=15, family=MONO, textLength=w, lengthAdjust="spacing")
              + f'<g class="cv" style="animation:{key} {n / 11:.2f}s steps({n}) {start}s forwards,'
              f'hd .01s {end}s forwards">'
              f'<rect x="{x}" y="{y - 15}" width="{w + CELL}" height="21" fill="{BG}"/>'
              f'<rect x="{x}" y="{y - 13}" width="{CELL}" height="17" fill="{LEAF}"/></g>')
    return css, body


def prompt(x, y) -> str:
    return t(x, y, "~", LEAF, 15, MONO, font_weight="bold") + t(x + 2 * CELL, y, "$", MUTED, 15, MONO)


def out_line(x, y, *parts) -> str:
    """One terminal line made of (text, color) runs."""
    spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in parts)
    n = sum(len(s) for s, _ in parts)
    return (f'<text x="{x}" y="{y}" font-size="15" font-family="{MONO}" '
            f'textLength="{n * CELL}" lengthAdjust="spacing">{spans}</text>')


def header() -> None:
    w, h, x = 800, 240, 26
    cmd_x = x + 4 * CELL
    css1, line1 = typed(cmd_x, 72, "whoami", 0, 0.5, 1.4, "ty1")
    css3, line3 = typed(cmd_x, 132, "cat about.txt", 1.7, 1.9, 3.3, "ty3")
    css = css1 + css3 + """
.dash{animation:dash .6s linear infinite}
@keyframes dash{to{stroke-dashoffset:16}}
.xp{animation:xp 1.8s ease-out infinite}
@keyframes xp{0%{opacity:0;transform:translateY(0)}15%{opacity:1}70%{opacity:1}
100%{opacity:0;transform:translateY(-26px)}}
.blink{animation:bl 1s steps(1) infinite}
"""
    body = f"""
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{LINE}"/>
<path d="M.5 36V12.5A12 12 0 0 1 12.5 .5H{w - 12.5}A12 12 0 0 1 {w - .5} 12.5V36Z" fill="{PANEL}"/>
<line x1=".5" y1="36" x2="{w - .5}" y2="36" stroke="{LINE}"/>
<circle cx="22" cy="18" r="6" fill="#ff5f57"/><circle cx="42" cy="18" r="6" fill="#febc2e"/>
<circle cx="62" cy="18" r="6" fill="#28c840"/>
{t(w / 2, 23, "s@i — ~/profile — zsh", MUTED, 12, text_anchor="middle")}
{prompt(x, 72)}{line1}
{ap(1.4, out_line(x, 98, ("s@i", AMBER), (" · full-stack engineer · tokyo", TEXT)))}
{ap(1.7, prompt(x, 132))}{line3}
{ap(3.3, out_line(x, 158, ("I build web & mobile apps with TypeScript,", TEXT)))}
{ap(3.4, out_line(x, 184, ("run ML models in the browser, and make things move.", TEXT)))}
{ap(3.6, prompt(x, 218) + f'<rect class="blink" x="{cmd_x}" y="205" width="{CELL}" height="17" fill="{LEAF}"/>')}
<defs><linearGradient id="fade" x1="560" x2="780" gradientUnits="userSpaceOnUse">
<stop offset="0" stop-color="{DIM}" stop-opacity="0"/><stop offset=".5" stop-color="{DIM}"/>
<stop offset="1" stop-color="{DIM}" stop-opacity="0"/></linearGradient></defs>
<line class="dash" x1="560" y1="200" x2="780" y2="200" stroke="url(#fade)" stroke-width="3"
 stroke-dasharray="6 10"/>
{mochi(630, 118, 5)}
<g class="xp">{t(712, 116, "+1 XP", LEAF, 12, MONO, font_weight="bold")}</g>
"""
    svg("header.svg", w, h, "$ whoami — s@i, full-stack engineer in Tokyo", css, body)


# --- now: the Desk Buddy tray menu, opened ---------------------------------

NOW = [
    ("Desk Buddy", "a tray pet that levels up with your CPU", "Rust · Tauri"),
    ("shaders-art", "a museum of fragment shaders", "GLSL · TS"),
    ("RSNA Knee MRI", "Kaggle · weakly-supervised multi-label", "Python"),
]


def now() -> None:
    w, h = 800, 320
    mx, mw = 404, 380  # dropdown
    row_h, first = 46, 128
    xp_w = mw - 28
    css = f"""
.b1{{animation:drift 14s ease-in-out infinite alternate}}
.b2{{animation:drift 17s ease-in-out -6s infinite alternate-reverse}}
@keyframes drift{{to{{transform:translate(70px,-36px)}}}}
.xpbar{{transform-box:fill-box;transform-origin:left center;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) .4s both}}
@keyframes grow{{from{{transform:scaleX(0)}}}}
.hl{{animation:hl 6s step-end infinite}}
@keyframes hl{{33.333%{{transform:translateY({row_h}px)}}66.667%{{transform:translateY({2 * row_h}px)}}}}
"""
    items = []
    for i, (name, sub, tag) in enumerate(NOW):
        top = first + i * row_h
        items.append(t(mx + 16, top + 20, name, TEXT, 13.5, font_weight="600")
                     + t(mx + 16, top + 37, sub, MUTED, 11.5)
                     + t(mx + mw - 16, top + 20, tag, MUTED, 11, MONO, text_anchor="end"))
    cpu = cycle([t(mx + 16, 92, f"CPU {p}%", MUTED, 12.5) for p in (23, 41, 17)], 3)
    body = f"""
<defs>
<clipPath id="card"><rect width="{w}" height="{h}" rx="12"/></clipPath>
<radialGradient id="g1"><stop offset="0" stop-color="#1f6b55" stop-opacity=".75"/>
<stop offset="1" stop-color="#1f6b55" stop-opacity="0"/></radialGradient>
<radialGradient id="g2"><stop offset="0" stop-color="#47358a" stop-opacity=".7"/>
<stop offset="1" stop-color="#47358a" stop-opacity="0"/></radialGradient>
{SHADOW}
</defs>
<g clip-path="url(#card)">
<rect width="{w}" height="{h}" fill="#0c0f17"/>
<circle class="b1" cx="150" cy="250" r="240" fill="url(#g1)"/>
<circle class="b2" cx="440" cy="60" r="230" fill="url(#g2)"/>
<rect width="{w}" height="28" fill="#0b0e14" fill-opacity=".72"/>
<line x1="0" y1="28.5" x2="{w}" y2="28.5" stroke="#ffffff" stroke-opacity=".06"/>
{t(18, 19, "Now", TEXT, 13, font_weight="bold")}
{t(54, 19, "what's on my desk", MUTED, 12.5)}
<rect x="706" y="4" width="30" height="20" rx="5" fill="#ffffff" fill-opacity=".16"/>
{mochi(713, 6, 1, {"w": TEXT})}
{t(784, 19, "Tokyo", TEXT, 12.5, text_anchor="end")}
{t(20, h - 18, "~/now", MUTED, 12, MONO)}
</g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{LINE}"/>
<g filter="url(#shadow)">
<rect x="{mx}" y="34" width="{mw}" height="{h - 50}" rx="10" fill="#1a1f2a" fill-opacity=".96"
 stroke="#323b4c"/>
</g>
{t(mx + 16, 57, "Lv 3", TEXT, 12.5, font_weight="bold")}
{t(mx + 50, 57, "(1,204 / 3,118 XP)", MUTED, 12.5)}
<rect x="{mx + 14}" y="65" width="{xp_w}" height="4" rx="2" fill="{DIM}"/>
<rect class="xpbar" x="{mx + 14}" y="65" width="{xp_w * 1204 / 3118:.1f}" height="4" rx="2" fill="{LEAF}"/>
<g>{cpu}</g>
<line x1="{mx + 10}" y1="104.5" x2="{mx + mw - 10}" y2="104.5" stroke="#ffffff" stroke-opacity=".08"/>
{t(mx + 16, 122, "NOW BUILDING", MUTED, 10.5, font_weight="bold", letter_spacing="1")}
<rect class="hl" x="{mx + 6}" y="{first + 1}" width="{mw - 12}" height="{row_h - 2}" rx="6"
 fill="{LEAF}" fill-opacity=".14"/>
{"".join(items)}
<line x1="{mx + 10}" y1="{first + 3 * row_h + 4.5}" x2="{mx + mw - 10}" y2="{first + 3 * row_h + 4.5}"
 stroke="#ffffff" stroke-opacity=".08"/>
{t(mx + 16, first + 3 * row_h + 27, "Quit", DIM, 12.5)}
{t(mx + mw - 16, first + 3 * row_h + 27, "not yet", DIM, 11, MONO, text_anchor="end")}
"""
    title = "Now: " + "; ".join(f"{n} — {s} ({tag})" for n, s, tag in NOW)
    svg("now.svg", w, h, title, css, body)


# --- stack: an RPG status window -------------------------------------------

STACK = [
    ("FRONTEND", 9, "TypeScript · Angular · React / Next.js · Ionic"),
    ("MOBILE", 6, "Swift · Kotlin · React Native (Expo)"),
    ("BACKEND", 7, "NestJS · AWS Serverless (Lambda, DynamoDB) · Vercel"),
    ("ML", 6, "Kaggle · NLP / BERT · ML on the web"),
    ("CREATIVE", 5, "Three.js · p5.js · GLSL · Blender"),
    ("SYSTEMS", 4, "Rust · Tauri · Effect-TS · WebRTC"),
]


def stack() -> None:
    w, h = 800, 340
    ink = "#07090d"
    row_h, top, lx = 46, 40, 240
    n = len(STACK)
    stops = "".join(f"{100 * i / n:.3f}%{{transform:translateY({i * row_h}px)}}" for i in range(1, n))
    css = f"""
.cur{{animation:cur {n * 1.6}s step-end infinite}}
@keyframes cur{{{stops}}}
.blink{{animation:bl .8s steps(1) infinite}}
.dash{{animation:dash .6s linear infinite}}
@keyframes dash{{to{{stroke-dashoffset:16}}}}
"""
    rows = []
    for i, (label, level, skills) in enumerate(STACK):
        y = top + i * row_h
        segs = []
        for j in range(10):
            sx = 360 + j * 17
            segs.append(f'<rect x="{sx + .5}" y="{y + 6.5}" width="13" height="9" fill="none" '
                        f'stroke="{DIM}"/>')
            if j < level:
                segs.append(ap(.4 + i * .15 + j * .05,
                               f'<rect x="{sx}" y="{y + 6}" width="14" height="10" fill="{LEAF}"/>'))
        rows.append(t(lx, y + 16, label, AMBER, 13, MONO, font_weight="bold", letter_spacing="1")
                    + "".join(segs) + t(lx, y + 36, skills, TEXT, 13))
    info = "".join(t(36, y, k, MUTED, 13, MONO) + t(96, y, v, TEXT, 13, MONO)
                   for y, (k, v) in zip((206, 232, 258),
                                        (("NAME", "s@i"), ("CLASS", "Full-stack"), ("BASE", "Tokyo"))))
    body = f"""
<rect x="9.5" y="12.5" width="{w - 19}" height="{h - 22}" rx="10" fill="{ink}" stroke="{TEXT}"
 stroke-width="3"/>
<rect x="16.5" y="19.5" width="{w - 33}" height="{h - 36}" rx="6" fill="none" stroke="{TEXT}"
 stroke-opacity=".22"/>
<rect x="30" y="3" width="84" height="20" fill="{ink}"/>
{t(38, 18, "STATUS", TEXT, 13, MONO, font_weight="bold", letter_spacing="2")}
<rect x="36.5" y="42.5" width="132" height="132" rx="6" fill="{BG}" stroke="{LINE}"/>
<line class="dash" x1="44" y1="157" x2="162" y2="157" stroke="{DIM}" stroke-width="3"
 stroke-dasharray="6 10"/>
{mochi(54, 59, 6)}
{info}
<line x1="196.5" y1="40" x2="196.5" y2="{h - 34}" stroke="{TEXT}" stroke-opacity=".12"/>
<g class="cur"><path class="blink" d="M{lx - 20} {top + 5}l9 6-9 6z" fill="{TEXT}"/></g>
{"".join(rows)}
<path class="blink" d="M{w - 44} {h - 30}h12l-6 7z" fill="{AMBER}"/>
"""
    title = "Stack — " + "; ".join(f"{label.title()}: {skills}" for label, _, skills in STACK)
    svg("stack.svg", w, h, title, css, body)


# --- achievements: unlock toasts ---------------------------------------------

ACHIEVEMENTS = [
    ("AWS Certified Solutions Architect – Professional", "Amazon Web Services", "AWS"),
    ("JDLA Deep Learning for ENGINEER", "Japan Deep Learning Association · E資格", "JDLA"),
    ("Applied Information Technology Engineer", "IPA · 応用情報技術者", "IPA"),
]

TROPHY = [
    "..########..",
    "###h#####d##",
    "#.#h#####d.#",
    "#.#h#####d.#",
    ".##h#####d#.",
    "..########..",
    "...######...",
    ".....##.....",
    ".....##.....",
    "....####....",
    "...######...",
    "...dddddd...",
]


def achievements() -> None:
    w, tw, th, gap = 800, 600, 66, 14
    x = (w - tw) // 2
    h = 14 + len(ACHIEVEMENTS) * (th + gap) + 8
    css = f"""
.toast{{animation:toast .7s cubic-bezier(.2,.8,.2,1) both}}
@keyframes toast{{from{{opacity:0;transform:translateX(56px)}}}}
.sh{{animation:sh 7s ease-in-out infinite}}
@keyframes sh{{20%,100%{{transform:translateX({tw + 220}px)}}}}
"""
    trophy = pixels(TROPHY, {"#": AMBER, "h": "#ffe3a8", "d": "#b9792b"}, 3)
    toasts = []
    for i, (title, sub, chip) in enumerate(ACHIEVEMENTS):
        y = 14 + i * (th + gap)
        delay = .3 + i * .45
        toasts.append(f"""
<g class="toast" style="animation-delay:{delay:.2f}s">
<clipPath id="tc{i}"><rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="12"/></clipPath>
<rect x="{x + .5}" y="{y + .5}" width="{tw - 1}" height="{th - 1}" rx="12" fill="{PANEL}" stroke="#2c3442"
 filter="url(#shadow)"/>
<rect x="{x + 10.5}" y="{y + 10.5}" width="45" height="45" rx="10" fill="#2a2112" stroke="{AMBER}"
 stroke-opacity=".35"/>
<g transform="translate({x + 15} {y + 15})" shape-rendering="crispEdges">{trophy}</g>
{t(x + 70, y + 22, "ACHIEVEMENT UNLOCKED", AMBER, 10, font_weight="bold", letter_spacing="1.5")}
{t(x + 70, y + 42, title, TEXT, 15, font_weight="bold")}
{t(x + 70, y + 58, sub, MUTED, 12)}
<rect x="{x + tw - 74.5}" y="{y + 22.5}" width="58" height="22" rx="11" fill="none" stroke="{DIM}"/>
{t(x + tw - 45.5, y + 37.5, chip, MUTED, 11, MONO, text_anchor="middle")}
<g clip-path="url(#tc{i})"><g class="sh" style="animation-delay:{delay + .6:.2f}s">
<path d="M{x - 150} {y + th}l40-{th}h56l-40 {th}z" fill="url(#shine)"/></g></g>
</g>""")
    body = f"""
<defs>{SHADOW}
<linearGradient id="shine"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset=".5" stop-color="#fff" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient></defs>
{"".join(toasts)}
"""
    title = "Achievements unlocked: " + "; ".join(a for a, _, _ in ACHIEVEMENTS)
    svg("achievements.svg", w, h, title, css, body)


# --- links: keycaps --------------------------------------------------------

KEYS = [
    ("key-kaggle.svg", "Kaggle", "sigmatango ↗", LEAF, 0),
]


def keycap(name, label, legend, accent, delay) -> None:
    w, h = 200, 88
    css = f"""
.cap{{animation:press 3.6s ease-in-out {delay}s infinite}}
@keyframes press{{0%,78%,100%{{transform:none}}84%,90%{{transform:translateY(6px)}}}}
.led{{animation:led 3.6s ease-in-out {delay}s infinite}}
@keyframes led{{0%,78%,100%{{opacity:.55}}84%,90%{{opacity:1}}}}
"""
    body = f"""
<defs><linearGradient id="surf" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#3b4559"/><stop offset="1" stop-color="#2d3546"/></linearGradient></defs>
<rect x="6.5" y="14.5" width="{w - 13}" height="68" rx="12" fill="#1a1f2b" stroke="#2c3443"/>
<g class="cap">
<rect x="6.5" y="6.5" width="{w - 13}" height="68" rx="12" fill="#29303f" stroke="#3a4457"/>
<rect x="16" y="10" width="{w - 32}" height="52" rx="9" fill="url(#surf)"/>
<circle class="led" cx="{w - 30}" cy="22" r="3.5" fill="{accent}"/>
{t(w / 2, 38, label, TEXT, 15, font_weight="bold", text_anchor="middle")}
{t(w / 2, 55, legend, MUTED, 11.5, text_anchor="middle")}
</g>
"""
    svg(name, w, h, f"{label} — {legend}", css, body)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    header()
    now()
    stack()
    achievements()
    for key in KEYS:
        keycap(*key)


if __name__ == "__main__":
    main()
