"""Genera las tarjetas SVG del README en cards/ (solo librería estándar).

    GH_TOKEN=... python scripts/render_cards.py

Sin token se omiten las tarjetas de contribuciones (se conservan las que ya existan).
"""
import datetime as dt
import json
import os
import random
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
USER = "LukasGarrido"

BG, SURFACE, BORDER = "#0a0809", "#131112", "#2a2526"
TEXT, MUTED, DIM = "#f4f4f5", "#a1a1aa", "#71717a"
CRIMSON, CORAL, ROSE, RED = "#dc2626", "#f87171", "#fb7185", "#ef4444"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'JetBrains Mono',SFMono-Regular,Consolas,Menlo,monospace"
MONTHS = "Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic".split()

# Solo hay animaciones en bucle: todo el contenido debe verse aunque no lleguen a ejecutarse.
STYLE = f"""
.s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
.pulse{{animation:pulse 1.6s ease-in-out infinite}}
.nudge{{animation:nudge 1.8s ease-in-out infinite}}
.sheen{{animation:sheen 6s ease-in-out infinite}}
@keyframes pulse{{50%{{opacity:.25}}}}
@keyframes nudge{{50%{{transform:translateX(5px)}}}}
@keyframes sheen{{0%,55%{{transform:translateX(-500px)}}100%{{transform:translateX(1100px)}}}}
.twinkle{{animation:twinkle 3.5s ease-in-out infinite}}
.hum{{animation:hum 2.4s ease-in-out infinite}}
.fly{{animation:fly 14s linear infinite}}
.hover{{animation:hover 5s ease-in-out infinite}}
@keyframes twinkle{{50%{{opacity:.1}}}}
@keyframes hum{{50%{{opacity:.55}}}}
@keyframes fly{{0%{{transform:none}}45%,100%{{transform:translate(1040px,26px)}}}}
@keyframes hover{{50%{{transform:translateY(-6px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.sheen{{display:none}}}}
"""


def text(x, y, value, size=14, fill=TEXT, cls="s", extra=""):
    return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" {extra}>'
            f"{escape(str(value))}</text>")


def anim(cls, delay, body):
    return f'<g class="{cls}" style="animation-delay:{delay:.2f}s">{body}</g>'


def stars(seed, width, height):
    """Campo de estrellas; la semilla es el nombre de la tarjeta para que no cambie cada día."""
    rng = random.Random(seed)
    out = ""
    for i in range(int(width * height) // 2600):
        x, y = rng.uniform(8, width - 8), rng.uniform(8, height - 8)
        r, opacity = rng.choice([.6, .6, .8, 1.1]), rng.uniform(.18, .6)
        star = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" opacity="{opacity:.2f}"/>'
        out += anim("twinkle", rng.uniform(0, 3.5), star) if i % 5 == 0 else star
    return out


def saber(x, y, length, delay=.6):
    """Sable de luz que se enciende: empuñadura, resplandor y núcleo."""
    hilt = (f'<rect x="{x}" y="{y - 4}" width="30" height="8" rx="2" fill="#71717a"/>'
            f'<rect x="{x + 5}" y="{y - 4}" width="3" height="8" fill="#27272a"/>'
            f'<rect x="{x + 11}" y="{y - 4}" width="3" height="8" fill="#27272a"/>'
            f'<rect x="{x + 27}" y="{y - 6}" width="4" height="12" rx="1" fill="#d4d4d8"/>'
            f'<circle cx="{x + 20}" cy="{y}" r="1.8" fill="{RED}"/>')
    start = x + 32
    halo = (f'<rect x="{start}" y="{y - 7}" width="{length}" height="14" rx="7" fill="{RED}" opacity=".16"/>'
            f'<rect x="{start}" y="{y - 4.5}" width="{length}" height="9" rx="4.5" fill="{RED}" opacity=".4"/>')
    core = (f'<rect x="{start}" y="{y - 2.5}" width="{length}" height="5" rx="2.5" fill="{RED}"/>'
            f'<rect x="{start}" y="{y - 1}" width="{length - 3}" height="2" rx="1" fill="#fff"/>')
    return hilt + anim("ignite", delay, f'<g class="hum">{halo}</g>{core}')


def tie_fighter(color):
    """Silueta de caza TIE centrada en (0, 0), de unos 60x52."""
    wing = "M-4-26H4L8-14V14L4 26H-4L-8 14V-14Z"
    return (f'<g fill="{color}"><path transform="translate(-24 0)" d="{wing}" opacity=".75"/>'
            f'<path transform="translate(24 0)" d="{wing}" opacity=".75"/>'
            '<rect x="-20" y="-2.5" width="40" height="5"/><circle r="11"/></g>'
            f'<circle r="5.5" fill="{BG}"/><path d="M-5.5 0H5.5M0-5.5V5.5" stroke="{color}" stroke-width="1"/>')


def death_star(cx, cy, r, opacity):
    lines = "".join(
        f'<path d="M{cx - r * w:.1f} {cy + r * h:.1f}H{cx + r * w:.1f}"/>'
        for h, w in [(-.66, .6), (-.4, .85), (.3, .9), (.52, .78), (.74, .55)])
    dish_x, dish_y = cx - r * .38, cy - r * .42
    return (f'<g opacity="{opacity}" fill="none" stroke="#fff" stroke-width="1.2">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" fill-opacity=".12"/>{lines}'
            f'<path d="M{cx - r} {cy}H{cx + r}" stroke-width="3.5"/>'
            f'<circle cx="{dish_x:.1f}" cy="{dish_y:.1f}" r="{r * .27:.1f}" fill="{BG}"/>'
            f'<circle cx="{dish_x:.1f}" cy="{dish_y:.1f}" r="{r * .07:.1f}"/></g>')


def save(name, width, height, title, body, fill=BG):
    """Tarjeta con margen transparente de 4px para que se puedan juntar en el README."""
    w, h = width - 8, height - 8
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{STYLE}</style>"
        f'<defs><clipPath id="c"><rect x="4" y="4" width="{w}" height="{h}" rx="14"/></clipPath></defs>'
        f'<g clip-path="url(#c)"><rect x="4" y="4" width="{w}" height="{h}" fill="{fill}"/>{stars(name, width, height)}{body}</g>'
        f'<rect x="4.5" y="4.5" width="{w - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{BORDER}"/>'
        "</svg>"
    )
    (CARDS / f"{name}.svg").write_text(svg, encoding="utf-8")


def glow(gid, cx, cy, r, color, opacity=0.22):
    return (f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>')


def hero():
    b = glow("g1", 690, 200, 300, RED) + glow("g2", 60, 20, 320, CRIMSON)
    b += anim("fade", .1,
              f'<rect class="pulse" x="40" y="62" width="9" height="9" fill="{CORAL}"/>'
              + text(60, 71, "INGENIERÍA INFORMÁTICA · USM CONCEPCIÓN", 12, MUTED, "m",
                     'letter-spacing="1.2"'))
    # nombre con un brillo que recorre el degradado
    b += (f'<linearGradient id="name" gradientUnits="userSpaceOnUse" x1="0" x2="520" spreadMethod="repeat">'
          f'<stop offset="0" stop-color="{CRIMSON}"/><stop offset=".5" stop-color="{CORAL}"/>'
          f'<stop offset="1" stop-color="{CRIMSON}"/>'
          '<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="520 0" '
          'dur="7s" repeatCount="indefinite"/></linearGradient>')
    heavy = 'font-weight="800" letter-spacing="-3"'
    b += anim("rise", .2, text(36, 164, "Lukas", 92, TEXT, "s", heavy))
    b += anim("rise", .32, text(36, 254, "Garrido", 92, "url(#name)", "s", heavy))
    b += saber(40, 274, 300, 1.0)
    b += anim("rise", .5,
              text(40, 306, "Ciencia de datos y desarrollo de software.", 18, "#d4d4d8")
              + text(40, 332, "Los Ángeles – Concepción, Chile", 15, DIM))
    b += anim("fade", .8,
              text(40, 376, "lukasgarrido-portfolio.vercel.app", 13, TEXT, "m")
              + f'<g class="nudge">{text(310, 376, "→", 15, CORAL, "m")}</g>')

    rows = json.loads((ROOT / "data" / "portrait.json").read_text(encoding="utf-8"))
    cols = len("".join(t for _, t in rows[0]))
    x, y, width, line = 478, 28, 372, 7.7
    for i, runs in enumerate(rows):
        spans = "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for c, t in runs)
        b += anim("fade", .25 + i * .03,
                  f'<text x="{x}" y="{y + i * line:.1f}" class="m" font-size="7.9" font-weight="700" '
                  f'xml:space="preserve" textLength="{width}" lengthAdjust="spacingAndGlyphs" '
                  f'data-cols="{cols}">{spans}</text>')
    b += f'<g class="fly"><g transform="translate(-70 32) scale(.6)">{tie_fighter("#a1a1aa")}</g></g>'
    save("hero", 880, 408,
         "Lukas Garrido, estudiante de Ingeniería Informática. Ciencia de datos y desarrollo.", b)


def pillar(name, x_label, big, unit, lines, color, delay):
    w, h = 440, 212
    b = glow("g", 390, 190, 220, color, .35)
    b += f'<rect x="4" y="4" width="432" height="3" fill="{color}"/>'
    b += (f'<g class="sheen"><path d="M0 0H60L-10 212H-70Z" fill="#fff" opacity=".05"/></g>')
    if name == "data":
        b += death_star(368, 130, 62, .22)
    else:
        b += (f'<g class="hover" opacity=".3"><g transform="translate(368 150) scale(1.5)">'
              f'{tie_fighter("#d4d4d8")}</g></g>')
    b += text(24, 40, x_label, 12, color, "m", 'letter-spacing="1.4"')
    b += f'<g class="nudge">{text(398, 40, "→", 15, color, "m")}</g>'
    b += anim("rise", delay,
              f'<text x="22" y="100" class="s" fill="{TEXT}"><tspan font-size="44" font-weight="800">{escape(big)}</tspan>'
              f'<tspan font-size="17" fill="{MUTED}" dx="8">{escape(unit)}</tspan></text>')
    for i, row in enumerate(lines):
        b += anim("rise", delay + .15 + i * .08, text(24, 138 + i * 22, row, 13.5, "#d4d4d8"))
    save(name, w, h, f"{x_label}: {big} {unit}. {' '.join(lines)}", b, SURFACE)


def section_title(name, label, color):
    b = (f'<rect class="pulse" x="26" y="27" width="9" height="9" fill="{color}"/>'
         + anim("rise", .1, text(48, 39, label, 22, TEXT, "s", 'font-weight="700"')))
    b += saber(150, 32, 650)
    save(name, 880, 64, label, b)


def stack():
    groups = [
        ("BACKEND", ["Python", "FastAPI", "Laravel", "MySQL", "PostgreSQL"], CRIMSON),
        ("CIENCIA DE DATOS", ["Jupyter", "Pandas", "NumPy", "Streamlit"], CORAL),
        ("WEB", ["Astro", "Tailwind CSS", "TypeScript"], ROSE),
        ("TOOLS", ["Docker", "Git", "GitHub", "GitLab", "Postman"], RED),
    ]
    b, n = "", 0
    for row, (label, items, color) in enumerate(groups):
        y = 28 + row * 48
        b += text(32, y + 20, label, 12, color, "m", 'letter-spacing="1.4"')
        x = 200
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
    colors = {"NONE": "#1c191a", "FIRST_QUARTILE": "#4c1519", "SECOND_QUARTILE": "#8f1d1d",
              "THIRD_QUARTILE": "#dc2626", "FOURTH_QUARTILE": "#ff6b6b"}
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
        (active, "días activos", CRIMSON),
        (longest, "días de racha máxima", CORAL),
        (best["contributionCount"], f"mejor día · {best_date.day} {MONTHS[best_date.month - 1]}", ROSE),
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
    b = (f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CORAL}"/>'
         f'<stop offset="1" stop-color="{CRIMSON}"/></linearGradient>') + death_star(430, 82, 66, .13) + b
    save("activity", 880, 224,
         f"Actividad mensual: {active} días activos, racha máxima de {longest} días", b)


def main():
    CARDS.mkdir(exist_ok=True)
    hero()
    pillar("data", "CIENCIA DE DATOS", "Datos", "ciencia y análisis", ["Análisis, visualización y aprendizaje automático",
           "con Python, Pandas y notebooks."], CORAL, .2)
    pillar("dev", "SOFTWARE", "Desarrollo", "backend y web", ["APIs con FastAPI y Laravel, sitios con Astro",
           "y entornos con Docker."], CRIMSON, .35)
    section_title("title-stack", "Stack", CORAL)
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
