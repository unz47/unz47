#!/usr/bin/env python3
"""Build the SVG images shown in the profile README.

GitHub renders README images through <img>, so each SVG is standalone: animation is
CSS inside it and the one display font is embedded. The header is a brass clockwork
that Mochi drives; every other section is plain type on a transparent background,
written twice (-dark / -light) so <picture> can follow the viewer's GitHub theme.

Run:  python3 scripts/build.py   (writes assets/*.svg)
"""

import base64
from html import escape
from pathlib import Path

from gears import TAU, Gear, circle, polar, teeth, train
from logos import LOGOS
from mochi import FRAMES

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

# Bodoni Moda (OFL, see fonts/OFL.txt), pinned to opsz 48 / wght 600 and cut to basic Latin.
FONT = base64.b64encode((HERE / "fonts" / "bodoni-moda-subset.woff2").read_bytes()).decode()
FONT_CSS = ("@font-face{font-family:'Bodoni Moda Subset';font-weight:600;"
            f"src:url(data:font/woff2;base64,{FONT}) format('woff2')}}")

DISPLAY = "'Bodoni Moda Subset','Bodoni 72',Didot,serif"
SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Sans','Yu Gothic UI',"
        "'Noto Sans JP',Helvetica,Arial,sans-serif")
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif"

# The header is a plate of warm black that reads the same in either GitHub theme.
PLATE = "#16120c"
PLATE_INK = "#efe6d2"
PLATE_MUTED = "#a39a88"
BRASS = "#d9ad55"
MOCHI_COLORS = {"o": "#282830", "w": "#faf9f5"}

# Transparent sections borrow GitHub's own text colors for each theme.
THEMES = {
    "dark": {"page": "#0d1117", "ink": "#e6edf3", "muted": "#8d96a0", "line": "#30363d"},
    "light": {"page": "#ffffff", "ink": "#1f2328", "muted": "#59636e", "line": "#d1d9e0"},
}

BASE_CSS = """
.spin{animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.cy{opacity:0}
@keyframes cy6{0%{opacity:1}16.667%{opacity:0}}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important}
  .cy:first-child{opacity:1}
}
"""

METAL = """<defs>
<linearGradient id="brass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6e2a8"/>
<stop offset=".35" stop-color="#d9ad55"/><stop offset=".7" stop-color="#a8762c"/><stop offset="1" stop-color="#6b4818"/>
</linearGradient>
<linearGradient id="bronze" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b8945a"/>
<stop offset=".5" stop-color="#7a5a2e"/><stop offset="1" stop-color="#3e2c16"/></linearGradient>
</defs>"""

X0 = 40  # every section's text starts on the same left edge as the header's


def svg(name: str, w: int, h: int, title: str, body: str, css: str = "") -> None:
    font = FONT_CSS if "Bodoni Moda Subset" in body else ""
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">\n'
           f"<title>{escape(title)}</title>\n<style>{font}{css}{BASE_CSS}</style>\n{body}\n</svg>\n")
    (ASSETS / name).write_text(doc)


def t(x, y, s, fill, size=13, family=SANS, **attrs) -> str:
    """A <text>. Keyword args become attributes (underscores turn into dashes)."""
    extra = "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-family="{family}"{extra}>{escape(s)}</text>')


def text_width(s: str, size: float) -> float:
    """Rough advance width of proportional sans text; errs wide so runs never collide."""
    em = {**dict.fromkeys("iljIf.,:;'|!/()[] ", .32), **dict.fromkeys("mwMW", .86)}
    return size * sum(em.get(c, .68 if c.isupper() or c.isdigit() else .56) for c in s)


def title(y, s, theme) -> str:
    return t(X0, y, s, theme["ink"], 30, DISPLAY, font_weight="600")


def rule(y, theme, x1=X0, x2=760) -> str:
    return f'<line x1="{x1}" y1="{y + .5}" x2="{x2}" y2="{y + .5}" stroke="{theme["line"]}"/>'


def spin(g: Gear, inner: str) -> str:
    """`inner` turning about the gear's centre at the gear's speed."""
    rev = ";animation-direction:reverse" if g.speed < 0 else ""
    return (f'<g class="spin" style="transform-origin:{g.x:.2f}px {g.y:.2f}px;'
            f'animation-duration:{1 / abs(g.speed):.3f}s{rev}">{inner}</g>')


def wheel(g: Gear, m, *, spokes=5, twist=.45, hub=None, metal="brass") -> str:
    """A clock wheel: toothed rim, curved spokes, an inner ring, and a slotted screw at the hub."""
    x, y, r = g.x, g.y, m * g.z / 2
    rim_in = r - 1.25 * m - max(2.5, 1.5 * m)
    hub = hub if hub is not None else max(5.0, r * .18)
    fill = f"url(#{metal})"
    mid = (hub + rim_in) / 2
    arms = "".join(f"M{polar(x, y, hub - .5, a)}Q{polar(x, y, mid, a + twist * .6)} "
                   f"{polar(x, y, rim_in + .5, a + twist)}"
                   for a in (g.rot + k * TAU / spokes for k in range(spokes)))
    slot = f"M{polar(x, y, hub * .7, g.rot + .4)}L{polar(x, y, hub * .7, g.rot + .4 + TAU / 2)}"
    return spin(g, f'<path d="{teeth(x, y, g.z, m, g.rot)}{circle(x, y, rim_in)}" fill="{fill}" '
                   f'fill-rule="evenodd"/>'
                   f'<path d="{arms}" fill="none" stroke="{fill}" stroke-width="{max(1.4, m * .7):.1f}" '
                   f'stroke-linecap="round"/>'
                   f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{hub + (rim_in - hub) * .62:.2f}" fill="none" '
                   f'stroke="{fill}" stroke-width="{max(.8, m * .35):.1f}"/>'
                   f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{hub:.2f}" fill="{fill}"/>'
                   f'<path d="{slot}" stroke="{PLATE}" stroke-width="{max(1.2, hub * .22):.1f}" '
                   f'stroke-linecap="round"/>')


def outline(x, y, z, m, rot=0.0) -> str:
    """A faint, still outline of a gear far behind the others."""
    r = m * z / 2
    arms = "".join(f"M{polar(x, y, r * .2, a)}L{polar(x, y, r * .62, a)}" for a in (k * TAU / 6 for k in range(6)))
    d = teeth(x, y, z, m, rot) + circle(x, y, r * .62) + circle(x, y, r * .2) + arms
    return f'<path d="{d}" fill="none" stroke="{BRASS}" stroke-opacity=".12"/>'


def dial(cx, cy, r) -> str:
    """A still ring of Roman numerals behind the wheel."""
    numerals = "XII I II III IV V VI VII VIII IX X XI".split()
    marks = "".join(t(cx, cy - r + 4, n, BRASS, 10, SERIF, text_anchor="middle", fill_opacity=".3",
                      transform=f"rotate({k * 30} {cx} {cy})") for k, n in enumerate(numerals))
    ticks = "".join(f"M{polar(cx, cy, r + 8, k * TAU / 60)}L{polar(cx, cy, r + (13 if k % 5 == 0 else 10), k * TAU / 60)}"
                    for k in range(60))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r + 8}" fill="none" stroke="{BRASS}" stroke-opacity=".18"/>'
            f'<path d="{ticks}" stroke="{BRASS}" stroke-opacity=".24"/>' + marks)


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


# --- header: Mochi runs a wheel that drives the clockwork -------------------

INTRO = [
    "Mostly TypeScript: Angular, Ionic and NestJS on AWS.",
    "Outside work: Rust, mobile apps, shaders, Kaggle.",
]


def header() -> None:
    w, h, m = 800, 260, 2.6
    cx, cy = 575, 140
    g = train((cx, cy), 50, m, 1 / 14, [
        (0, 18, -40),     # 1 front, driven by the wheel
        (1, 44, "axle"),  # 2 back, on the same shaft
        (2, 30, 25),      # 3
        (3, 36, 95),      # 4
        (2, 24, -95),     # 5
        (0, 16, 205),     # 6 front, left of the wheel
        (4, 14, 150),     # 7
    ])
    back = (outline(790, 30, 60, 3, .05) + outline(430, 292, 56, 3, .1) + outline(700, 268, 40, 3, .2)
            + dial(cx, cy, 118))
    behind = "".join(wheel(g[i], m, metal="bronze", spokes=s) for i, s in ((2, 6), (3, 5), (4, 5), (5, 4), (7, 3)))
    rim_in = m * 50 / 2 - 1.25 * m - 3.9
    arms = "".join(f"M{polar(cx, cy, 7, a)}L{polar(cx, cy, rim_in + .5, a)}" for a in (k * TAU / 10 for k in range(10)))
    drum = spin(g[0], f'<path d="{teeth(cx, cy, 50, m)}{circle(cx, cy, rim_in)}" fill="url(#brass)" '
                      f'fill-rule="evenodd"/><path d="{arms}" stroke="url(#bronze)" stroke-width="1.6"/>')
    front = drum + wheel(g[1], m, spokes=4) + wheel(g[6], m, spokes=4)
    clockwork = back + behind + front + mochi(cx - 32, cy + 46 - 64, 4)
    words = (t(X0, 100, "s@i", PLATE_INK, 64, DISPLAY, font_weight="600")
             + t(X0 + 2, 132, "Full-stack engineer, Tokyo", PLATE_MUTED, 14)
             + "".join(t(X0 + 2, 178 + i * 24, line, PLATE_INK, 15) for i, line in enumerate(INTRO)))
    body = (METAL + f'<defs><clipPath id="plate"><rect width="{w}" height="{h}" rx="8"/></clipPath></defs>'
            f'<rect width="{w}" height="{h}" rx="8" fill="{PLATE}"/>'
            f'<g clip-path="url(#plate)">{clockwork}</g>' + words)
    svg("header.svg", w, h, "s@i — full-stack engineer in Tokyo. " + " ".join(INTRO), body)


# --- the plain sections -------------------------------------------------------

NOW = [
    ("Desk Buddy", "A tray pet that levels up with your CPU", "Rust, Tauri"),
    ("shaders-art", "A museum of fragment shaders", "GLSL, TypeScript"),
    ("RSNA Knee MRI", "Kaggle, weakly-supervised multi-label", "Python"),
]

CERTS = [
    ("AWS Certified Solutions Architect – Professional", "Amazon Web Services"),
    ("JDLA Deep Learning for ENGINEER (E資格)", "Japan Deep Learning Association"),
    ("Applied Information Technology Engineer (応用情報)", "IPA"),
]

# (row label, [(logo slug or None, name)]); None where there is no logo or it is an unreadable wordmark
STACK = [
    ("Languages", [("typescript", "TypeScript"), ("javascript", "JavaScript"), ("python", "Python"),
                   ("rust", "Rust"), ("swift", "Swift"), ("kotlin", "Kotlin"), ("openjdk", "Java"),
                   (None, "GLSL"), ("gnubash", "Bash"), ("nixos", "Nix"), (None, "SQL")]),
    ("Frameworks", [("angular", "Angular"), ("ionic", "Ionic"), ("capacitor", "Capacitor"), ("react", "React"),
                    ("nextdotjs", "Next.js"), ("react", "React Native"), ("expo", "Expo"), ("nestjs", "NestJS"),
                    ("express", "Express"), ("fastapi", "FastAPI"), ("tauri", "Tauri"),
                    ("tailwindcss", "Tailwind CSS")]),
    ("Libraries", [("effect", "Effect"), ("reactivex", "RxJS"), ("drizzle", "Drizzle"), ("threedotjs", "Three.js"),
                   (None, "p5.js"), ("shadcnui", "shadcn/ui"), ("vitest", "Vitest"), ("webrtc", "WebRTC"),
                   ("pytorch", "PyTorch"), ("scikitlearn", "scikit-learn"), ("pandas", "pandas"),
                   ("numpy", "NumPy")]),
    ("Platforms & tools", [(None, "AWS"), ("vercel", "Vercel"), ("supabase", "Supabase"), ("docker", "Docker"),
                           ("githubactions", "GitHub Actions"), ("stripe", "Stripe"), ("claude", "Claude"),
                           ("vite", "Vite"), ("turborepo", "Turborepo"), (None, "Kaggle"),
                           ("jupyter", "Jupyter"), ("blender", "Blender")]),
]


GLYPHS = {"AWS": "#ff9900", "GLSL": "#5586a4", "p5.js": "#ed225d", "Kaggle": "#20beff"}


def logo(slug, x, y, size, fill) -> str:
    """A Simple Icons logo, one flat color, with its top-left corner at (x, y)."""
    return (f'<path transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})" '
            f'd="{LOGOS[slug][1]}" fill="{fill}"/>')


def table(rows, y, theme, row_h=40) -> tuple[str, float]:
    """Rows of name / note / detail divided by hairlines; returns (markup, y below)."""
    out = [rule(y, theme)]
    for name, note, detail in rows:
        base = y + row_h / 2 + 5
        out.append(t(X0, base, name, theme["ink"], 15, font_weight="600")
                   + (t(232, base, note, theme["muted"], 14) if note else "")
                   + t(760, base, detail, theme["muted"], 13, text_anchor="end")
                   + rule(y + row_h, theme))
        y += row_h
    return "".join(out), y


def now(theme) -> tuple[str, int, str]:
    rows, end = table(NOW, 58, theme)
    return title(40, "Now", theme) + rows, int(end + 8), "Now: " + "; ".join(f"{n} — {s} ({d})" for n, s, d in NOW)


def certifications(theme) -> tuple[str, int, str]:
    rows, end = table([(c, "", issuer) for c, issuer in CERTS], 58, theme)
    return (title(40, "Certifications", theme) + rows, int(end + 8),
            "Certifications: " + "; ".join(c for c, _ in CERTS))


def luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return sum(k * (c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4)
               for k, c in zip((.2126, .7152, .0722), (r, g, b)))


def readable(brand: str, theme) -> str:
    """The brand color, unless it nearly vanishes on this theme's page; then the text color."""
    a, b = luminance(brand), luminance(theme["page"])
    return brand if (max(a, b) + .05) / (min(a, b) + .05) >= 2 else theme["ink"]


def stack(theme) -> tuple[str, int, str]:
    pitch, size = 60, 28
    out, y = [title(40, "Stack", theme)], 40
    for label, items in STACK:
        y += 44
        out.append(t(X0, y, label, theme["muted"], 14))
        for i, (slug, name) in enumerate(items):
            cx, cy = X0 + pitch / 2 + i * pitch, y + 34
            if slug in LOGOS:
                out.append(logo(slug, cx - size / 2, cy - size / 2, size, readable(LOGOS[slug][0], theme)))
            else:
                color = readable(GLYPHS.get(name, theme["ink"]), theme)
                out.append(t(cx, cy + 5, name, color, 14, MONO, font_weight="bold", text_anchor="middle"))
            out.append(t(cx, cy + 32, name, theme["muted"], 10.5, text_anchor="middle"))
        y += 66
    alt = "Stack — " + "; ".join(f"{label}: " + ", ".join(n for _, n in items) for label, items in STACK)
    return "".join(out), int(y + 4), alt


def kaggle(theme) -> tuple[str, int, str]:
    return (t(X0, 22, "Kaggle", theme["ink"], 14, font_weight="600")
            + t(X0 + 58, 22, "sigmatango ↗", theme["muted"], 14), 32, "Kaggle: sigmatango")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    header()
    for name, section in (("now", now), ("stack", stack), ("certifications", certifications), ("kaggle", kaggle)):
        for theme_name, theme in THEMES.items():
            body, h, alt = section(theme)
            svg(f"{name}-{theme_name}.svg", 800, h, alt, body)


if __name__ == "__main__":
    main()
