"""Genera las tarjetas SVG del README en cards/ (solo librería estándar).

    GH_TOKEN=... python scripts/render_cards.py

Sin token se omiten las tarjetas de contribuciones (se conservan las que ya existan).
Estética de Blade Runner 2049: portada en arte ASCII (ver portrait.py) y rótulos de neón en el resto.
"""
import base64
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
COVER = ROOT / "assets" / "br2049" / "cover.jpg"
USER = "LukasGarrido"

BG, SURFACE, BORDER = "#0a0b0e", "#111318", "#262a33"
TEXT, MUTED, DIM = "#eef0f2", "#9aa1ab", "#666e7a"
ORANGE, AMBER, TEAL, MAGENTA = "#f0801c", "#f5b83d", "#3fd0cc", "#ee4aa6"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'JetBrains Mono',SFMono-Regular,Consolas,Menlo,monospace"
MONTHS = "Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic".split()

# La portada se "genera" al cargar. El nombre no se anima y la foto tenue queda visible desde el
# principio, para que la tarjeta nunca aparezca vacía si las animaciones no llegan a ejecutarse.
STYLE = f"""
.s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
.shadow{{paint-order:stroke;stroke:#000;stroke-opacity:.35;stroke-width:3px}}
.flicker{{animation:flicker 5s linear infinite}}
@keyframes flicker{{0%,90%,94%,100%{{opacity:1}}92%{{opacity:.3}}96%{{opacity:.6}}}}
.build{{animation:build .45s ease-out both}}
.reveal{{animation:reveal 3.2s linear both}}
.beam{{opacity:0;animation:beam 2.9s linear .1s}}
@keyframes build{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes reveal{{from{{opacity:.12}}to{{opacity:.42}}}}
@keyframes beam{{0%,92%{{opacity:1}}100%{{opacity:0}}}}
@keyframes sweep{{from{{transform:translateY(0)}}to{{transform:translateY(420px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def text(x, y, value, size=14, fill=TEXT, cls="s", extra=""):
    return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" {extra}>'
            f"{escape(str(value))}</text>")


def neon(x, y, value, size, color, angle=0, opacity=.7, flicker=False):
    """Rótulo de neón: un halo ancho bajo las letras."""
    common = f'text-anchor="middle" letter-spacing="2"'
    halo = "".join(
        text(x, y, value, size, "none", "m",
             f'{common} stroke="{color}" stroke-width="{width}" stroke-opacity="{alpha}" stroke-linejoin="round"')
        for width, alpha in ((7, .1), (3, .22)))
    cls = ' class="flicker"' if flicker else ""
    return (f'<g transform="rotate({angle} {x} {y})" opacity="{opacity}"><g{cls}>{halo}'
            f"{text(x, y, value, size, color, 'm', common)}</g></g>")


def sign(x, y, value, color, size=15, opacity=.6):
    """Letrero vertical japonés, como los de las calles de la película."""
    height = len(value) * (size + 3) + 12
    letters = "".join(
        text(x, y + 6 + size + i * (size + 3) - 2, char, size, color, "s", 'text-anchor="middle"')
        for i, char in enumerate(value))
    return (f'<g opacity="{opacity}"><rect x="{x - size / 2 - 6}" y="{y}" width="{size + 12}" height="{height}" '
            f'fill="{color}" fill-opacity=".07" stroke="{color}" stroke-opacity=".6"/>{letters}</g>')


def unicorn(x, y, scale, color):
    """Unicornio de origami centrado en (x, y)."""
    facets = [
        ("M-30 4L8-6L24 18L-18 22Z", .5), ("M8-6L26-34L36-18L24 18Z", .75),
        ("M26-34L50-20L36-18Z", .95), ("M28-33L40-58L33-31Z", 1),
        ("M-30 4L-52-22L-38 12Z", .65), ("M-18 22L-28 50L-8 22Z", .8),
        ("M-8 22L-6 48L4 20Z", .4), ("M12 19L10 50L22 18Z", .6), ("M20 18L36 40L24 8Z", .85),
    ]
    paths = "".join(
        f'<path d="{d}" fill="{color}" fill-opacity="{a * .35:.2f}" stroke="{color}" stroke-opacity="{a}" '
        'stroke-linejoin="round"/>' for d, a in facets)
    return f'<g transform="translate({x} {y}) scale({scale})" opacity=".6">{paths}</g>'


def glow(gid, cx, cy, r, color, opacity=0.2):
    return (f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>')


def save(name, width, height, title, body, fill=BG, texture=True):
    """Tarjeta con margen transparente de 4px para que se puedan juntar en el README."""
    w, h = width - 8, height - 8
    lines = (f'<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse">'
             '<rect width="4" height="1" fill="#fff" opacity=".028"/></pattern>'
             f'<rect x="4" y="4" width="{w}" height="{h}" fill="url(#lines)"/>') if texture else ""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{STYLE}</style>"
        f'<defs><clipPath id="c"><rect x="4" y="4" width="{w}" height="{h}" rx="14"/></clipPath></defs>'
        f'<g clip-path="url(#c)"><rect x="4" y="4" width="{w}" height="{h}" fill="{fill}"/>{body}{lines}</g>'
        f'<rect x="4.5" y="4.5" width="{w - 1}" height="{h - 1}" rx="13.5" fill="none" stroke="{BORDER}"/>'
        "</svg>"
    )
    (CARDS / f"{name}.svg").write_text(svg, encoding="utf-8")


def hero():
    # Imagen tenue de base (incrustada: GitHub no deja que un SVG cargue imágenes externas)
    # y encima la misma escena dibujada con caracteres.
    data = base64.b64encode(COVER.read_bytes()).decode()
    b = (f'<image class="reveal" x="4" y="4" width="872" height="420" opacity=".42" '
         f'href="data:image/jpeg;base64,{data}"/>')
    rows = json.loads((ROOT / "data" / "portrait.json").read_text(encoding="utf-8"))
    line = 420 / len(rows)
    for i, runs in enumerate(rows):
        spans = "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for c, t in runs)
        b += (f'<text x="4" y="{4 + (i + .85) * line:.1f}" class="m build" '
              f'style="animation-delay:{.1 + i * .05:.2f}s" font-size="8.4" font-weight="700" '
              f'xml:space="preserve" textLength="872" lengthAdjust="spacingAndGlyphs">{spans}</text>')
    # haz que baja junto a las filas que van apareciendo
    b += ('<g class="beam"><g style="animation:sweep 2.75s linear .1s both">'
          f'<rect x="4" y="-14" width="872" height="18" fill="{AMBER}" opacity=".12"/>'
          f'<rect x="4" y="3" width="872" height="2" fill="{AMBER}" opacity=".85"/></g></g>')
    # sombra suave bajo el texto, sobre el suelo, lejos de la figura y el vehículo
    b += (f'<radialGradient id="shade"><stop offset=".35" stop-color="{BG}" stop-opacity=".9"/>'
          f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>'
          '<ellipse cx="170" cy="340" rx="340" ry="165" fill="url(#shade)"/>')
    heavy = 'font-weight="800" letter-spacing="-2"'
    b += (f'<linearGradient id="name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ORANGE}"/>'
          f'<stop offset="1" stop-color="{AMBER}"/></linearGradient>')
    b += text(40, 250, "INGENIERÍA INFORMÁTICA · USM", 11, "#f6dcc0", "m shadow", 'letter-spacing="1.2"')
    b += text(36, 312, "Lukas", 68, "#ffffff", "s shadow", heavy)
    b += text(36, 372, "Garrido", 68, "url(#name)", "s shadow", heavy)
    b += text(40, 399, "Ciencia de datos y desarrollo · Concepción, Chile", 13, "#f6dcc0", "s shadow")
    save("hero", 880, 428,
         "Lukas Garrido, estudiante de Ingeniería Informática. Ciencia de datos y desarrollo.", b, texture=False)


def pillar(name, x_label, big, unit, lines, color, extras):
    b = glow("g", 380, 180, 220, color, .24)
    b += f'<rect x="4" y="4" width="432" height="2" fill="{color}"/>'
    b += text(24, 40, x_label, 12, color, "m", 'letter-spacing="2"')
    b += (f'<text x="22" y="98" class="s" fill="{TEXT}"><tspan font-size="42" font-weight="800">{escape(big)}</tspan>'
          f'<tspan font-size="17" fill="{MUTED}" dx="8">{escape(unit)}</tspan></text>')
    for i, row in enumerate(lines):
        b += text(24, 136 + i * 22, row, 13.5, "#d3d7dd")
    save(name, 440, 212, f"{x_label}: {big} {unit}. {' '.join(lines)}", b + extras, SURFACE)


def stack_title():
    b = glow("g", 760, 32, 260, ORANGE, .2)
    b += (f'<rect x="26" y="27" width="9" height="9" fill="{ORANGE}"/>'
          + text(48, 39, "Stack", 22, TEXT, "s", 'font-weight="700"'))
    b += neon(440, 38, "ブレードランナー", 15, TEAL, 0, .55)
    b += neon(790, 40, "2049", 24, ORANGE, -4, .75, True)
    save("title-stack", 880, 64, "Stack", b)


def stack():
    groups = [
        ("BACKEND", ["Python", "FastAPI", "Laravel", "MySQL", "PostgreSQL"], ORANGE),
        ("CIENCIA DE DATOS", ["Jupyter", "Pandas", "NumPy", "Streamlit"], TEAL),
        ("WEB", ["Astro", "Tailwind CSS", "TypeScript"], AMBER),
        ("TOOLS", ["Docker", "Git", "GitHub", "GitLab", "Postman"], MAGENTA),
    ]
    b = glow("g", 780, 200, 260, MAGENTA, .13)
    for row, (label, items, color) in enumerate(groups):
        y = 28 + row * 48
        b += text(32, y + 20, label, 12, color, "m", 'letter-spacing="1.4"')
        x = 200
        for item in items:
            w = len(item) * 8 + 36
            b += (f'<rect x="{x}" y="{y}" width="{w}" height="31" rx="15.5" fill="{SURFACE}" stroke="{BORDER}"/>'
                  f'<circle cx="{x + 15}" cy="{y + 15.5}" r="3.5" fill="{color}"/>'
                  + text(x + 25, y + 20, item, 12.5, TEXT, "m",
                         f'textLength="{len(item) * 7.2:.0f}" lengthAdjust="spacingAndGlyphs"'))
            x += w + 10
    b += neon(690, 137, "lágrimas en la lluvia", 14, TEAL, -5, .6)
    b += unicorn(790, 180, .62, AMBER) + sign(844, 24, "レプリカント", MAGENTA, 13, .55)
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
    colors = {"NONE": "#181b21", "FIRST_QUARTILE": "#4d2a0e", "SECOND_QUARTILE": "#8c480e",
              "THIRD_QUARTILE": "#e07412", "FOURTH_QUARTILE": "#fdc14a"}
    total = calendar["totalContributions"]
    b = glow("g", 830, 190, 300, ORANGE, .16)
    b += text(32, 40, f"{total} contribuciones en el último año", 15, TEXT, "s", 'font-weight="700"')
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
        for day in week["contributionDays"]:
            weekday = dt.date.fromisoformat(day["date"]).isoweekday() % 7
            b += (f'<rect x="{x:.1f}" y="{top + weekday * step:.1f}" width="12" height="12" rx="3" '
                  f'fill="{colors[day["contributionLevel"]]}"/>')
    # los rótulos van en la franja superior, donde no tapan datos
    b += neon(500, 39, "células interconectadas", 14, TEAL, -2, .7, True)
    b += neon(752, 40, "constante K", 15, MAGENTA, 3, .7)
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
        (active, "días activos", ORANGE),
        (longest, "días de racha máxima", AMBER),
        (best["contributionCount"], f"mejor día · {best_date.day} {MONTHS[best_date.month - 1]}", TEAL),
    ]
    b = glow("g", 200, 0, 330, TEAL, .12) + glow("o", 830, 224, 280, ORANGE, .18)
    b += neon(455, 58, "¿sueñan los androides", 17, TEAL, -3, .6)
    b += neon(470, 82, "con ovejas eléctricas?", 17, TEAL, -3, .6)
    b += sign(672, 14, "データ", MAGENTA, 15, .6)
    for i, (value, label, color) in enumerate(stats):
        y = 56 + i * 62
        b += text(32, y, value, 30, color, "s", 'font-weight="800"') + text(32, y + 18, label, 12, MUTED)
    peak = max(v for _, v in months) or 1
    for i, (key, value) in enumerate(months):
        x, h = 250 + i * 50.5, max(3, value / peak * 130)
        b += f'<rect x="{x}" y="{178 - h:.1f}" width="34" height="{h:.1f}" rx="5" fill="{ORANGE}"/>'
        b += text(x + 17, f"{170 - h:.1f}", value, 11, MUTED, "m", 'text-anchor="middle"')
        b += text(x + 17, 202, MONTHS[int(key[5:]) - 1], 11, DIM, "m", 'text-anchor="middle"')
    save("activity", 880, 224,
         f"Actividad mensual: {active} días activos, racha máxima de {longest} días", b)


def main():
    CARDS.mkdir(exist_ok=True)
    hero()
    pillar("data", "CIENCIA DE DATOS", "Datos", "ciencia y análisis",
           ["Análisis, visualización y aprendizaje automático", "con Python, Pandas y notebooks."], TEAL,
           neon(320, 190, "test de referencia ✓", 14, TEAL, -4, .65) + sign(404, 24, "情報", TEAL))
    pillar("dev", "SOFTWARE", "Desarrollo", "backend y web",
           ["APIs con FastAPI y Laravel, sitios con Astro", "y entornos con Docker."], ORANGE,
           neon(236, 190, "más humano que humano", 14, ORANGE, -3, .65) + unicorn(394, 148, .6, ORANGE))
    stack_title()
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
