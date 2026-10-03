# -*- coding: utf-8 -*-
"""
Proluna (PLN) — Progresión Lunar Natural, técnica de Boris Cristoff
("La Proluna", Ed. Kier, 1993), tal como la recibió y aplicó Hugo Bonito.

NO es un punto que se mueve por el cielo (no usa efemérides salvo para
calcular las 12 casas natales una sola vez). Es una progresión SIMBÓLICA:
las 12 casas de la carta natal se convierten en una regla de tiempo. Cada
casa representa una porción fija de tiempo (7 años en la escala de vida
completa), arrancando en el Ascendente = momento de nacimiento. Para saber
"dónde cae" un momento dado, se ve en qué casa entra la edad/tiempo
transcurrido y se interpola linealmente el grado dentro de esa casa.

Escalas documentadas por Cristoff (todas con la misma mecánica, la única
diferencia es cuánto tiempo representa cada casa):

    escala   años/casa-equivalente   ciclo total (12 casas)
    PLN      7 años                  84 años   (hitos biográficos)
    RSN      1 mes                   1 año     (destino anual)
    RLN      ~2.4635 días            1 mes lunar (~29.53 días) (destino mensual)
    R7N      14 horas                1 semana  (destino semanal)
    RDN      2 horas                 1 día     (destino diario)
    RHN      5 minutos               1 hora    (sucesos horarios)
    RMN      5 segundos              1 minuto  (sucesos instantáneos)

RSN y RLN (25/9/2026): Cristoff aclara en su libro que la carta anual por
RSN se traza "basada en la revolución solar" del año correspondiente — es
decir, la base NO son las cúspides natales sino las cúspides de la carta
de Revolución Solar de ese año puntual, progresadas 1 mes por casa. Por
la misma lógica de afinación sucesiva (PLN -> RSN -> RLN) la RLN usa como
base la Revolución Lunar del mes correspondiente. En vez de asumir una
duración fija de "1 año" o "1 mes lunar" por ciclo, se usa la duración
REAL entre esa Revolución y la siguiente (RS-a-RS o RL-a-RL), que es más
preciso y evita asumir un promedio.

R7N, RDN, RHN, RMN (semanal, diaria, horaria, por minuto) siguen sin
implementarse: ni el libro de Cristoff ni el material de Bonito revisado
documentan su punto de reinicio de forma utilizable — el propio Cristoff
escribe que nunca llegó a aplicarlas en la práctica ("sólo mi destino dirá
si algún día soy capaz de interpretar prácticamente con los restantes
cuatro"). Implementarlas sería inventar una convención que ni el creador
de la técnica resolvió.
"""
import datetime as dt
import swisseph as swe
from astro import norm360, jd_from_local, jd_to_local, sign_of, _diff_angular
from puntos import casas, puntos_angulares, HSYS_DEFAULT
from revolucion import _sol_luna, _buscar_retorno

ANIOS_POR_CASA_PLN = 7.0
CICLO_PLN_ANIOS = 12 * ANIOS_POR_CASA_PLN  # 84

# Multiplos de 15 grados (0..180) usados por Bonito para validar aspectos
# entre Proluna directa y conversa (semisextil=30, sextil=60, cuadratura=90,
# trigono=120, quincuncio=150, oposicion=180, mas los intermedios de 15/45/
# 75/105/135/165 que el tambien usa "a ojo" en el metodo numerico).
ASPECTOS_15 = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]


def casas_natales(year, month, day, hour, minute, utc_offset, lat, lon, hsys=HSYS_DEFAULT):
    """Calcula (una sola vez) las 12 cúspides de casa natales, base de toda
    progresión Proluna de esta persona."""
    jd = jd_from_local(year, month, day, hour, minute, utc_offset)
    cusps, ascmc = casas(jd, lat, lon, hsys)
    return list(cusps)  # cusps[0]=casa I (=Ascendente) ... cusps[11]=casa XII


def _edad_en_anios(fecha_nacimiento, fecha_objetivo):
    """Años transcurridos (con fracción) entre dos datetimes 'naive' (UTC),
    con precisión de días — suficiente para la escala de 7 años/casa."""
    delta = fecha_objetivo - fecha_nacimiento
    return delta.total_seconds() / (365.2425 * 86400.0)


def proluna(cusps, year, month, day, hour, minute, utc_offset,
            nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset,
            conversa=False):
    """Posición de la Proluna (PLN) para una fecha/hora objetivo, dada la
    carta natal (cusps) y los datos de nacimiento.

    'conversa=True' calcula la Proluna CONVERSA: Bonito describe la
    dirección "directa" como la progresión normal ("en contra de las
    agujas del reloj") y la "conversa" como la misma progresión pero
    retrocediendo desde la fecha de nacimiento ("a favor de las agujas
    del reloj") — en la práctica, la misma mecánica de interpolación mas
    la edad transcurrida en NEGATIVO (mismo patrón "directa/conversa" que
    usa el resto del proyecto para progresiones de planetas, ver
    pronostico_natal.progresion_extendida).

    Devuelve la posición interpolada, la casa natal en la que "cae" ese
    momento, y la edad exacta usada para el cálculo.
    """
    nac_local = dt.datetime(nac_year, nac_month, nac_day, nac_hour, nac_minute)
    nac_ut = nac_local - dt.timedelta(hours=nac_utc_offset)

    obj_local = dt.datetime(year, month, day, hour, minute)
    obj_ut = obj_local - dt.timedelta(hours=utc_offset)

    edad = _edad_en_anios(nac_ut, obj_ut)
    if conversa:
        edad = -edad
    edad_en_ciclo = edad % CICLO_PLN_ANIOS  # el ciclo se repite cada 84 años

    casa_idx = int(edad_en_ciclo // ANIOS_POR_CASA_PLN)  # 0..11
    frac = (edad_en_ciclo % ANIOS_POR_CASA_PLN) / ANIOS_POR_CASA_PLN  # 0..1 dentro de la casa

    cusp_ini = cusps[casa_idx]
    cusp_fin = cusps[(casa_idx + 1) % 12]
    ancho = norm360(cusp_fin - cusp_ini)  # ancho de la casa en grados (0-360, en sentido directo)

    lon = norm360(cusp_ini + ancho * frac)
    signo, grado = sign_of(lon)

    return {
        "lon": lon,
        "signo": signo,
        "grado": round(grado, 4),
        "casa_natal": casa_idx + 1,  # 1-12, en numeración humana
        "edad_anios": round(edad, 4),
        "conversa": conversa,
        "escala": "PLN (7 años/casa, ciclo de 84 años)",
    }


def _progresion_simbolica(cusps, jd_ini, jd_fin, jd_objetivo):
    """Mecánica común a PLN/RSN/RLN: dadas las 12 cúspides de una carta base
    y el intervalo [jd_ini, jd_fin) que representa un ciclo completo (12
    casas), interpola la posición correspondiente a jd_objetivo dentro de
    ese intervalo."""
    ciclo = jd_fin - jd_ini
    transcurrido = (jd_objetivo - jd_ini) % ciclo
    casa_dur = ciclo / 12.0

    casa_idx = int(transcurrido // casa_dur) % 12
    frac = (transcurrido % casa_dur) / casa_dur

    cusp_ini = cusps[casa_idx]
    cusp_fin = cusps[(casa_idx + 1) % 12]
    ancho = norm360(cusp_fin - cusp_ini)

    lon = norm360(cusp_ini + ancho * frac)
    signo, grado = sign_of(lon)
    return lon, signo, grado, casa_idx + 1, ciclo


def resona(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset,
           year, month, day, hour, minute, utc_offset, lat, lon):
    """RSN (Resona) — refinamiento anual de la Proluna. Base: las 12 casas
    de la Revolución Solar del año vigente en la fecha objetivo (no las
    cúspides natales), progresadas a lo largo de ese año solar real (de
    un retorno solar al siguiente)."""
    jd_natal = jd_from_local(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset)
    sol_natal_lon, _ = _sol_luna(jd_natal)

    jd_objetivo = jd_from_local(year, month, day, hour, minute, utc_offset)

    # aproximación al retorno solar vigente: el cumpleaños del año de la
    # fecha objetivo, o el del año anterior si ese cumpleaños todavía no
    # ocurrió respecto de la fecha objetivo
    jd_aprox = jd_from_local(year, nac_month, nac_day, nac_hour, nac_minute, utc_offset)
    if jd_aprox > jd_objetivo:
        jd_aprox = jd_from_local(year - 1, nac_month, nac_day, nac_hour, nac_minute, utc_offset)

    jd_ini = _buscar_retorno(sol_natal_lon, jd_aprox, swe.SUN, ventana_dias=4)
    if jd_ini is None or jd_ini > jd_objetivo:
        # margen de seguridad: retroceder un año más si cayó del lado equivocado
        jd_aprox -= 365.2425
        jd_ini = _buscar_retorno(sol_natal_lon, jd_aprox, swe.SUN, ventana_dias=4)
    if jd_ini is None:
        raise ValueError("No se pudo ubicar la Revolución Solar vigente para esta fecha.")

    jd_fin = _buscar_retorno(sol_natal_lon, jd_ini + 365.2425, swe.SUN, ventana_dias=5)
    if jd_fin is None:
        raise ValueError("No se pudo ubicar la siguiente Revolución Solar.")

    cusps_rs = puntos_angulares(jd_ini, lat, lon)["cusps"]

    lon_rsn, signo, grado, casa_idx, ciclo_dias = _progresion_simbolica(cusps_rs, jd_ini, jd_fin, jd_objetivo)

    return {
        "lon": lon_rsn,
        "signo": signo,
        "grado": round(grado, 4),
        "casa_rsn": casa_idx,
        "escala": "RSN (1 mes/casa, ciclo de 1 revolución solar a la siguiente)",
        "revolucion_solar_base": jd_to_local(jd_ini, utc_offset),
        "revolucion_solar_siguiente": jd_to_local(jd_fin, utc_offset),
        "duracion_ciclo_dias": round(ciclo_dias, 4),
    }


def reluna(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset,
           year, month, day, hour, minute, utc_offset, lat, lon):
    """RLN (Reluna) — refinamiento mensual de la Proluna. Base: las 12
    casas de la Revolución Lunar (retorno de la Luna a su longitud natal)
    vigente en la fecha objetivo, progresadas a lo largo de ese mes lunar
    real (de un retorno lunar al siguiente)."""
    jd_natal = jd_from_local(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset)
    _, luna_natal_lon = _sol_luna(jd_natal)

    jd_objetivo = jd_from_local(year, month, day, hour, minute, utc_offset)

    # se busca el retorno lunar más cercano a "objetivo menos medio mes
    # lunar", para sesgar la búsqueda hacia el retorno ANTERIOR al objetivo
    jd_centro = jd_objetivo - 13.5
    jd_ini = _buscar_retorno(luna_natal_lon, jd_centro, swe.MOON, ventana_dias=16)
    if jd_ini is None or jd_ini > jd_objetivo:
        jd_centro -= 27.32
        jd_ini = _buscar_retorno(luna_natal_lon, jd_centro, swe.MOON, ventana_dias=16)
    if jd_ini is None:
        raise ValueError("No se pudo ubicar la Revolución Lunar vigente para esta fecha.")

    jd_fin = _buscar_retorno(luna_natal_lon, jd_ini + 27.32, swe.MOON, ventana_dias=4)
    if jd_fin is None:
        raise ValueError("No se pudo ubicar la siguiente Revolución Lunar.")

    cusps_rl = puntos_angulares(jd_ini, lat, lon)["cusps"]

    lon_rln, signo, grado, casa_idx, ciclo_dias = _progresion_simbolica(cusps_rl, jd_ini, jd_fin, jd_objetivo)

    return {
        "lon": lon_rln,
        "signo": signo,
        "grado": round(grado, 4),
        "casa_rln": casa_idx,
        "escala": "RLN (~2.3 días/casa, ciclo de 1 revolución lunar a la siguiente)",
        "revolucion_lunar_base": jd_to_local(jd_ini, utc_offset),
        "revolucion_lunar_siguiente": jd_to_local(jd_fin, utc_offset),
        "duracion_ciclo_dias": round(ciclo_dias, 4),
    }


def _orbe_a_multiplo_15(diferencia):
    """Dada una separación angular (0-180), devuelve el múltiplo de 15°
    más cercano y el orbe (distancia) a ese múltiplo."""
    mejor_mult, mejor_orbe = None, 999.0
    for m in ASPECTOS_15:
        orbe = abs(diferencia - m)
        if orbe < mejor_orbe:
            mejor_mult, mejor_orbe = m, orbe
    return mejor_mult, mejor_orbe


def rectificar_hora_proluna(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset, lat, lon,
                             evento_year, evento_month, evento_day, evento_hour, evento_minute, evento_utc_offset,
                             rango_minutos=90, paso_minutos=1):
    """Técnica de rectificación de hora natal con la Proluna (Bonito, fuente
    86874430-attachment.txt, caso 'Verazategui'): dado un evento puntual
    conocido (fallecimiento, mudanza, compra/venta de inmueble...), se
    prueba la hora de nacimiento minuto a minuto alrededor de la hora
    aproximada dada, y para cada candidata se calculan la Proluna DIRECTA
    y la Proluna CONVERSA en el momento del evento. La hora correcta es
    aquella en que ambas quedan en aspecto EXACTO (múltiplo de 15°,
    idealmente 0° o el aspecto de 105° que Bonito llama "de ausencia") —
    cuanto menor el orbe, más precisa la hora. Se listan los candidatos
    ordenados por orbe (menor primero) para que Celina identifique el
    minuto ganador, tal como hacía Bonito probando minuto por minuto en el
    Kepler ("un minuto de arco ~ una semana de precisión").

    RECONSTRUCCIÓN HONESTA: se recalculan las 12 cúspides natales para
    cada minuto candidato (en vez del ajuste manual minuto a minuto de
    Bonito en el Kepler) — misma técnica, ejecutada de forma exhaustiva
    en vez de a prueba y error.
    """
    EPS_MIN = 1e-9
    nac_base = dt.datetime(nac_year, nac_month, nac_day, nac_hour, nac_minute)
    candidatos = []

    delta = -rango_minutos
    while delta <= rango_minutos + EPS_MIN:
        cand_dt = nac_base + dt.timedelta(minutes=delta)
        cusps = casas_natales(cand_dt.year, cand_dt.month, cand_dt.day, cand_dt.hour, cand_dt.minute,
                               nac_utc_offset, lat, lon)
        directa = proluna(cusps, evento_year, evento_month, evento_day, evento_hour, evento_minute,
                           evento_utc_offset, cand_dt.year, cand_dt.month, cand_dt.day, cand_dt.hour,
                           cand_dt.minute, nac_utc_offset, conversa=False)
        conversa = proluna(cusps, evento_year, evento_month, evento_day, evento_hour, evento_minute,
                            evento_utc_offset, cand_dt.year, cand_dt.month, cand_dt.day, cand_dt.hour,
                            cand_dt.minute, nac_utc_offset, conversa=True)
        diferencia = abs(_diff_angular(directa["lon"], conversa["lon"]))
        aspecto, orbe = _orbe_a_multiplo_15(diferencia)
        candidatos.append({
            "hora_candidata": f"{cand_dt.hour:02d}:{cand_dt.minute:02d}",
            "delta_minutos": delta,
            "proluna_directa": {"signo": directa["signo"], "grado": directa["grado"], "lon": round(directa["lon"], 4)},
            "proluna_conversa": {"signo": conversa["signo"], "grado": conversa["grado"], "lon": round(conversa["lon"], 4)},
            "diferencia_grados": round(diferencia, 4),
            "aspecto_mas_cercano": aspecto,
            "orbe": round(orbe, 4),
        })
        delta += paso_minutos

    candidatos.sort(key=lambda c: c["orbe"])
    return {
        "total_candidatos": len(candidatos),
        "mejores": candidatos[:15],
        "todos": candidatos,
        "nota": ("Rectificación por Proluna directa/conversa (Bonito): se prueba la hora de nacimiento minuto a "
                 "minuto y se calcula, para cada candidata, la Proluna DIRECTA y la Proluna CONVERSA en el "
                 "momento del evento conocido — la hora correcta es la de MENOR orbe a un múltiplo exacto de "
                 "15° entre ambas. Los 15 candidatos de menor orbe se listan primero; recuerde que, por la "
                 "propia técnica, más de un minuto puede dar un orbe bajo — Bonito recomienda cruzar el "
                 "resultado con otro evento conocido si hay ambigüedad."),
    }
