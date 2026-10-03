# -*- coding: utf-8 -*-
"""
Astrología Horaria de Hugo Bonito.

Reconstruida a partir de las transcripciones de sus clases sobre horaria
(9 preguntas de alumnos resueltas en vivo: Vero, Baby, Francisco, Adriana,
Nilda, Alfonso, Olga, y menciones parciales de Marisa y Lucy).

ES UN SISTEMA PROPIO DE BONITO, NO HORARIA CLÁSICA. No reparte casas
derivadas a la carta de la pregunta, no usa regentes de casa, ni recepción
mutua, ni prohibición, ni vía combusta, ni "vacío de curso" — ninguno de
esos términos aparece en el material revisado. En cambio, todo el sistema
pivota sobre los mismos 4-5 puntos angulares que Bonito usa en el resto de
su obra:

  - Medio Cielo (MC)     = la persona que consulta ("el autor del hecho",
    quien proyecta la acción).
  - Ascendente (ASC)     = el asunto/pregunta ("lo que está pensando" esa
    persona en el momento de preguntar).
  - Ecuador Celeste (EQ) = alterno del Ascendente, "mismo significado...
    un camino, hacia donde nos dirigimos"; se usa cuando el Ascendente no
    da elementos de análisis claros.
  - Vértex               = alterno de MC o de ASC/EQ, se prueba con el que
    "cierre" mejor el aspecto (sin regla fija declarada por Bonito).
  - Rueda de la Fortuna  = refuerzo específico para asuntos patrimoniales
    (compra/venta, dinero).

Cada uno de estos puntos se calcula en TRÓPICO y en SIDERAL (Fagan-Bradley,
igual que el resto del proyecto) y ambas variantes se prueban por igual —
Bonito revisa sistemáticamente las dos buscando la que dé un aspecto más
cerrado ("closest"), el mismo criterio que usa en Mellizos/Cartas Análogas.

CONVERSIÓN GRADO→TIEMPO — VALIDADO contra dos casos reales de clase (Vero
y Baby, clase del 18/9/2011 — fecha confirmada por capturas de pantalla
del software original de Bonito, Winstar; una fecha inferida antes por
cruce documental, 26/9/2011, resultó ser de otra clase distinta y quedó
descartada). Con la fecha correcta:
  - Vero ("¿cuándo se vende la casa de mamá?", 10:43hs): el motor
    encuentra el mismo vínculo que Bonito usó — Plutón trígono Vértex,
    armónico — y la fecha exacta de efeméride de ese trígono es el
    30/11/2011: coincide con su "fines de noviembre" casi al día.
  - Baby ("¿compro departamento?", 10:45hs): el Medio Cielo calculado
    para ese instante exacto (0°20.2' Sagitario) coincide con el valor
    que Bonito lee en pantalla (0°20' Sagitario) con un margen de 0.003°.
Con esto, la técnica de grado=tiempo quedó confirmada así: Bonito no
calculaba cuándo el planeta lento llega exacto por efeméride (esa
sustitución, probada antes contra la fecha equivocada, daba resultados
absurdos — un trígono ya cumplido 3 años antes); tomaba el valor numérico
del ORBE ACTUAL (el que hay en el momento de la pregunta) y lo releía
directamente como una cantidad de meses o de años ("cada grado de
distancia podemos tener un mes o un año el valor... nos acomodamos el
valor numérico a mes o año de acuerdo a las circunstancias" — sus propias
palabras). La elección entre "meses" o "años" no depende de qué tan rápido
se mueve el planeta sino de la naturaleza del asunto consultado (un cierre
de negocio se lee en meses; un tema de fondo, en años) — es un criterio
interpretativo del consultante, no una fórmula.

Esta versión implementa ESO: para cada vínculo/tránsito, se toma el orbe
en grados en el momento exacto de la pregunta y se lo devuelve tal cual,
listo para leerse como "N meses" o "N años" (ambas lecturas, para que el
intérprete elija según el asunto), junto con si el aspecto está aplicando
(orbe achicándose = viene, hacia el futuro) o separando (orbe agrandándose
= ya pasó, hacia el pasado) — este signo de aplicación/separación reemplaza
la búsqueda de fecha exacta como criterio de futuro/pasado. La búsqueda de
fecha exacta por efeméride (bisección) se conserva como dato adicional
"fecha_exacta_efemeride", claramente separado y con advertencia expresa de
que para planetas lentos puede diferir en años de la lectura de Bonito, en
vez de reemplazarla.

"ENROQUE" — NOTA HONESTA: en el material es un workaround del software de
Bonito (Winstar): su menú de tránsito a ÁNGULOS solo permitía tránsito
geocéntrico simple, mientras que el menú pensado para PLANETAS sí permitía
combinar geocéntrico + ascensión recta + sideral en una sola búsqueda
("merge"). Para aprovechar esa búsqueda combinada sobre un ángulo, Bonito
copiaba el valor numérico del ángulo dentro del casillero de la Luna de
una carta auxiliar y buscaba tránsitos "a la Luna" (que en realidad
apuntaban al ángulo). Acá no hace falta ese rodeo: se puede buscar
tránsitos a cualquier punto directamente con Swiss Ephemeris.

NO IMPLEMENTADO (fuera de alcance de esta primera versión): la técnica de
detección de infidelidad con la Luna de revolución solar a 30° del Sol de
la pareja ("30° = el enemigo", mencionada de paso en el material) — es una
técnica distinta, no parte del motor central de horaria; se puede agregar
más adelante si Celina lo pide.

VALIDACIÓN — ACTUALIZADA: la clase es del 18/9/2011 (confirmado por
capturas de pantalla del software original de Bonito — Winstar — que
Celina fue transcribiendo). Con esa fecha, DOS de los 9 casos (Vero y
Baby) ya se validaron numéricamente contra la reconstrucción histórica
real, con resultados que coinciden (ver nota de grado=tiempo más arriba).
Los 7 casos restantes (Francisco, Adriana, Nilda, Alfonso, Olga, y las
menciones parciales de Marisa y Lucy) quedan sin validar numéricamente
todavía — se puede retomar si Celina sigue transcribiendo esa clase o
pide seguir revisando esos casos puntuales.
"""
import swisseph as swe

from astro import (
    jd_from_local, jd_to_local, norm360, _diff_angular, sign_of,
    sol_luna_geo_tropical, cuerpo_base_lon,
)
from puntos import puntos_angulares, puntos_angulares_sideral, rueda_de_la_fortuna, es_diurna

# Familias de aspecto usadas por Bonito en horaria (más finas que las de
# Fechas Gemelas: incluye semicuadratura/sesquicuadratura/semisextil/
# quincuncio, que en horaria sí tienen lectura propia).
ASPECTOS_HORARIA = {
    "Conjunción": 0, "Semisextil": 30, "Semicuadratura": 45, "Sextil": 60,
    "Cuadratura": 90, "Trígono": 120, "Sesquicuadratura": 135,
    "Quincuncio": 150, "Oposición": 180,
}
FAMILIA_ASPECTO = {
    "Conjunción": "neutro",
    "Trígono": "armónico", "Sextil": "armónico",
    "Cuadratura": "tenso", "Oposición": "tenso",
    "Semicuadratura": "tenso", "Sesquicuadratura": "tenso",
    "Semisextil": "sacrificio", "Quincuncio": "sacrificio",
}
# Lectura corta de cada familia, tal como la describe Bonito en el material
LECTURA_FAMILIA = {
    "armónico": "camino favorecido / respuesta orientada al sí",
    "tenso": "freno, obstáculo o tensión / respuesta orientada al no",
    "sacrificio": "logro o beneficio a medias — algo se gana y algo se pierde a la vez",
    "neutro": "intensifica el tema, para bien o para mal según el resto de la carta",
}

ORBE_PARTIL_HORARIA = 0.1  # grados

PLANETAS_LENTOS_HORARIA = ["JUPITER", "SATURNO", "URANO", "NEPTUNO", "PLUTON"]

# Agregado tras validar con el caso real de Baby (compra de departamento,
# 26/9/2011): Bonito no se limita a los planetas lentos para leer el
# "cómo viene la persona hoy" — usa también el tránsito del SOL sobre el
# Medio Cielo, con un orbe MUY chico medido en minutos de arco ("cuadratura
# partil, 4 minutos de arco... esto es de ayer o de hoy"; "40 minutos de
# arco pueden ser 20 días"). Es la misma técnica de grado=tiempo, pero para
# un cuerpo rápido el "grado" natural pasa a ser el MINUTO de arco y la
# unidad de tiempo pasa a ser el DÍA (no el mes/año) — inferido de ese
# único caso, no declarado por Bonito como regla general, así que se marca
# aparte con su propia nota.
CUERPOS_RAPIDOS_HORARIA = ["SOL"]

PUNTOS_HORARIA = ("mc", "ascendente", "ecuador_celeste", "vertex", "rueda_de_la_fortuna")
NOMBRES_PUNTOS = {
    "mc": "Medio Cielo (persona)", "ascendente": "Ascendente (pregunta)",
    "ecuador_celeste": "Ecuador Celeste (pregunta, alterno)",
    "vertex": "Vértex (persona o pregunta, alterno)",
    "rueda_de_la_fortuna": "Rueda de la Fortuna (asuntos patrimoniales)",
}


def _aspecto_horaria(lon1, lon2, orbe_max):
    d = abs(_diff_angular(lon1, lon2))
    mejor = None
    for nombre, angulo in ASPECTOS_HORARIA.items():
        diff = abs(d - angulo)
        if diff <= orbe_max and (mejor is None or diff < mejor["orbe"]):
            mejor = {"aspecto": nombre, "familia": FAMILIA_ASPECTO[nombre],
                     "orbe": round(diff, 4), "partil": diff <= ORBE_PARTIL_HORARIA}
    return mejor


def _puntos_sistema(jd, lat, lon, sideral):
    """Los 5 puntos horaria (MC/ASC/EQ/Vértex/Rueda de Fortuna) en el
    sistema pedido (trópico o sideral)."""
    if sideral:
        angulos = puntos_angulares_sideral(jd, lat, lon)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        sol_lon = swe.calc_ut(jd, swe.SUN, flag)[0][0]
        luna_lon = swe.calc_ut(jd, swe.MOON, flag)[0][0]
    else:
        angulos = puntos_angulares(jd, lat, lon)
        sol_lon, luna_lon = sol_luna_geo_tropical(jd)
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)
    return {
        "mc": angulos["mc"], "ascendente": angulos["ascendente"],
        "ecuador_celeste": angulos["ecuador_celeste"], "vertex": angulos["vertex"],
        "rueda_de_la_fortuna": fortuna,
    }


def _aplicando(jd, lon_punto, angulo, cuerpo, helio, sideral):
    """True si el orbe entre 'cuerpo' y 'lon_punto' se está achicando (el
    aspecto está aplicando, viene "hacia adelante"); False si se está
    agrandando (separando, ya "quedó atrás"). Es el criterio tradicional de
    aplicación/separación, y reemplaza la fecha exacta de efeméride como
    forma de decidir futuro/pasado para la técnica de grado=tiempo."""
    def orbe_en(jd_):
        lon_pl, _ = cuerpo_base_lon(jd_, cuerpo, helio, sideral)
        d = abs(_diff_angular(lon_pl, lon_punto))
        return abs(d - angulo)
    return orbe_en(jd + 1.0) < orbe_en(jd)


def _resolver_fecha_aspecto(jd_desde, lon_punto, angulo, cuerpo, helio, sideral,
                             ventana_dias=1200, paso_dias=3):
    """Busca, adelante y atrás de 'jd_desde', la fecha más cercana en que
    'cuerpo' completa el aspecto 'angulo' (por cualquiera de sus dos lados)
    con 'lon_punto'. Usa el mismo patrón de bisección + verificación de
    raíz (EPS) que el resto del motor, para no confundir un cruce genuino
    con el falso cruce en el antípoda (ver astro.buscar_retornos) — acá
    además es imprescindible porque los planetas lentos retrogradan."""
    EPS = 1e-4

    def lon_en(jd):
        return cuerpo_base_lon(jd, cuerpo, helio, sideral)[0]

    candidatos = []
    for lado in (1, -1):
        objetivo = norm360(lon_punto + lado * angulo)
        for direccion in (1, -1):
            paso = paso_dias * direccion
            jd = jd_desde
            prev = _diff_angular(lon_en(jd), objetivo)
            pasos_max = int(ventana_dias / paso_dias) + 2
            for _ in range(pasos_max):
                jd_next = jd + paso
                curr = _diff_angular(lon_en(jd_next), objetivo)
                if (prev > 0) != (curr > 0):
                    lo, hi = (jd, jd_next) if paso > 0 else (jd_next, jd)
                    dlo = _diff_angular(lon_en(lo), objetivo)
                    for _ in range(60):
                        mid = (lo + hi) / 2
                        dmid = _diff_angular(lon_en(mid), objetivo)
                        if (dmid > 0) == (dlo > 0):
                            lo, dlo = mid, dmid
                        else:
                            hi = mid
                    raiz = (lo + hi) / 2
                    if abs(_diff_angular(lon_en(raiz), objetivo)) < EPS:
                        candidatos.append(raiz)
                    break  # alcanza el primer cruce de este lado/dirección
                prev, jd = curr, jd_next
    if not candidatos:
        return None
    return min(candidatos, key=lambda c: abs(c - jd_desde))


def carta_horaria(consulta, orbe_vinculo=3.0, orbe_transito=3.0, anios_busqueda=3):
    """Carta horaria de Bonito para el momento y lugar de una pregunta.

    consulta: dict con year/month/day/hour/minute/utc_offset/lat/lon (y,
    opcionalmente, 'pregunta' de texto libre, solo para referencia).

    Devuelve los puntos MC/ASC/EQ/Vértex/Rueda de Fortuna en trópico y
    sideral, el 'vínculo directo' persona↔pregunta (aspecto entre MC/Vértex
    y ASC/EQ/Vértex), y los tránsitos actuales de los planetas lentos
    (Júpiter/Saturno/Urano/Neptuno/Plutón, geo y helio) sobre cada punto,
    con la fecha real más cercana (pasada o futura) en que cada aspecto se
    vuelve exacto."""
    jd = jd_from_local(consulta["year"], consulta["month"], consulta["day"],
                        consulta["hour"], consulta["minute"], consulta["utc_offset"])
    lat, lon = consulta["lat"], consulta["lon"]

    sistemas = {
        "trópico": _puntos_sistema(jd, lat, lon, sideral=False),
        "sideral": _puntos_sistema(jd, lat, lon, sideral=True),
    }

    # 1) Vínculo directo: MC/Vértex (persona) vs. Ascendente/Ecuador Celeste/
    # Vértex (pregunta), en ambos sistemas.
    PERSONA = ("mc", "vertex")
    PREGUNTA = ("ascendente", "ecuador_celeste", "vertex")
    vinculos = []
    for nombre_sis, puntos in sistemas.items():
        for p_persona in PERSONA:
            for p_pregunta in PREGUNTA:
                if p_persona == p_pregunta:
                    continue
                asp = _aspecto_horaria(puntos[p_persona]["lon"], puntos[p_pregunta]["lon"], orbe_vinculo)
                if asp:
                    vinculos.append({
                        "sistema": nombre_sis,
                        "persona": NOMBRES_PUNTOS[p_persona], "pregunta": NOMBRES_PUNTOS[p_pregunta],
                        **asp,
                    })
    vinculos.sort(key=lambda v: v["orbe"])

    # 2) Tránsitos actuales sobre cada punto horaria: planetas lentos (en
    # sus 4 variantes geo/helio × trópico/sideral) y, además, el Sol como
    # cuerpo rápido (solo geocéntrico — helio no tiene sentido para el Sol),
    # con su propia escala de grado=tiempo (ver nota en CUERPOS_RAPIDOS_HORARIA).
    def _item_transito(nombre_sis, nombre_punto, lon_punto, nombre_cuerpo, helio, sideral_flag, rapido):
        lon_cuerpo, _spd = cuerpo_base_lon(jd, nombre_cuerpo, helio, sideral_flag)
        asp = _aspecto_horaria(lon_cuerpo, lon_punto, orbe_transito)
        if not asp:
            return None
        angulo_asp = ASPECTOS_HORARIA[asp["aspecto"]]
        aplicando = _aplicando(jd, lon_punto, angulo_asp, nombre_cuerpo, helio, sideral_flag)
        if rapido:
            orbe_min = asp["orbe"] * 60
            grado_tiempo = {
                "orbe_grados": asp["orbe"], "orbe_minutos_arco": round(orbe_min, 2),
                "dias": round(orbe_min, 1), "semanas": round(orbe_min / 7, 1),
                "sentido": "aplicando (viene hacia adelante)" if aplicando else "separando (ya quedó atrás)",
                "nota": ("Cuerpo rápido (Sol): inferido del caso real de Baby, no una regla "
                         "que Bonito haya declarado en general. Ahí usó el orbe en MINUTOS de "
                         "arco leído directamente como DÍAS ('4 minutos de arco... de ayer o "
                         "de hoy'; '40 minutos de arco pueden ser 20 días') — misma lógica de "
                         "grado=tiempo que con los planetas lentos, pero con el Sol la unidad "
                         "natural es el minuto de arco y el día, no el grado y el mes/año."),
            }
        else:
            grado_tiempo = {
                "orbe_grados": asp["orbe"], "meses": asp["orbe"], "anios": asp["orbe"],
                "sentido": "aplicando (viene hacia adelante)" if aplicando else "separando (ya quedó atrás)",
                "nota": ("Técnica de Bonito: el valor numérico del orbe se lee "
                         "directamente como esa cantidad de meses O de años — la "
                         "elección de unidad depende de la naturaleza del asunto "
                         "consultado (un cierre a corto plazo se lee en meses; un "
                         "tema de fondo, en años), no de qué tan rápido se mueve el "
                         "planeta. No es un cálculo de efeméride."),
            }
        item = {
            "sistema": nombre_sis, "punto": NOMBRES_PUNTOS[nombre_punto],
            "planeta": nombre_cuerpo.capitalize(), "modo": "Heliocéntrico" if helio else "Geocéntrico",
            "lectura": LECTURA_FAMILIA[asp["familia"]],
            **asp,
            "aplicando": aplicando,
            "cuando": "futuro" if aplicando else "pasado",
            "grado_tiempo": grado_tiempo,
        }
        jd_exacto = _resolver_fecha_aspecto(
            jd, lon_punto, angulo_asp, nombre_cuerpo, helio, sideral_flag,
            ventana_dias=(60 if rapido else anios_busqueda * 365.2425))
        if jd_exacto is not None:
            item["fecha_exacta_efemeride"] = jd_to_local(jd_exacto, consulta["utc_offset"])
            item["fecha_exacta_efemeride_nota"] = (
                "Fecha real (por efeméride) en que el aspecto se completa exacto — "
                "dato de referencia, NO la lectura de Bonito. Para planetas lentos "
                "puede caer años antes o después de lo que da la técnica de "
                "grado=tiempo (ver 'grado_tiempo'); validado así contra un caso real."
            )
        return item

    transitos = []
    for nombre_sis, puntos in sistemas.items():
        sideral_flag = nombre_sis == "sideral"
        for nombre_punto in PUNTOS_HORARIA:
            lon_punto = puntos[nombre_punto]["lon"]
            for nombre_pl in PLANETAS_LENTOS_HORARIA:
                for helio in (False, True):
                    item = _item_transito(nombre_sis, nombre_punto, lon_punto, nombre_pl, helio, sideral_flag, rapido=False)
                    if item:
                        transitos.append(item)
            for nombre_cuerpo in CUERPOS_RAPIDOS_HORARIA:
                item = _item_transito(nombre_sis, nombre_punto, lon_punto, nombre_cuerpo, False, sideral_flag, rapido=True)
                if item:
                    transitos.append(item)
    transitos.sort(key=lambda t: t["orbe"])

    return {
        "fecha_pregunta": jd_to_local(jd, consulta["utc_offset"]),
        "pregunta": consulta.get("pregunta", ""),
        "puntos": {
            "trópico": {k: sistemas["trópico"][k] for k in PUNTOS_HORARIA},
            "sideral": {k: sistemas["sideral"][k] for k in PUNTOS_HORARIA},
        },
        "vinculos_directos": vinculos,
        "transitos": transitos,
        "total_transitos": len(transitos),
    }
