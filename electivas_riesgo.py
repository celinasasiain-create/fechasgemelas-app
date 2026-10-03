# -*- coding: utf-8 -*-
"""
Electivas de riesgo y Manchas Solares — Hugo Bonito.

Reconstruido de una transcripción de clase (fuente: "2941af3e-attachment.txt")
donde Bonito muestra, en el mismo tramo, DOS aplicaciones de una misma
técnica: comparar el SOL real en tránsito (rápido) contra un banco de
grados de referencia, DENTRO de una ventana horaria corta (2 horas en su
ejemplo: 18 a 20hs), buscando TODOS los aspectos mayores exactos — no
solo la conjunción, como en Programa Omega/Imantación, sino también
sextil, cuadratura, trígono, semicuadratura, sesquicuadratura y oposición.

1) ELECTIVA DE RIESGO ("¿es buen momento para actuar?"): el banco es la
   posición ACTUAL (geocéntrica o heliocéntrica — Bonito: "da lo mismo
   que sean las posiciones de Plutón geocéntrica o heliocéntrica") de un
   planeta lento de referencia (Plutón en su ejemplo). El tránsito es el
   Sol real moviéndose durante la ventana. Su criterio: sextil/trígono =
   "aspecto bueno"; cuadratura, semicuadratura, sesquicuadratura =
   "aspecto malo, no conviene usar ese momento". Además, su propio
   criterio operativo explícito: "si hay un aspecto bueno muy cerca de
   uno hostil, no conviene utilizarlo" — un buen aspecto solo sirve si no
   tiene un aspecto malo pisándole los talones en el tiempo.

2) MANCHAS SOLARES (riesgo de actividad solar / interferencia en
   comunicaciones): el banco es TODOS los Soles de las Fechas Gemelas
   (cadena de Retornos de Plutón, las 4 variantes) de una carta de
   referencia. El tránsito es el Sol real. Bonito es taxativo: "las
   fechas gemelas te permiten manchas solares SOLO cuando un sol está a
   180 grados. Un sol de fechas gemelas con otro hace 180 grados" — el
   ÚNICO aspecto que cuenta para esta técnica puntual es la OPOSICIÓN
   exacta (partil) entre el Sol real y un Sol del banco. En su caso real
   encontró una oposición partil (3 minutos de arco) e interpretó: "en
   algunas horas esas manchas solares... llegan a la Tierra y complican
   las comunicaciones" — no da una fórmula fija de cuántas horas en este
   tramo de clase.

RECONSTRUCCIÓN HONESTA: se reutiliza el mismo motor de bisección exacta
de Programa Omega/Imantación, generalizado para buscar CUALQUIER ángulo
de aspecto (antes esa generalización, ASPECTOS_HORARIA, solo existía en
horaria.py para una carta ESTÁTICA/puntual; acá se aplica a una ventana
horaria corta con búsqueda de cruces reales, como en Omega). El "banco de
un solo planeta lento" (Plutón geo/helio 'ahora') se recalcula
dinámicamente en cada instante de la ventana en vez de tomar solo los 2
valores manuales de los extremos (18h/20h) como hacía Bonito a mano en
Excel — la diferencia numérica es insignificante (Plutón mueve fracciones
de segundo de arco en 2 horas), así que esto no es una sustitución de
método, es la misma aproximación sin el paso manual de copiar 2 valores.
"""
from astro import _diff_angular, jd_to_local, cuerpo_base_lon, calcular_fechas_gemelas

EPS = 1e-4

# Aspectos que Bonito usa para "electiva de riesgo" en este tramo de clase
ASPECTOS_ELECTIVA = {
    "Sextil": 60, "Trígono": 120,                                    # buenos
    "Semicuadratura": 45, "Cuadratura": 90, "Sesquicuadratura": 135,  # malos
}
FAMILIA_ELECTIVA = {
    "Sextil": "bueno", "Trígono": "bueno",
    "Semicuadratura": "malo", "Cuadratura": "malo", "Sesquicuadratura": "malo",
}


def _buscar_cruce_en_ventana(jd_ini, jd_fin, objetivo_fn, cuerpo,
                              helio=False, sideral=False, paso_segundos=20):
    """Busca TODOS los cruces exactos (conjunción, 0°) de 'cuerpo' en
    tránsito real contra la posición dada por objetivo_fn(jd) dentro de
    [jd_ini, jd_fin] — bisección + verificación EPS (evita el bug de
    antípoda de _diff_angular). Es el bloque de base que reutilizan tanto
    la búsqueda de conjunción pura como la de cualquier otro aspecto (ver
    _buscar_aspecto_en_ventana), apuntando cada vez a un objetivo distinto
    (el grado del banco desplazado por el ángulo del aspecto)."""
    paso = paso_segundos / 86400.0

    def f(jd_):
        lon, _spd = cuerpo_base_lon(jd_, cuerpo, helio=helio, sideral=sideral)
        return _diff_angular(lon, objetivo_fn(jd_))

    resultados = []
    jd = jd_ini
    prev = f(jd)
    while jd < jd_fin:
        jd_next = min(jd + paso, jd_fin)
        curr = f(jd_next)
        if (prev > 0) != (curr > 0):
            lo, hi, dlo = jd, jd_next, prev
            for _ in range(40):
                mid = (lo + hi) / 2
                dmid = f(mid)
                if (dmid > 0) == (dlo > 0):
                    lo, dlo = mid, dmid
                else:
                    hi = mid
            raiz = (lo + hi) / 2
            if abs(f(raiz)) < EPS:
                resultados.append(raiz)
        prev, jd = curr, jd_next
        if jd >= jd_fin:
            break
    return resultados


def _buscar_aspecto_en_ventana(jd_ini, jd_fin, objetivo_fn, angulo, cuerpo,
                                helio=False, sideral=False, paso_segundos=20):
    """Busca TODOS los instantes en que 'cuerpo' en tránsito real forma el
    aspecto 'angulo' con la posición dada por objetivo_fn(jd) dentro de
    [jd_ini, jd_fin]. NOTA TÉCNICA: para un ángulo A, el aspecto exacto
    ocurre cuando el cuerpo pasa por objetivo+A o por objetivo-A (dos
    puntos distintos del cielo, salvo A=0 o A=180 donde ambos coinciden
    en un único punto). Buscarlo comparando abs(diferencia)-A y esperando
    un cambio de signo FALLA para A=180 (oposición): abs(diferencia) tiene
    un máximo de 180, así que solo "toca" ese valor tangencialmente en el
    punto exacto, sin cruzar — nunca hay cambio de signo y la oposición
    quedaba sin detectarse. Por eso acá se buscan directamente los cruces
    (conjunción, cambio de signo genuino) contra cada uno de los 1 o 2
    puntos absolutos del aspecto, en vez de trabajar con el valor
    absoluto del ángulo."""
    if angulo <= 0 or angulo >= 180:
        objetivos = [lambda jd_, a=angulo: objetivo_fn(jd_) + a]
    else:
        objetivos = [lambda jd_, a=angulo: objetivo_fn(jd_) + a,
                     lambda jd_, a=angulo: objetivo_fn(jd_) - a]
    resultados = []
    for obj_fn in objetivos:
        resultados += _buscar_cruce_en_ventana(jd_ini, jd_fin, obj_fn, cuerpo,
                                                helio=helio, sideral=sideral,
                                                paso_segundos=paso_segundos)
    return sorted(resultados)


def escanear_electiva(jd_ini, jd_fin, utc_offset_salida, cuerpo_banco="PLUTON",
                       helio_banco=False, sideral_banco=False, cuerpo_transito="SOL",
                       paso_segundos=20):
    """Electiva de riesgo de Bonito: escanea [jd_ini, jd_fin] buscando
    aspectos exactos (sextil/trígono = bueno; semicuadratura/cuadratura/
    sesquicuadratura = malo) entre 'cuerpo_transito' (Sol por defecto) y
    la posición real y dinámica de 'cuerpo_banco' (Plutón geocéntrico por
    defecto). Marca cuándo un buen aspecto cae 'pisado' en el tiempo por
    uno malo (=no conviene usar ese momento, criterio explícito de
    Bonito)."""
    def objetivo_fn(jd_):
        lon, _spd = cuerpo_base_lon(jd_, cuerpo_banco, helio=helio_banco, sideral=sideral_banco)
        return lon

    eventos = []
    for nombre_asp, angulo in ASPECTOS_ELECTIVA.items():
        for jd in _buscar_aspecto_en_ventana(jd_ini, jd_fin, objetivo_fn, angulo,
                                              cuerpo_transito, paso_segundos=paso_segundos):
            eventos.append({
                "hora_local": jd_to_local(jd, utc_offset_salida),
                "aspecto": nombre_asp, "calidad": FAMILIA_ELECTIVA[nombre_asp],
                "cuerpo_transito": cuerpo_transito.capitalize(),
                "cuerpo_banco": cuerpo_banco.capitalize(),
                "modo_banco": "Heliocéntrico" if helio_banco else "Geocéntrico",
            })
    def _clave_fecha(hl):
        return (hl["year"], hl["month"], hl["day"], hl["hour"], hl["minute"], hl["second"])

    def _minutos_totales(hl):
        # minutos desde una época arbitraria fija — sirve para comparar
        # cercanía en el TIEMPO real (no solo la hora del día) entre dos
        # eventos que pueden caer en fechas distintas si la ventana es larga.
        return ((hl["year"] * 372 + hl["month"] * 31 + hl["day"]) * 1440
                + hl["hour"] * 60 + hl["minute"] + hl["second"] / 60.0)

    eventos.sort(key=lambda e: _clave_fecha(e["hora_local"]))

    UMBRAL_MINUTOS = 15  # propio de esta reconstrucción — Bonito no dio un número fijo
    for ev in eventos:
        if ev["calidad"] != "bueno":
            continue
        ev["usable"] = True
        ti = _minutos_totales(ev["hora_local"])
        for otro in eventos:
            if otro["calidad"] != "malo":
                continue
            tj = _minutos_totales(otro["hora_local"])
            if abs(ti - tj) <= UMBRAL_MINUTOS:
                ev["usable"] = False
                break

    return {
        "total_eventos": len(eventos), "eventos": eventos,
        "nota": ("Criterio de Bonito: sextil/trígono son aspectos 'buenos' (momento favorable "
                 "para actuar); cuadratura/semicuadratura/sesquicuadratura son 'malos' (mejor no "
                 "usar ese momento). Un aspecto bueno muy cerca en el tiempo (< 15 min — umbral "
                 "propio de esta reconstrucción) de uno malo se marca 'usable: false': 'si está "
                 "muy cerquita de un aspecto hostil, no conviene utilizarlo'."),
    }


def escanear_manchas_solares(entidad, jd_ini, jd_fin, utc_offset_salida,
                              anios_atras=150, anios_adelante=150, paso_segundos=20):
    """Técnica de Manchas Solares de Bonito: arma el banco de TODOS los
    Soles de las Fechas Gemelas (Retornos de Plutón, 4 variantes) de una
    carta de referencia, y escanea [jd_ini, jd_fin] buscando los
    instantes en que el Sol REAL en tránsito hace OPOSICIÓN exacta (180°,
    partil) con algún Sol del banco — el único aspecto que Bonito usa
    para esta técnica puntual."""
    fechas_gemelas = calcular_fechas_gemelas(
        entidad["year"], entidad["month"], entidad["day"],
        entidad["hour"], entidad["minute"], entidad["utc_offset"],
        anios_atras=anios_atras, anios_adelante=anios_adelante)
    banco = []
    for variante, lista in fechas_gemelas.items():
        for entrada in lista:
            banco.append({"grado": entrada["sol"]["lon"], "variante": variante,
                           "fecha_origen": entrada["fecha_local"]})

    eventos = []
    for item in banco:
        def objetivo_fn(jd_, g=item["grado"]):
            return g
        for jd in _buscar_aspecto_en_ventana(jd_ini, jd_fin, objetivo_fn, 180.0, "SOL",
                                              paso_segundos=paso_segundos):
            eventos.append({
                "hora_local": jd_to_local(jd, utc_offset_salida),
                "grado_banco": round(item["grado"], 5),
                "variante_origen": item["variante"],
                "fecha_origen": item["fecha_origen"],
            })
    hl = "hora_local"
    eventos.sort(key=lambda e: (e[hl]["year"], e[hl]["month"], e[hl]["day"],
                                 e[hl]["hour"], e[hl]["minute"], e[hl]["second"]))
    return {
        "total_banco": len(banco), "total_eventos": len(eventos), "eventos": eventos,
        "nota": ("Técnica de Bonito: cada evento es una OPOSICIÓN EXACTA entre el Sol real y un "
                 "Sol de Fechas Gemelas de la carta de referencia — 'mancha solar' en su "
                 "lenguaje. En su ejemplo real la interpretó como el momento en que se produce "
                 "una actividad solar cuyo efecto (interferencia en comunicaciones) llega a la "
                 "Tierra 'en algunas horas' — sin una fórmula fija de cuántas horas, según lo que "
                 "dice en este tramo de clase."),
    }
