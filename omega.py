# -*- coding: utf-8 -*-
"""
Programa Omega de Hugo Bonito.

Reconstruido a partir de "OmegaCargolunes.doc" (manual paso a paso, escrito
para operar a mano con Winstar + Excel + un ejecutable auxiliar llamado
"Omega") y de casos reales de aplicación: Mundial 2010 (Argentina/Nigeria,
Alemania, la final), "personajes imantados" (Maradona), la carta natal de
Argentina, y "Goles_Boca.doc" (Boca vs. Banfield, 04/12/2011).

TÉCNICA (tal como la describe el manual): se arma un "banco de grados" —
las posiciones de Sol y Luna en cada una de las Fechas Gemelas de los
Retornos de Plutón (Geocéntrico/Heliocéntrico x Trópico/Sideral) de la
persona, equipo o evento de referencia (el "debut", el nacimiento, etc.).
Después se toma una ventana horaria CORTA y REAL — la duración de un
partido de fútbol, una sesión bursátil — y se escanea la posición real en
tránsito de la Luna (el cuerpo que Bonito usa: "SOL conjunción LUNA es el
GANADOR" — es la Luna en tránsito la que se compara contra el banco de
Soles y Lunas) buscando los instantes EXACTOS de conjunción partil con
cada grado guardado. Esos instantes son los "horarios imantados": para
Bonito, ahí es donde caen los goles, los golpes de mercado, o el resultado
favorable a uno u otro lado. Comparando el banco de dos equipos sobre la
misma ventana, "gana" el que acumula más conjunciones (o una conjunción
más exacta/partil).

RECONSTRUCCIÓN HONESTA — lo que se simplifica: el manual original arma el
banco a mano en Excel, copiando y pegando 4 columnas (Luna1/Luna2/Sol1/
Sol2) que salen de calcular los Retornos de Plutón DOS VECES (una para el
inicio del evento, otra para el inicio + 2 horas) y de un truco de Excel
para "clonar" una columna con un incremento de 0,000001 cuando hace falta
alinear filas. Ese rodeo es limitación de la herramienta de 2010, no parte
de la técnica astrológica — acá se arma el banco directamente con
calcular_fechas_gemelas (ya implementado y validado en este proyecto) y se
escanea el tránsito real por bisección exacta (mismo patrón que el resto
del proyecto), en lugar de foto a mano cada minuto en Winstar.

NO IMPLEMENTADO todavía: el detalle de "Cotidian Cardinal"/direcciones
secundarias que aparece en Goles_Boca.doc como paso previo (buscar el
Vértex/MC del día por direcciones diarias) — es una técnica aparte, ya
reconstruida en astro.py para otro uso; se puede combinar con Omega más
adelante si Celina lo pide. Tampoco se implementó el companion Sol-en-
tránsito (más lento, útil para ventanas de varios días, no para un
partido de 90 minutos) — se deja como opción (cuerpo_transito="SOL").
"""
import swisseph as swe

from astro import jd_from_local, jd_to_local, norm360, _diff_angular, calcular_fechas_gemelas

ORBE_PARTIL_OMEGA = 0.05  # grados (~3 minutos de arco) — "conjunción" para
                           # Bonito es un cruce casi exacto, no un orbe amplio


def _banco_de_grados(fechas_gemelas):
    """A partir de calcular_fechas_gemelas, arma la lista plana de grados
    de referencia (Sol y Luna de cada Fecha Gemela, en las 4 variantes:
    geo/helio x trópico/sideral), cada uno con su origen para poder
    explicar de dónde salió cada coincidencia."""
    banco = []
    for variante, lista in fechas_gemelas.items():
        for entrada in lista:
            banco.append({"grado": entrada["sol"]["lon"], "cuerpo_origen": "Sol",
                           "variante": variante, "fecha_origen": entrada["fecha_local"]})
            banco.append({"grado": entrada["luna"]["lon"], "cuerpo_origen": "Luna",
                           "variante": variante, "fecha_origen": entrada["fecha_local"]})
    return banco


def _lon_en(jd, cuerpo):
    flag = swe.FLG_SWIEPH | swe.FLG_SPEED
    swe_id = swe.MOON if cuerpo == "LUNA" else swe.SUN
    pos, _ = swe.calc_ut(jd, swe_id, flag)
    return pos[0]


def _buscar_conjuncion_en_ventana(jd_ini, jd_fin, objetivo, cuerpo, paso_segundos=20):
    """Busca TODOS los cruces exactos donde 'cuerpo' (Luna o Sol) en
    tránsito real pasa por 'objetivo' dentro de [jd_ini, jd_fin] — mismo
    patrón de bisección + verificación EPS que el resto del proyecto."""
    EPS = 1e-4
    paso = paso_segundos / 86400.0
    resultados = []
    jd = jd_ini
    prev = _diff_angular(_lon_en(jd, cuerpo), objetivo)
    while jd < jd_fin:
        jd_next = min(jd + paso, jd_fin)
        curr = _diff_angular(_lon_en(jd_next, cuerpo), objetivo)
        if (prev > 0) != (curr > 0):
            lo, hi = jd, jd_next
            dlo = prev
            for _ in range(40):
                mid = (lo + hi) / 2
                dmid = _diff_angular(_lon_en(mid, cuerpo), objetivo)
                if (dmid > 0) == (dlo > 0):
                    lo, dlo = mid, dmid
                else:
                    hi = mid
            raiz = (lo + hi) / 2
            if abs(_diff_angular(_lon_en(raiz, cuerpo), objetivo)) < EPS:
                resultados.append(raiz)
        prev, jd = curr, jd_next
        if jd >= jd_fin:
            break
    return resultados


def escanear_omega(persona, jd_ventana_ini, jd_ventana_fin, utc_offset_salida,
                    anios_atras=80, anios_adelante=80, cuerpo_transito="LUNA"):
    """Corre el Programa Omega para una entidad (persona, equipo, evento):
    arma su banco de grados (Sol/Luna de sus Fechas Gemelas de Retornos de
    Plutón) y escanea la ventana horaria real [jd_ventana_ini,
    jd_ventana_fin] buscando conjunciones partiles del cuerpo en tránsito
    (Luna por default, criterio de Bonito) contra cada grado del banco."""
    fechas_gemelas = calcular_fechas_gemelas(
        persona["year"], persona["month"], persona["day"],
        persona["hour"], persona["minute"], persona["utc_offset"],
        anios_atras=anios_atras, anios_adelante=anios_adelante)
    banco = _banco_de_grados(fechas_gemelas)

    eventos = []
    for item in banco:
        for jd in _buscar_conjuncion_en_ventana(jd_ventana_ini, jd_ventana_fin, item["grado"], cuerpo_transito):
            eventos.append({
                "hora_local": jd_to_local(jd, utc_offset_salida),
                "cuerpo_en_transito": cuerpo_transito.capitalize(),
                "grado_banco": round(item["grado"], 5),
                "origen_banco": item["cuerpo_origen"],
                "variante_origen": item["variante"],
                "fecha_origen": item["fecha_origen"],
            })
    eventos.sort(key=lambda e: (e["hora_local"]["hour"], e["hora_local"]["minute"], e["hora_local"]["second"]))
    return {"total_banco": len(banco), "total_eventos": len(eventos), "eventos": eventos}


def comparar_omega(persona_a, nombre_a, persona_b, nombre_b, jd_ventana_ini, jd_ventana_fin,
                    utc_offset_salida, anios_atras=80, anios_adelante=80, cuerpo_transito="LUNA"):
    """Corre escanear_omega para dos entidades (por ejemplo, dos equipos)
    sobre la misma ventana horaria y compara: 'gana' quien acumula más
    conjunciones en la ventana — el criterio explícito de Bonito ("Sol
    conjunción Luna es el ganador")."""
    res_a = escanear_omega(persona_a, jd_ventana_ini, jd_ventana_fin, utc_offset_salida,
                            anios_atras, anios_adelante, cuerpo_transito)
    res_b = escanear_omega(persona_b, jd_ventana_ini, jd_ventana_fin, utc_offset_salida,
                            anios_atras, anios_adelante, cuerpo_transito)
    if res_a["total_eventos"] > res_b["total_eventos"]:
        ganador = nombre_a
    elif res_b["total_eventos"] > res_a["total_eventos"]:
        ganador = nombre_b
    else:
        ganador = "empate"
    return {
        nombre_a: res_a, nombre_b: res_b,
        "ganador_por_cantidad": ganador,
        "nota": ("Criterio de Bonito: más conjunciones partiles del cuerpo en tránsito "
                 "contra el banco de grados de cada lado, dentro de la ventana horaria, "
                 "indica el lado 'ganador'. Es un criterio de cantidad, no de certeza — "
                 "Bonito lo usaba como indicio a favor, no como pronóstico cerrado."),
    }
