# -*- coding: utf-8 -*-
"""
Reglas de Eventos de Vida — Hugo Bonito.

Fuente: dos documentos mecanografiados encontrados entre el material
gráfico de Bonito (imágenes 3e06e7c1 y 787b785b, transcriptas íntegras en
revision_omega_imagenes.md), con reglas puntuales de "esto significa esto"
— no una técnica de escaneo en el tiempo como Fechas Gemelas o Pronóstico,
sino un CHEQUEO de aspectos fijos sobre una carta (Natal y/o Revolución
Solar de un año dado).

REGLAS 1-10 (documento "reglas generales", texto íntegro citado en cada
regla): cada una compara un cuerpo (Natal o de una Revolución Solar dada,
en las variantes Trópico/Sideral y a veces también Geocéntrico/
Heliocéntrico que el propio texto enumera) contra un punto angular NATAL
fijo (Ascendente, MC, Vértex, Ecuador Celeste o Rueda de la Fortuna).

REGLAS 12-14 (documento de Revolución Solar, "HUGO BONITO. REVOLUCIÓN
SOLAR"): a diferencia de las anteriores, comparan puntos DE LA REVOLUCIÓN
SOLAR entre sí o contra un punto/cuerpo NATAL — requieren que se calcule
una Revolución Solar para el año en cuestión (ver revolucion.py).

RECONSTRUCCIÓN HONESTA:
- La regla de "Pérdida del padre" (imagen 787b785b) se creyó cortada en un
  primer momento por una transcripción automática defectuosa del original;
  releída directamente de la imagen dice completa: "Absolutamente siempre
  el MC de la revolución solar va a estar 90 grados del sol." Se implementa
  como MC de la Revolución Solar en cuadratura (90°) con el Sol NATAL (sin
  "de revo" aclarado, se toma Natal — misma convención que el resto de las
  reglas de este módulo).
- Regla "Divorciada" (imagen 787b785b): corregida tras releer la imagen
  directamente — los aspectos documentados son Conjunción, SEXTIL y
  Trígono del Ascendente de revo con Plutón (no Cuadratura, como decía una
  versión anterior de este módulo). La propia imagen trae una nota de
  quien transcribió la clase de Hugo: "Esto lo dijo así pero para mí se
  equivocó porque después abajo escribí otra cosa" — es decir, hay una
  duda sobre esta regla puesta por la propia persona que tomó el apunte en
  su momento, no una incertidumbre introducida acá.
- Reglas 12-14 tienen partes ambiguas sobre si un cuerpo/punto es Natal o
  de la Revolución (el texto no lo aclara en todos los casos). Se optó,
  de forma consistente con el resto de las reglas 1-10 (donde el cuerpo
  sin aclaración de "de revo" siempre es Natal), por tomar Plutón/Nodo/
  Venus/Mercurio/Sol/Marte NATALES contra el MC/Vértex/Sol DE LA
  REVOLUCIÓN. Se marca cada resultado con esta convención explícita.
- La misma imagen trae, después de la regla de Embarazo, una nota general
  (no una regla con aspecto/objetivo definido, no se reconstruye como tal):
  "Un planeta no me asusta un planeta en 6, 8, 12. Pero cuando en una Revo
  dentro de un grado de orbe en todo, hay aspectos disociativos al MC, al
  vértex o al ecuador celeste o al ascendente estamos complicados de
  verdad" — un criterio cualitativo de alerta general (aspectos disociativos
  de cualquier tipo, dentro de 1° de orbe, a los ángulos de la Revolución),
  no una regla puntual con cuerpo/aspecto fijo como las demás.
- Los puntos angulares de referencia (Asc, MC, Vértex, Ecuador Celeste,
  Rueda de Fortuna) de las reglas 1-10 se usan siempre NATALES y
  Trópicos/Geocéntricos (el punto angular de comparación, no el cuerpo en
  movimiento) — Bonito no aclara una variante sideral/helio para ellos en
  este documento, a diferencia del cuerpo que sí varía.
- Orbe: 2° (convención de Bonito para aspectos que involucran un punto
  angular/cúspide, la misma que usa el resto del proyecto — ORBE_CUSPIDE).
"""
from astro import cuerpo_base_lon, carta_natal_simple, jd_from_local, _diff_angular, ORBE_CUSPIDE

ASPECTOS_EVENTOS = {
    "Conjunción": 0, "Semicuadratura": 45, "Sextil": 60, "Cuadratura": 90,
    "Trígono": 120, "Sesquicuadratura": 135, "Oposición": 180,
}

# (helio, sideral) — las 4 combinaciones posibles
GEO_TROP = (False, False)
GEO_SID = (False, True)
HELIO_TROP = (True, False)
HELIO_SID = (True, True)
TODAS_LAS_VARIANTES = [GEO_TROP, GEO_SID, HELIO_TROP, HELIO_SID]
SOLO_TROP_SID = [GEO_TROP, GEO_SID]  # cuando el texto no menciona Helio/Geo

ETIQUETA_VARIANTE = {
    GEO_TROP: "Geocéntrico Trópico", GEO_SID: "Geocéntrico Sideral",
    HELIO_TROP: "Heliocéntrico Trópico", HELIO_SID: "Heliocéntrico Sideral",
}

REGLAS_EVENTOS = [
    {"id": 1, "nombre": "Inicio de noviazgo", "cuerpo": "PLUTON", "variantes": SOLO_TROP_SID,
     "objetivos": ["ascendente", "ecuador_celeste"], "aspectos": ["Conjunción", "Sextil", "Trígono"],
     "cita": "Plutón Tropical o Sideral (natal, Rev solar) en conjunción, sextil o trígono con el Asc o Ecuador celeste."},
    {"id": 2, "nombre": "Nacimiento de un hijo", "cuerpo": "MERCURIO", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["mc", "vertex", "ascendente", "ecuador_celeste"], "aspectos": ["Oposición"],
     "cita": "Mercurio Tropical o Sideral, Geocéntrico o Heliocéntrico (Natal, Rev Solar) en oposición al MC o al Vertex, al Asc o Eq."},
    {"id": 3, "nombre": "Cirugía", "cuerpo": "MARTE", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["ascendente", "ecuador_celeste"], "aspectos": ["Oposición"],
     "cita": "Marte Tropical o Sideral, Geocéntrico o Heliocéntrico (Natal, Rev solar) oposición al Asc o Eq."},
    {"id": 4, "nombre": "Divorcio o separación", "cuerpo": "PLUTON", "variantes": SOLO_TROP_SID,
     "objetivos": ["ascendente", "ecuador_celeste"], "aspectos": ["Cuadratura", "Sesquicuadratura"],
     "cita": "Plutón Tropical o Sideral (Natal, Rev Solar) en cuadratura o sesquicuadratura al Asc o Eq."},
    {"id": "5a", "nombre": "Ingreso de dinero / mejoran finanzas (Saturno)", "cuerpo": "SATURNO", "variantes": SOLO_TROP_SID,
     "objetivos": ["ascendente", "ecuador_celeste", "mc"], "aspectos": ["Cuadratura", "Sesquicuadratura"],
     "cita": "Saturno o Urano Tropical o Sideral, Natal (Rev Solar), en cuadratura o sesquicuadratura al Asc o Eq o MC."},
    {"id": "5b", "nombre": "Ingreso de dinero / mejoran finanzas (Urano)", "cuerpo": "URANO", "variantes": SOLO_TROP_SID,
     "objetivos": ["ascendente", "ecuador_celeste", "mc"], "aspectos": ["Cuadratura", "Sesquicuadratura"],
     "cita": "Saturno o Urano Tropical o Sideral, Natal (Rev Solar), en cuadratura o sesquicuadratura al Asc o Eq o MC."},
    {"id": 6, "nombre": "Solución a problema judicial", "cuerpo": "JUPITER", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["mc", "ecuador_celeste"], "aspectos": ["Cuadratura"],
     "cita": "Júpiter Tropical o Sideral, Geocéntrico o Heliocéntrico (Natal, Rev Solar) en cuadratura al MC o Eq."},
    {"id": "7a", "nombre": "Mudanzas (Sol)", "cuerpo": "SOL", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["mc", "ecuador_celeste", "vertex"], "aspectos": ["Oposición"],
     "cita": "Sol o Marte Tropical o Sideral, Geocéntrico o Heliocéntrico (Natal, Rev Solar) en oposición al MC o Eq o Vertex."},
    {"id": "7b", "nombre": "Mudanzas (Marte)", "cuerpo": "MARTE", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["mc", "ecuador_celeste", "vertex"], "aspectos": ["Oposición"],
     "cita": "Sol o Marte Tropical o Sideral, Geocéntrico o Heliocéntrico (Natal, Rev Solar) en oposición al MC o Eq o Vertex."},
    {"id": 8, "nombre": "Víctima de envidia / pérdidas financieras / salud familiar", "cuerpo": "NEPTUNO", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["mc", "vertex"], "aspectos": ["Cuadratura", "Semicuadratura", "Sesquicuadratura"],
     "cita": "Neptuno Tropical o Sideral, Geo o Helio (Natal, Rev solar) cuadratura, semicuadratura o sesquicuadratura al MC o Vertex."},
    {"id": 9, "nombre": "Alejamiento o pérdida de figura masculina", "cuerpo": "SOL", "variantes": SOLO_TROP_SID,
     "objetivos": ["rueda_de_la_fortuna"], "aspectos": ["Conjunción", "Trígono"],
     "cita": "Alejamiento o pérdida de figura masculina con el Sol (Natal, Rev solar) en conjunción o trígono con Fortuna."},
    {"id": 10, "nombre": "Inversión inmobiliaria importante", "cuerpo": "JUPITER", "variantes": TODAS_LAS_VARIANTES,
     "objetivos": ["rueda_de_la_fortuna"], "aspectos": ["Conjunción", "Sextil", "Trígono"],
     "cita": "INVERSIÓN INMOBILIARIA IMPORTANTE: Júpiter (natal, rev solar) en conjunción, sextil o trígono con Fortuna."},
]

# Reglas 12-14: aspectos INTERNOS de la Revolución Solar (contra sus propios
# ángulos) o de un cuerpo NATAL contra un ángulo DE LA REVOLUCIÓN — requieren
# obligatoriamente una carta de Revolución Solar (no aplican a la Natal sola).
REGLAS_REVOLUCION_SOLAR = [
    {"id": 11, "nombre": "Pérdida del padre", "aspectos_grados": [90],
     "cita": "Pérdida del padre: Absolutamente siempre el MC de la revolución solar va a estar 90 grados del sol.",
     "descripcion": "MC de la Revolución Solar en cuadratura (90°) con el Sol NATAL (sin 'de revo' aclarado, se "
                     "toma Natal, misma convención del resto de las reglas)."},
    {"id": 12, "nombre": "Viudez", "aspectos_grados": [90, 45, 135],
     "cita": "Viudez: cuando el sol de revo está a 90, a 45 o 135 del medio cielo de revo o vertex.",
     "descripcion": "Sol de la Revolución Solar a 90°, 45° o 135° del MC de la Revolución o del Vértex de la Revolución."},
    {"id": 13, "nombre": "Divorciada", "aspectos_grados": [0, 60, 120],
     "cita": "Divorciada: Cuando el asc de revo está en conjunción, sextil o trígono con Plutón (nota de la propia "
             "persona que transcribió la clase: 'Esto lo dijo así pero para mí se equivocó porque después abajo "
             "escribí otra cosa').",
     "descripcion": "Ascendente de la Revolución Solar en conjunción, sextil o trígono con el Plutón NATAL "
                     "(el texto no aclara si el Plutón es natal o de revo; se usa el natal, igual que el resto de "
                     "las reglas de este módulo cuando no se aclara 'de revo'). Bonito mismo dejó esta regla en "
                     "duda según la nota de quien tomó el apunte en la clase."},
    {"id": 14, "nombre": "Embarazo", "aspectos_grados": [180],
     "cita": "Embarazo: El nodo, Venus, Mercurio o el Sol o Marte están en oposición al medio cielo de revo o al vertex.",
     "descripcion": "Nodo, Venus, Mercurio, Sol o Marte NATALES en oposición al MC de la Revolución Solar o al "
                     "Vértex de la Revolución Solar (mismo criterio: cuerpos natales salvo que se diga 'de revo')."},
]

NO_IMPLEMENTADAS = []


def _lon_variantes(jd, cuerpo, combos):
    out = {}
    for combo in combos:
        lon, _ = cuerpo_base_lon(jd, cuerpo, helio=combo[0], sideral=combo[1])
        out[ETIQUETA_VARIANTE[combo]] = lon
    return out


def _chequear_aspecto(lon_cuerpo, lon_objetivo, aspectos_nombres, orbe=ORBE_CUSPIDE):
    diff = abs(_diff_angular(lon_cuerpo, lon_objetivo))
    mejor = None
    for nombre in aspectos_nombres:
        angulo = ASPECTOS_EVENTOS[nombre]
        delta = abs(diff - angulo)
        if delta <= orbe and (mejor is None or delta < mejor["orbe"]):
            mejor = {"aspecto": nombre, "orbe": round(delta, 4)}
    return mejor


def evaluar_eventos_vida(carta_natal_dict, jd_natal, jd_revo=None, anio_revo=None,
                          carta_revo_dict=None, orbe=ORBE_CUSPIDE):
    """Corre las reglas 1-10 contra la carta Natal (siempre) y, si se pasa
    jd_revo (Día Juliano de una Revolución Solar ya calculada — ver
    revolucion.revolucion_solar), también contra esa Revolución. Los
    ángulos objetivo (Asc/MC/Vértex/Eq/Fortuna) son siempre los NATALES.
    carta_natal_dict = salida de astro.carta_natal_simple."""
    resultados = []
    contextos = [("Natal", jd_natal)]
    if jd_revo is not None:
        contextos.append((f"Revolución Solar {anio_revo}" if anio_revo else "Revolución Solar", jd_revo))

    for regla in REGLAS_EVENTOS:
        for nombre_contexto, jd_ctx in contextos:
            lons = _lon_variantes(jd_ctx, regla["cuerpo"], regla["variantes"])
            for variante, lon_cuerpo in lons.items():
                for objetivo in regla["objetivos"]:
                    punto = carta_natal_dict.get(objetivo)
                    if not punto:
                        continue
                    hit = _chequear_aspecto(lon_cuerpo, punto["lon"], regla["aspectos"], orbe)
                    if hit:
                        resultados.append({
                            "regla_id": regla["id"], "nombre": regla["nombre"],
                            "contexto": nombre_contexto, "cuerpo": regla["cuerpo"], "variante": variante,
                            "objetivo": objetivo, "aspecto": hit["aspecto"], "orbe": hit["orbe"],
                            "cita": regla["cita"],
                        })

    # Reglas 11-14: solo si hay Revolución Solar
    if carta_revo_dict is not None:
        sol_revo = carta_revo_dict["sol"]["lon"]
        mc_revo = carta_revo_dict["mc"]["lon"]
        vertex_revo = carta_revo_dict["vertex"]["lon"]
        asc_revo = carta_revo_dict["ascendente"]["lon"]

        # Regla 11 — Pérdida del padre: MC de revo en cuadratura (90°) con el Sol NATAL
        sol_natal, _ = cuerpo_base_lon(jd_natal, "SOL")
        hit = _chequear_aspecto(mc_revo, sol_natal, ["Cuadratura"], orbe)
        if hit:
            resultados.append({"regla_id": 11, "nombre": "Pérdida del padre", "contexto": "Revolución Solar",
                                "cuerpo": "MC de revo", "variante": "—", "objetivo": "Sol natal",
                                "aspecto": hit["aspecto"], "orbe": hit["orbe"],
                                "cita": REGLAS_REVOLUCION_SOLAR[0]["cita"]})

        # Regla 12 — Viudez: Sol de revo a 90/45/135 del MC de revo o Vértex de revo
        for nombre_obj, lon_obj in (("MC de revo", mc_revo), ("Vértex de revo", vertex_revo)):
            diff = abs(_diff_angular(sol_revo, lon_obj))
            for grado in (90, 45, 135):
                delta = abs(diff - grado)
                if delta <= orbe:
                    resultados.append({"regla_id": 12, "nombre": "Viudez", "contexto": "Revolución Solar",
                                        "cuerpo": "Sol de revo", "variante": "—", "objetivo": nombre_obj,
                                        "aspecto": f"{grado}°", "orbe": round(delta, 4),
                                        "cita": REGLAS_REVOLUCION_SOLAR[1]["cita"]})

        # Regla 13 — Divorciada: Asc de revo conjunción/sextil/trígono con Plutón NATAL
        pluton_natal, _ = cuerpo_base_lon(jd_natal, "PLUTON")
        hit = _chequear_aspecto(asc_revo, pluton_natal, ["Conjunción", "Sextil", "Trígono"], orbe)
        if hit:
            resultados.append({"regla_id": 13, "nombre": "Divorciada", "contexto": "Revolución Solar",
                                "cuerpo": "Asc de revo", "variante": "—", "objetivo": "Plutón natal",
                                "aspecto": hit["aspecto"], "orbe": hit["orbe"],
                                "cita": REGLAS_REVOLUCION_SOLAR[2]["cita"]})

        # Regla 14 — Embarazo: Nodo/Venus/Mercurio/Sol/Marte NATALES en oposición a MC de revo o Vértex de revo
        for cuerpo_n in ("NODO", "VENUS", "MERCURIO", "SOL", "MARTE"):
            lon_n, _ = cuerpo_base_lon(jd_natal, cuerpo_n)
            for nombre_obj, lon_obj in (("MC de revo", mc_revo), ("Vértex de revo", vertex_revo)):
                hit = _chequear_aspecto(lon_n, lon_obj, ["Oposición"], orbe)
                if hit:
                    resultados.append({"regla_id": 14, "nombre": "Embarazo", "contexto": "Revolución Solar",
                                        "cuerpo": f"{cuerpo_n.capitalize()} natal", "variante": "—",
                                        "objetivo": nombre_obj, "aspecto": hit["aspecto"], "orbe": hit["orbe"],
                                        "cita": REGLAS_REVOLUCION_SOLAR[3]["cita"]})

    resultados.sort(key=lambda r: r["orbe"])
    return {
        "total": len(resultados),
        "resultados": resultados,
        "no_implementadas": NO_IMPLEMENTADAS,
        "nota": ("Reglas generales de eventos de vida de Hugo Bonito (dos documentos mecanografiados hallados "
                 "junto al material gráfico) — no es una técnica de escaneo temporal, es un chequeo de aspectos "
                 "fijos sobre la carta Natal y, si se indicó año, la Revolución Solar de ese año. Orbe 2°. "
                 "Ver eventos_vida.py para el detalle de cada regla, sus citas textuales y la única duda que deja "
                 "la fuente (la regla de 'Divorciada', señalada como dudosa por la propia persona que tomó el "
                 "apunte de la clase de Hugo)."),
    }
