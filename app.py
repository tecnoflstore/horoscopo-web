import random
from datetime import date, timedelta
from flask import Flask, abort, render_template, request, redirect
from datos import SIGNOS, BANCOS, COLORES

app = Flask(__name__)

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

NIVELES = [
    (80, "Excelente", "Una combinación con mucha química: se entienden casi sin hablar y se impulsan mutuamente."),
    (65, "Buena", "Tienen buenas bases. Con comunicación y paciencia pueden construir algo sólido."),
    (50, "Regular", "Son distintos, y eso puede enriquecer o chocar. Requiere esfuerzo de ambos."),
    (0, "Desafiante", "Sus ritmos son muy diferentes, pero con respeto y humor pueden aprender mucho el uno del otro."),
]

# Último día (mes, día) de cada signo, en orden del calendario
RANGOS = [(1, 19, "capricornio"), (2, 18, "acuario"), (3, 20, "piscis"), (4, 19, "aries"),
          (5, 20, "tauro"), (6, 20, "geminis"), (7, 22, "cancer"), (8, 22, "leo"),
          (9, 22, "virgo"), (10, 22, "libra"), (11, 21, "escorpio"), (12, 21, "sagitario")]


def signo_de(mes, dia):
    for m, d, slug in RANGOS:
        if (mes, dia) <= (m, d):
            return slug
    return "capricornio"


def generar(slug, semilla):
    """Mismo signo + misma fecha = mismo texto. Fecha nueva = texto nuevo (automático)."""
    r = random.Random(f"{slug}-{semilla}")
    h = {k: " ".join(r.sample(BANCOS[k], 2)) for k in ("general", "amor", "trabajo", "dinero", "salud")}
    h["consejo"] = r.choice(BANCOS["consejo"])
    h["frase"] = r.choice(BANCOS["frase"])
    h["estrellas"] = {k: r.randint(2, 5) for k in ("Amor", "Trabajo", "Dinero", "Salud")}
    h["numero"] = r.randint(1, 99)
    h["color"] = r.choice(COLORES)
    h["hora"] = f"{r.randint(8, 21)}:{r.choice(['00', '15', '30', '45'])}"
    h["amor_largo"] = " ".join(r.sample(BANCOS["amor"], 4))
    h["compatible"] = r.choice([v["n"] for k, v in SIGNOS.items() if k != slug])
    return h


def afinidad(a, b):
    """Calcula la compatibilidad según los elementos. A+B da lo mismo que B+A."""
    ea, eb = SIGNOS[a]["el"], SIGNOS[b]["el"]
    par = {ea, eb}
    if ea == eb:
        base = 80
    elif par in ({"Fuego", "Aire"}, {"Tierra", "Agua"}):
        base = 85
    elif par in ({"Fuego", "Tierra"}, {"Aire", "Agua"}):
        base = 55
    else:
        base = 45
    r = random.Random("-".join(sorted([a, b])))
    p = {k: max(30, min(100, base + r.randint(-10, 10))) for k in ("Amor", "Amistad", "Trabajo")}
    total = round(sum(p.values()) / 3)
    nivel, texto = next((n, t) for m, n, t in NIVELES if total >= m)
    return p, total, nivel, texto


@app.route("/")
def inicio():
    hoy = date.today()
    frase = random.Random(str(hoy)).choice(BANCOS["frase"])
    dest_slug = random.Random(f"destacado{hoy}").choice(list(SIGNOS))  # cambia cada día
    return render_template("index.html", signos=SIGNOS, hoy=hoy, frase=frase,
                           dest_slug=dest_slug, dest=SIGNOS[dest_slug],
                           dest_h=generar(dest_slug, hoy))


@app.route("/signo/<slug>")
@app.route("/signo/<slug>/<modo>")
def signo(slug, modo="hoy"):
    if slug not in SIGNOS or modo not in ("hoy", "semana", "mes", "amor"):
        abort(404)
    hoy = date.today()
    if modo == "hoy":
        h, rango = generar(slug, hoy), hoy.strftime("%d/%m/%Y")
    elif modo == "mes":
        h, rango = generar(slug, f"mes{hoy.year}-{hoy.month}"), f"{MESES[hoy.month - 1]} {hoy.year}"
    elif modo == "amor":
        h, rango = generar(slug, f"amor{hoy}"), hoy.strftime("%d/%m/%Y")
    else:
        lunes = hoy - timedelta(days=hoy.weekday())
        h = generar(slug, f"semana{lunes}")
        rango = f"{lunes.strftime('%d/%m')} al {(lunes + timedelta(days=6)).strftime('%d/%m/%Y')}"
    return render_template("signo.html", s=SIGNOS[slug], slug=slug, h=h, modo=modo,
                           rango=rango, signos=SIGNOS)


@app.route("/compatibilidad")
def compat_form():
    a, b = request.args.get("a"), request.args.get("b")
    if a in SIGNOS and b in SIGNOS:
        return redirect(f"/compatibilidad/{a}/{b}")
    return render_template("compat.html", signos=SIGNOS, res=None, a=None, b=None)


@app.route("/compatibilidad/<a>/<b>")
def compat(a, b):
    if a not in SIGNOS or b not in SIGNOS:
        abort(404)
    p, total, nivel, texto = afinidad(a, b)
    res = dict(p=p, total=total, nivel=nivel, texto=texto)
    return render_template("compat.html", signos=SIGNOS, a=a, b=b, res=res)


@app.route("/que-signo-soy")
def que_signo():
    slug, error = None, None
    texto = request.args.get("fecha")
    if texto:
        try:
            f = date.fromisoformat(texto)
            slug = signo_de(f.month, f.day)
        except ValueError:
            error = "La fecha no es válida. Inténtalo de nuevo."
    return render_template("quien.html", signos=SIGNOS, slug=slug, error=error)


@app.route("/contacto")
def contacto():
    return render_template("contacto.html")


@app.route("/privacidad")
def privacidad():
    return render_template("privacidad.html")


if __name__ == "__main__":
    app.run(debug=True)