# -*- coding: utf-8 -*-
"""
Discriminación de cartas casi idénticas por orbe — Hugo Bonito.

Reconstruido de una transcripción de clase (fuente: "964c7b6f-attachment.txt")
sobre el caso real de dos hermanas/mellizas, JAZMÍN y SOFÍA, cuyos horarios
de nacimiento son casi idénticos (22:51:38 vs 22:50:12 — un minuto y pico
de diferencia). Por tener datos de nacimiento tan cercanos, sus Fechas
Gemelas (Retornos de Plutón) caen en fechas casi paralelas: la posición
número N de una prácticamente corresponde en el tiempo a la posición N de
la otra. Bonito arma, para cada una, una carta COMPLETA en cada retorno
(Sol, Luna, Ascendente, Medio Cielo, Vértex, Ecuador Celeste, Rueda de la
Fortuna, los planetas Venus/Marte/Júpiter/Saturno/Urano/Neptuno, Quirón y
el Nodo — no solo Sol/Luna/ángulos como en la 'carta muerta' básica) y,
POSICIÓN POR POSICIÓN, compara los mismos aspectos (misma pareja de
puntos, mismo tipo de aspecto) en ambas cartas. Su regla explícita:

  "Encontramos un Medio Cielo en cuadratura con Venus... la cuadratura
  está a 1 minuto de arco [en la carta de Sofía]... quiere decir que el
  Medio Cielo cuadrado Venus le corresponde a Jazmín [porque en la suya
  el orbe es más chico] y que a Sofía le corresponde [la interpretación
  del] Urano [en esa] posición del Medio Cielo, porque ahí encontramos
  que el aspecto más cerrado es de Urano."

Es decir: cuando dos personas con datos de nacimiento casi idénticos
comparten en la práctica "la misma" Fecha Gemela número N, el aspecto que
la describe realmente a CADA UNA se decide por CUÁL DE LAS DOS TIENE EL
ORBE MÁS CERRADO (más exacto) para ese aspecto — el orbe más chico "gana"
la atribución de esa lectura a esa persona. Cuando ambas tienen el mismo
aspecto con el mismo orbe (o casi), Bonito lo anota como "sin
modificación" (el rasgo es compartido, no discrimina entre ellas).

RECONSTRUCCIÓN HONESTA:
- Bonito también menciona Quirón y el Nodo en sus aspectos ("Asc
  quincuncio Quirón", "Asc trígono Nodo") — al principio no estaban
  implementados en el resto del proyecto, así que se agregaron a
  CUERPOS_BASE (astro.py): Quirón (swe.CHIRON, requiere el archivo de
  asteroides seas_18.se1 — se descargó de la distribución oficial de
  Astrodienst/JPL y se agregó a ephe/, porque sin él Quirón no se puede
  calcular en absoluto, ni siquiera con el motor Moshier) y el Nodo
  (swe.MEAN_NODE, el "nodo medio", el que usaba la mayoría del software
  de la época de Bonito incluido Winstar — puramente analítico, no
  necesita archivo). También se agregó Venus a CUERPOS_BASE, que tampoco
  estaba, y era necesario para el ejemplo real de Bonito (MC cuadratura
  Venus).
- Las 8 posiciones de ejemplo de Bonito ("A1 a A8", "B1 a B8") no
  necesariamente enumeran EL MISMO conjunto de retornos en el mismo
  orden que este proyecto calcula (por ejemplo, retornos tropicales
  cronológicos vs. algún otro orden manual de Winstar). Acá se emparejan
  por ÍNDICE dentro de la MISMA variante (geo_tropico por defecto) de
  cada persona — es la lectura más simple y fiel al criterio de fondo
  ("casi la misma fecha, casi la misma posición"), pero puede no coincidir
  1 a 1 exactamente con el orden que Bonito tenía a mano en su planilla ya
  armada.
"""
from astro import cuerpo_base_lon, calcular_fechas_gemelas, sign_of, _diff_angular
from puntos import puntos_angulares, puntos_angulares_sideral, rueda_de_la_fortuna, es_diurna

PLANETAS_EXTRA = ["VENUS", "MARTE", "JUPITER", "SATURNO", "URANO", "NEPTUNO", "QUIRON", "NODO"]

# Mismo set de aspectos "finos" que usa horaria.py — Bonito los usa acá
# también (sextil, cuadratura, trígono, semicuadratura, sesquicuadratura,
# quincuncio, oposición, conjunción, semisextil)
ASPECTOS_DISCRIMINACION = {
    "Conjunción": 0, "Semisextil": 30, "Semicuadratura": 45, "Sextil": 60,
    "Cuadratura": 90, "Trígono": 120, "Sesquicuadratura": 135,
    "Quincuncio": 150, "Oposición": 180,
}


def _punto(lon):
    signo, grado = sign_of(lon)
    return {"lon": lon, "signo": signo, "grado": round(grado, 4)}


def carta_retorno_completa(jd, lat, lon, sideral=False):
    """Carta completa (no solo Sol/Luna/ángulos) para el instante y lugar
    de un retorno puntual: Ascendente, Medio Cielo, Vértex, Ecuador
    Celeste, Rueda de la Fortuna, Sol, Luna, los planetas Venus a Neptuno,
    Quirón y el Nodo — todos los puntos que Bonito compara en este tramo
    de clase."""
    angulos = puntos_angulares_sideral(jd, lat, lon) if sideral else puntos_angulares(jd, lat, lon)
    sol_lon, _ = cuerpo_base_lon(jd, "SOL", sideral=sideral)
    luna_lon, _ = cuerpo_base_lon(jd, "LUNA", sideral=sideral)
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)

    puntos = {
        "Ascendente": angulos["ascendente"]["lon"], "Medio Cielo": angulos["mc"]["lon"],
        "Vértex": angulos["vertex"]["lon"], "Ecuador Celeste": angulos["ecuador_celeste"]["lon"],
        "Rueda de la Fortuna": fortuna["lon"],
        "Sol": sol_lon, "Luna": luna_lon,
    }
    for nombre in PLANETAS_EXTRA:
        try:
            lon_p, _ = cuerpo_base_lon(jd, nombre, sideral=sideral)
            puntos[nombre.capitalize()] = lon_p
        except Exception:
            # Quirón necesita archivos de asteroides por bloques de ~600
            # años (seas_12/18/...); si el retorno cae fuera de los
            # bloques incluidos en ephe/, se omite SOLO ese punto en esa
            # posición puntual en vez de abortar toda la comparación —
            # el resto de los puntos (Sol/Luna/ángulos/planetas/Nodo)
            # sigue comparándose igual.
            continue
    return puntos


def _todos_los_aspectos(carta, orbe_max=1.0):
    """Todos los aspectos (de ASPECTOS_DISCRIMINACION, dentro de orbe_max
    grados) entre cada par de puntos de una carta puntual. Clave =
    (puntoA, puntoB, nombre_aspecto) para poder cruzarlos con la otra
    carta más adelante."""
    nombres = list(carta.keys())
    aspectos = {}
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            pA, pB = nombres[i], nombres[j]
            d = abs(_diff_angular(carta[pA], carta[pB]))
            mejor = None
            for nombre_asp, angulo in ASPECTOS_DISCRIMINACION.items():
                diff = abs(d - angulo)
                if diff <= orbe_max and (mejor is None or diff < mejor[1]):
                    mejor = (nombre_asp, diff)
            if mejor:
                aspectos[(pA, pB, mejor[0])] = round(mejor[1], 4)
    return aspectos


def comparar_por_orbe(cartaA, cartaB, nombreA="A", nombreB="B", orbe_max=1.0):
    """Compara los aspectos internos de dos cartas puntuales (p.ej. la
    misma posición de retorno de dos personas con datos de nacimiento
    casi idénticos) y, para cada aspecto (misma pareja de puntos, mismo
    tipo) presente en AMBAS dentro de orbe_max, dice a cuál de las dos le
    'corresponde' — la de orbe más chico, criterio explícito de Bonito."""
    aspectos_A = _todos_los_aspectos(cartaA, orbe_max)
    aspectos_B = _todos_los_aspectos(cartaB, orbe_max)
    resultados = []
    for clave in sorted(set(aspectos_A) & set(aspectos_B)):
        puntoA, puntoB, nombre_asp = clave
        orbeA, orbeB = aspectos_A[clave], aspectos_B[clave]
        if orbeA < orbeB - 1e-6:
            ganador = nombreA
        elif orbeB < orbeA - 1e-6:
            ganador = nombreB
        else:
            ganador = "empate (sin diferencia — rasgo compartido)"
        resultados.append({
            "puntos": f"{puntoA} {nombre_asp} {puntoB}",
            f"orbe_{nombreA}": orbeA, f"orbe_{nombreB}": orbeB,
            "corresponde_a": ganador,
        })
    resultados.sort(key=lambda r: min(r[f"orbe_{nombreA}"], r[f"orbe_{nombreB}"]))
    return resultados


def discriminar_por_orbe(personaA, personaB, nombreA="A", nombreB="B",
                          variante="geo_tropico", anios_atras=250, anios_adelante=250,
                          orbe_max=1.0):
    """Técnica completa de Bonito: arma las Fechas Gemelas de dos personas
    con datos de nacimiento MUY cercanos (mellizas/hermanas nacidas casi
    a la misma hora), empareja sus retornos por ÍNDICE dentro de la misma
    variante (sus ciclos de Plutón caen casi en paralelo por tener
    horarios tan próximos) y en cada posición compara, por orbe, a cuál
    de las dos le corresponde cada aspecto compartido."""
    sideral = "sideral" in variante
    fgA = calcular_fechas_gemelas(
        personaA["year"], personaA["month"], personaA["day"], personaA["hour"], personaA["minute"],
        personaA["utc_offset"], anios_atras=anios_atras, anios_adelante=anios_adelante,
        lat=personaA["lat"], lon=personaA["lon"])
    fgB = calcular_fechas_gemelas(
        personaB["year"], personaB["month"], personaB["day"], personaB["hour"], personaB["minute"],
        personaB["utc_offset"], anios_atras=anios_atras, anios_adelante=anios_adelante,
        lat=personaB["lat"], lon=personaB["lon"])
    listaA, listaB = fgA[variante], fgB[variante]
    n = min(len(listaA), len(listaB))

    posiciones = []
    for i in range(n):
        entradaA, entradaB = listaA[i], listaB[i]
        cartaA = carta_retorno_completa(entradaA["jd"], personaA["lat"], personaA["lon"], sideral=sideral)
        cartaB = carta_retorno_completa(entradaB["jd"], personaB["lat"], personaB["lon"], sideral=sideral)
        aspectos = comparar_por_orbe(cartaA, cartaB, nombreA, nombreB, orbe_max)
        if aspectos:
            posiciones.append({
                "posicion": i + 1,
                f"fecha_{nombreA}": entradaA["fecha_local"], f"fecha_{nombreB}": entradaB["fecha_local"],
                "aspectos": aspectos,
            })

    return {
        "variante": variante, "total_posiciones_comparadas": n,
        "posiciones_con_coincidencias": len(posiciones), "posiciones": posiciones,
        "nota": ("Técnica de Bonito para discriminar entre dos cartas casi idénticas (por ej. "
                 "mellizas con horarios muy próximos): en cada posición de retorno emparejada por "
                 "índice, cuando ambas cartas comparten el mismo aspecto (misma pareja de puntos, "
                 "mismo tipo), el orbe más chico ('más cerrado') decide a cuál de las dos personas "
                 "le corresponde esa lectura. Un empate señala un rasgo compartido, sin "
                 "diferenciación entre ambas. Incluye Quirón (necesita el archivo de asteroides "
                 "seas_18.se1, incluido en ephe/) y el Nodo medio, además de Sol/Luna/ángulos y "
                 "los planetas Venus a Neptuno."),
    }
