"""Genera las tarjetas SVG del README en cards/ (solo librería estándar).

    GH_TOKEN=... python scripts/render_cards.py

Sin token se omiten las tarjetas de contribuciones (se conservan las que ya existan).
"""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
USER = "LukasGarrido"

BG, SURFACE, BORDER = "#08090a", "#111315", "#23272d"
TEXT, MUTED, DIM = "#f1f5f9", "#94a3b8", "#64748b"
INDIGO, CYAN, EMERALD, RED = "#6366f1", "#06b6d4", "#10b981", "#ef4444"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'JetBrains Mono',SFMono-Regular,Consolas,Menlo,monospace"
MONTHS = "Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic".split()

STYLE = f"""
.s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
.rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
.fade{{animation:fade .6s ease both}}
.pulse{{animation:pulse 1.6s ease-in-out infinite}}
.nudge{{animation:nudge 1.8s ease-in-out infinite}}
.grow{{animation:grow .9s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:bottom}}
.sheen{{animation:sheen 6s ease-in-out infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pulse{{50%{{opacity:.25}}}}
@keyframes nudge{{50%{{transform:translateX(5px)}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:none}}}}
@keyframes sheen{{0%,55%{{transform:translateX(-500px)}}100%{{transform:translateX(1100px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.sheen{{display:none}}}}
"""


def text(x, y, value, size=14, fill=TEXT, cls="s", extra=""):
    return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" {extra}>'
            f"{escape(str(value))}</text>")


def anim(cls, delay, body):
    return f'<g class="{cls}" style="animation-delay:{delay:.2f}s">{body}</g>'


def save(name, width, height, title, body, fill=BG):
    """Tarjeta con margen transparente de 4px para que se puedan juntar en el README."""
    w, h = width - 8, height - 8
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{STYLE}</style>"
        f'<defs><clipPath id="c"><rect x="4" y="4" width="{w}" height="{h}" rx="14"/></clipPath></defs>'
        f'<g clip-path="url(#c)"><rect x="4" y="4" width="{w}" height="{h}" fill="{fill}"/>{body}</g>'
        f'<rect x="4.5" y="4.5" width="{w - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{BORDER}"/>'
        "</svg>"
    )
    (CARDS / f"{name}.svg").write_text(svg, encoding="utf-8")


def glow(gid, cx, cy, r, color, opacity=0.22):
    return (f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>')


def hero():
    b = glow("g1", 690, 200, 300, RED) + glow("g2", 60, 20, 320, INDIGO)
    b += anim("fade", .1,
              f'<rect class="pulse" x="40" y="62" width="9" height="9" fill="{CYAN}"/>'
              + text(60, 71, "INGENIERÍA INFORMÁTICA · USM CONCEPCIÓN", 12, MUTED, "m",
                     'letter-spacing="1.2"'))
    # nombre con un brillo que recorre el degradado
    b += (f'<linearGradient id="name" gradientUnits="userSpaceOnUse" x1="0" x2="520" spreadMethod="repeat">'
          f'<stop offset="0" stop-color="{INDIGO}"/><stop offset=".5" stop-color="{CYAN}"/>'
          f'<stop offset="1" stop-color="{INDIGO}"/>'
          '<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="520 0" '
          'dur="7s" repeatCount="indefinite"/></linearGradient>')
    heavy = 'font-weight="800" letter-spacing="-3"'
    b += anim("rise", .2, text(36, 164, "Lukas", 92, TEXT, "s", heavy))
    b += anim("rise", .32, text(36, 254, "Garrido", 92, "url(#name)", "s", heavy))
    b += anim("rise", .5,
              text(40, 300, "Desarrollo backend, APIs y análisis de datos.", 18, "#cbd5e1")
              + text(40, 326, "Los Ángeles – Concepción, Chile", 15, DIM))
    b += anim("fade", .8,
              text(40, 376, "lukasgarrido-portfolio.vercel.app", 13, TEXT, "m")
              + f'<g class="nudge">{text(310, 376, "→", 15, CYAN, "m")}</g>')

    rows = json.loads((ROOT / "data" / "portrait.json").read_text(encoding="utf-8"))
    cols = len("".join(t for _, t in rows[0]))
    x, y, width, line = 478, 28, 372, 7.7
    for i, runs in enumerate(rows):
        spans = "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for c, t in runs)
        b += anim("fade", .25 + i * .03,
                  f'<text x="{x}" y="{y + i * line:.1f}" class="m" font-size="7.9" font-weight="700" '
                  f'xml:space="preserve" textLength="{width}" lengthAdjust="spacingAndGlyphs" '
                  f'data-cols="{cols}">{spans}</text>')
    save("hero", 880, 408,
         "Lukas Garrido, estudiante de Ingeniería Informática. Backend, APIs y análisis de datos.", b)


def pillar(name, x_label, big, unit, lines, color, delay):
    w, h = 293.333, 212
    b = glow("g", 250, 190, 170, color, .35)
    b += f'<rect x="4" y="4" width="286" height="3" fill="{color}"/>'
    b += (f'<g class="sheen"><path d="M0 0H60L-10 212H-70Z" fill="#fff" opacity=".05"/></g>')
    b += text(24, 40, x_label, 12, color, "m", 'letter-spacing="1.4"')
    b += f'<g class="nudge">{text(252, 40, "→", 15, color, "m")}</g>'
    b += anim("rise", delay,
              f'<text x="22" y="100" class="s" fill="{TEXT}"><tspan font-size="44" font-weight="800">{escape(big)}</tspan>'
              f'<tspan font-size="17" fill="{MUTED}" dx="8">{escape(unit)}</tspan></text>')
    for i, row in enumerate(lines):
        b += anim("rise", delay + .15 + i * .08, text(24, 138 + i * 22, row, 13.5, "#cbd5e1"))
    save(name, w, h, f"{x_label}: {big} {unit}. {' '.join(lines)}", b, SURFACE)


def section_title(name, label, color):
    b = (f'<rect class="pulse" x="26" y="27" width="9" height="9" fill="{color}"/>'
         + anim("rise", .1, text(48, 39, label, 22, TEXT, "s", 'font-weight="700"')))
    save(name, 880, 64, label, b)


def stack():
    groups = [
        ("BACKEND", ["Python", "FastAPI", "Laravel", "MySQL", "PostgreSQL"], INDIGO),
        ("DATOS", ["Jupyter", "Pandas", "NumPy", "Streamlit"], CYAN),
        ("WEB", ["Astro", "Tailwind CSS", "TypeScript", "JavaScript", "Bootstrap"], EMERALD),
        ("TOOLS", ["Docker", "Git", "GitHub", "GitLab", "Postman"], RED),
    ]
    b, n = "", 0
    for row, (label, items, color) in enumerate(groups):
        y = 28 + row * 48
        b += text(32, y + 20, label, 12, color, "m", 'letter-spacing="1.4"')
        x = 150
        for item in items:
            w = len(item) * 8 + 36
            b += anim("rise", .1 + n * .04,
                      f'<rect x="{x}" y="{y}" width="{w}" height="31" rx="15.5" fill="{SURFACE}" stroke="{BORDER}"/>'
                      f'<circle cx="{x + 15}" cy="{y + 15.5}" r="3.5" fill="{color}"/>'
                      + text(x + 25, y + 20, item, 12.5, TEXT, "m",
                             f'textLength="{len(item) * 7.2:.0f}" lengthAdjust="spacingAndGlyphs"'))
            x += w + 10
            n += 1
    save("stack", 880, 232, "Stack: " + ", ".join(i for g in groups for i in g[1]), b)


def fetch_calendar(token):
    query = ("query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{"
             "totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def heatmap(calendar):
    colors = {"NONE": "#16191d", "FIRST_QUARTILE": "#1e2a5e", "SECOND_QUARTILE": "#3b3fa8",
              "THIRD_QUARTILE": "#6366f1", "FOURTH_QUARTILE": "#22d3ee"}
    total = calendar["totalContributions"]
    b = text(32, 40, f"{total} contribuciones en el último año", 15, TEXT, "s", 'font-weight="700"')
    weeks = calendar["weeks"][-53:]
    step, left, top = 15.4, 32, 76
    last_month, last_x = None, -99
    for i, week in enumerate(weeks):
        x = left + i * step
        month = int(week["contributionDays"][0]["date"][5:7])
        if month != last_month and x - last_x > 32 and x < 820:
            b += text(f"{x:.1f}", 66, MONTHS[month - 1], 11, DIM, "m")
            last_x = x
        last_month = month
        cells = ""
        for day in week["contributionDays"]:
            weekday = dt.date.fromisoformat(day["date"]).isoweekday() % 7
            cells += (f'<rect x="{x:.1f}" y="{top + weekday * step:.1f}" width="12" height="12" rx="3" '
                      f'fill="{colors[day["contributionLevel"]]}"/>')
        b += anim("fade", i * .018, cells)
    save("heatmap", 880, 204, f"{total} contribuciones en GitHub durante el último año", b)


def activity(calendar):
    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["contributionCount"]
    months = list(months.items())[-12:]
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    best = max(days, key=lambda d: d["contributionCount"])
    active = sum(1 for d in days if d["contributionCount"])
    best_date = dt.date.fromisoformat(best["date"])
    stats = [
        (active, "días activos", INDIGO),
        (longest, "días de racha máxima", CYAN),
        (best["contributionCount"], f"mejor día · {best_date.day} {MONTHS[best_date.month - 1]}", EMERALD),
    ]
    b = ""
    for i, (value, label, color) in enumerate(stats):
        y = 56 + i * 62
        b += anim("rise", .15 + i * .15,
                  text(32, y, value, 30, color, "s", 'font-weight="800"')
                  + text(32, y + 18, label, 12, MUTED))
    peak = max(v for _, v in months) or 1
    for i, (key, value) in enumerate(months):
        x, h = 250 + i * 50.5, max(3, value / peak * 130)
        b += (f'<rect class="grow" style="animation-delay:{.2 + i * .06:.2f}s" x="{x}" y="{178 - h:.1f}" '
              f'width="34" height="{h:.1f}" rx="5" fill="url(#bar)"/>')
        b += text(x + 17, f"{170 - h:.1f}", value, 11, MUTED, "m", 'text-anchor="middle"')
        b += text(x + 17, 202, MONTHS[int(key[5:]) - 1], 11, DIM, "m", 'text-anchor="middle"')
    b = (f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}"/>'
         f'<stop offset="1" stop-color="{INDIGO}"/></linearGradient>') + b
    save("activity", 880, 224,
         f"Actividad mensual: {active} días activos, racha máxima de {longest} días", b)


def main():
    CARDS.mkdir(exist_ok=True)
    hero()
    pillar("backend", "BACKEND", "APIs", "REST", ["FastAPI y Laravel sobre", "MySQL y PostgreSQL, con",
           "autenticación JWT."], INDIGO, .2)
    pillar("data", "DATOS", "Data", "& BI", ["Análisis y visualización", "con Python, notebooks",
           "y aprendizaje automático."], CYAN, .35)
    pillar("web", "WEB", "Web", "estática", ["Sitios rápidos y modulares", "con Astro, Tailwind CSS",
           "y Docker."], EMERALD, .5)
    section_title("title-stack", "Stack", CYAN)
    stack()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        calendar = fetch_calendar(token)
        heatmap(calendar)
        activity(calendar)
    else:
        print("Sin GH_TOKEN: no se actualizan heatmap.svg ni activity.svg")


if __name__ == "__main__":
    main()
