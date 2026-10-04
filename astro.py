# -*- coding: utf-8 -*-
"""
Motor de cálculo para la Técnica de las Fechas Gemelas (Hugo Bonito).

Usa pyswisseph con el motor Moshier incorporado (sin necesidad de archivos
de efemérides externos) — precisión de arco-segundo, la que exige la técnica
("grado, minuto, segundo exactos").
"""
import swisseph as swe
import datetime as dt
import os

swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
EPHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")
swe.set_ephe_path(EPHE_DIR)

SIGNS = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
         "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]

PERIODO_PLUTON_ANIOS = 247.94  # período orbital, para los saltos de "+240 años"
PERIODO_NEPTUNO_ANIOS = 164.79  # período orbital de Neptuno (técnica de Mellizos)

CUERPOS_BASE = {
    "PLUTON": swe.PLUTO, "NEPTUNO": swe.NEPTUNE, "MARTE": swe.MARS,
    "SATURNO": swe.SATURN, "URANO": swe.URANUS, "JUPITER": swe.JUPITER,
    "SOL": swe.SUN, "LUNA": swe.MOON, "VENUS": swe.VENUS,
    # Quirón necesita el archivo de asteroides seas_18.se1 (incluido en
    # ephe/ — Astrodienst/JPL, sin él swisseph tira error incluso con
    # Moshier, porque los asteroides no forman parte de esa teoría
    # analítica). El Nodo (medio, el que usa la mayoría del software de
    # la época de Bonito, incluido Winstar) es puramente analítico y no
    # necesita ningún archivo.
    "QUIRON": swe.CHIRON, "NODO": swe.MEAN_NODE,
    "MERCURIO": swe.MERCURY,
    # Luna Negra (media/"Lilith media"): punto puramente matemático (el
    # apogeo medio de la órbita lunar), no un cuerpo físico — no necesita
    # ningún archivo de efemérides, igual que el Nodo medio.
    "LUNA_NEGRA": swe.MEAN_APOG,
}


def norm360(x):
    return x % 360


def sign_of(lon):
    lon = norm360(lon)
    idx = int(lon // 30)
    return SIGNS[idx], lon - idx * 30


def jd_from_local(year, month, day, hour, minute, utc_offset):
    """Convierte fecha/hora LOCAL a Día Juliano UT."""
    local_dt = dt.datetime(year, month, day, hour, minute)
    ut_dt = local_dt - dt.timedelta(hours=utc_offset)
    return swe.julday(ut_dt.year, ut_dt.month, ut_dt.day,
                       ut_dt.hour + ut_dt.minute / 60.0 + ut_dt.second / 3600.0)


def jd_to_local(jd, utc_offset):
    """Convierte Día Juliano UT a fecha/hora LOCAL (dict)."""
    y, m, d, h = swe.revjul(jd)
    ut_dt = dt.datetime(y, m, d) + dt.timedelta(hours=h)
    local_dt = ut_dt + dt.timedelta(hours=utc_offset)
    return {
        "year": local_dt.year, "month": local_dt.month, "day": local_dt.day,
        "hour": local_dt.hour, "minute": local_dt.minute,
        "second": local_dt.second, "iso": local_dt.isoformat(),
    }


def cuerpo_base_lon(jd, cuerpo="PLUTON", helio=False, sideral=False):
    """Longitud eclíptica del 'cuerpo base' (Plutón o Neptuno, los dos
    usados por Bonito para las Fechas Gemelas) en el modo pedido."""
    swe_id = CUERPOS_BASE[cuerpo]
    flag = swe.FLG_SWIEPH | swe.FLG_SPEED
    if helio:
        flag |= swe.FLG_HELCTR
    if sideral:
        flag |= swe.FLG_SIDEREAL
    try:
        (lo, la, r, spd, *_), _ = swe.calc_ut(jd, swe_id, flag)
    except swe.Error:
        flagm = swe.FLG_MOSEPH | swe.FLG_SPEED
        if helio:
            flagm |= swe.FLG_HELCTR
        if sideral:
            flagm |= swe.FLG_SIDEREAL
        (lo, la, r, spd, *_), _ = swe.calc_ut(jd, swe_id, flagm)
    return lo, spd


def pluton_lon(jd, helio=False, sideral=False):
    """Longitud eclíptica de Plutón en el modo pedido (alias histórico de
    cuerpo_base_lon con cuerpo='PLUTON', mantenido por compatibilidad)."""
    return cuerpo_base_lon(jd, "PLUTON", helio, sideral)


def sol_luna_geo_tropical(jd):
    """Posiciones del Sol y la Luna, Geocéntricas Trópicas (siempre igual,
    independientemente del modo en que se haya encontrado el retorno de
    Plutón — son los marcadores que se comparan entre 'fechas gemelas')."""
    flag = swe.FLG_SWIEPH | swe.FLG_SPEED
    sol, _ = swe.calc_ut(jd, swe.SUN, flag)
    luna, _ = swe.calc_ut(jd, swe.MOON, flag)
    return sol[0], luna[0]


def _diff_angular(a, b):
    """Diferencia angular con signo, en rango (-180, 180]."""
    d = (a - b + 180) % 360 - 180
    return d


# --- Cotidian Cardinal 1 ("Quotidian Cardinal" / "Daily House Progressed
# Chart" del Winstar/Matrix Software) -----------------------------------
#
# Reconstruida a partir de referencias indirectas en el material de Bonito
# ("cotidian cardinal 1... una especie de revolución de progresión
# secundaria vinculada con las posiciones cardinales"; "mueve el ascendente
# a razón de 1 grado por día") combinadas con documentación pública del
# propio Winstar/Matrix Software, que describe una "Daily House Progressed
# Chart" (también llamada "Quotidian" — de ahí "Cotidian") en la cual los
# 4 puntos cardinales (Ascendente, MC, Vértex, Ecuador Celeste) completan
# un círculo de 360° por cada año real transcurrido, dirigiendo el ARMC
# (Tiempo Sidéreo Local, NO la longitud eclíptica) y recalculando esos
# puntos por trigonometría esférica con la latitud natal — a diferencia
# del Arco Solar, que sí dirige por longitud eclíptica.
#
# Validada en signo (no en grado exacto, por incertidumbre en el horario
# natal de prueba) contra el caso real de Boca Juniors (Programa Omega,
# archivo ff94e6f2): MC dirigido cae en Acuario, igual que el 4°50'
# Acuario que reporta Bonito en esa clase.
RATE_COTIDIAN_CARDINAL = 360.0 / 365.2425  # grados de ARMC por día real


def cotidian_cardinal_1(jd_natal, lat, lon, jd_objetivo):
    """Dirige el Ascendente, MC, Vértex y Ecuador Celeste natales a
    'jd_objetivo' mediante Cotidian Cardinal 1: avanza el ARMC natal a
    razón de 360°/año real (RATE_COTIDIAN_CARDINAL por día) y recalcula
    los 4 puntos cardinales con ese ARMC dirigido, por trigonometría
    esférica (swe.houses_armc), usando la latitud geográfica natal."""
    import puntos as _puntos
    cusps, ascmc = swe.houses_ex2(jd_natal, lat, lon, _puntos.HSYS_DEFAULT)[:2]
    armc_natal = ascmc[2]
    eps = swe.calc_ut(jd_natal, swe.ECL_NUT)[0][0]

    dias = jd_objetivo - jd_natal
    arco = norm360(dias * RATE_COTIDIAN_CARDINAL)
    armc_dirigido = norm360(armc_natal + arco)

    _, ascmc_dir = swe.houses_armc(armc_dirigido, lat, eps, _puntos.HSYS_DEFAULT)
    asc, mc, vertex, eq = ascmc_dir[0], ascmc_dir[1], ascmc_dir[3], ascmc_dir[4]
    return {
        "arco_armc": round(arco, 4),
        "ascendente": _puntos._punto(asc),
        "mc": _puntos._punto(mc),
        "vertex": _puntos._punto(vertex),
        "ecuador_celeste": _puntos._punto(eq),
    }


def _cotidian_cardinal_lon(jd_natal, lat, armc_natal, eps, punto, jd):
    """Longitud de un punto cardinal ('ascendente'|'mc'|'vertex'|
    'ecuador_celeste') dirigido por Cotidian Cardinal 1 a 'jd'."""
    import puntos as _puntos
    arco = norm360((jd - jd_natal) * RATE_COTIDIAN_CARDINAL)
    armc_dirigido = norm360(armc_natal + arco)
    _, ascmc_dir = swe.houses_armc(armc_dirigido, lat, eps, _puntos.HSYS_DEFAULT)
    idx = {"ascendente": 0, "mc": 1, "vertex": 3, "ecuador_celeste": 4}[punto]
    return ascmc_dir[idx]


def _arco_cotidian_monotono(jd_natal, jd):
    """Arco (sin mod 360) de Cotidian Cardinal 1 para 'jd' — monotónico
    creciente, para bisección segura por comparación '<' (mismo patrón
    que _resolver_fecha_por_arco, sin el bug de _diff_angular)."""
    return (jd - jd_natal) * RATE_COTIDIAN_CARDINAL


def _resolver_fecha_cotidian_cardinal(jd_natal, lat, lon, punto, lon_objetivo,
                                       jd_desde, anios_max=250):
    """Bisección monotónica (misma técnica que _resolver_fecha_por_arco):
    encuentra las fechas en que el punto cardinal dirigido por Cotidian
    Cardinal 1 pasa por 'lon_objetivo', usando el arco de ARMC (que crece
    sin envolverse) para evitar el bug de falsos cruces antipodales."""
    import puntos as _puntos
    cusps, ascmc = swe.houses_ex2(jd_natal, lat, lon, _puntos.HSYS_DEFAULT)[:2]
    armc_natal = ascmc[2]
    eps = swe.calc_ut(jd_natal, swe.ECL_NUT)[0][0]

    lon0 = _cotidian_cardinal_lon(jd_natal, lat, armc_natal, eps, punto, jd_desde)
    arco_para_llegar = norm360(lon_objetivo - lon0)
    dias_por_grado = 1.0 / RATE_COTIDIAN_CARDINAL
    resultados = []
    vuelta = 0
    jd_fin = jd_desde + anios_max * 365.2425
    while True:
        jd_cand = jd_desde + (arco_para_llegar + 360 * vuelta) * dias_por_grado
        if jd_cand > jd_fin:
            break
        resultados.append(jd_cand)
        vuelta += 1
    return resultados


def buscar_retornos(jd_origen, lon_objetivo, jd_inicio, jd_fin, helio, sideral,
                     paso_dias=3, max_retornos=60, cuerpo="PLUTON"):
    """Busca TODOS los cruces donde el cuerpo base (Plutón o Neptuno, en el
    modo pedido) pasa por lon_objetivo entre jd_inicio y jd_fin. Debido a las
    retrogradaciones (en modo geocéntrico) puede haber más de un cruce cerca
    de cada 'vuelta' orbital — se detectan todos por cambio de signo en pasos
    finos y se refinan por bisección hasta precisión de segundos de arco."""
    EPS = 1e-4  # grados; tolerancia para aceptar la raíz como cruce genuino
                # (no el punto antipodal, donde _diff_angular también
                # cambia de signo por el "salto" de +180 a -180 sin pasar
                # realmente por el objetivo — ver nota abajo)

    resultados = []
    jd = jd_inicio
    prev_diff = _diff_angular(cuerpo_base_lon(jd, cuerpo, helio, sideral)[0], lon_objetivo)
    prev_jd = jd
    while jd < jd_fin and len(resultados) < max_retornos:
        jd_next = jd + paso_dias
        diff_next = _diff_angular(cuerpo_base_lon(jd_next, cuerpo, helio, sideral)[0], lon_objetivo)
        if prev_diff == 0:
            resultados.append(prev_jd)
        elif (prev_diff > 0) != (diff_next > 0):
            # cambio de signo de _diff_angular: puede ser un cruce genuino
            # del objetivo, o un salto discontinuo al pasar por el punto
            # antipodal (objetivo + 180°), donde _diff_angular también
            # cambia de signo (de +180 a -180) sin que el cuerpo pase
            # realmente por lon_objetivo. Se refina por bisección y luego
            # se verifica que la raíz hallada esté realmente cerca del
            # objetivo antes de aceptarla, descartando el antípoda.
            lo, hi = prev_jd, jd_next
            dlo = prev_diff
            for _ in range(60):
                mid = (lo + hi) / 2
                dmid = _diff_angular(cuerpo_base_lon(mid, cuerpo, helio, sideral)[0], lon_objetivo)
                if (dmid > 0) == (dlo > 0):
                    lo, dlo = mid, dmid
                else:
                    hi = mid
            raiz = (lo + hi) / 2
            if abs(_diff_angular(cuerpo_base_lon(raiz, cuerpo, helio, sideral)[0], lon_objetivo)) < EPS:
                resultados.append(raiz)
        prev_jd, prev_diff = jd_next, diff_next
        jd = jd_next
    return resultados


def calcular_fechas_gemelas(year, month, day, hour, minute, utc_offset,
                             anios_adelante=250, anios_atras=250,
                             lat=None, lon=None, cuerpo_base="PLUTON"):
    """Calcula los retornos del cuerpo base (Plutón por defecto; Neptuno
    para la técnica de Mellizos de Bonito) en las 4 variantes (Geo/Helio x
    Trópico/Sideral) hacia adelante y atrás de la fecha de origen, y arma
    la 'carta muerta' con el Sol y la Luna (Geocéntricos Trópicos) de cada
    retorno encontrado.

    Si se pasan lat/lon (lugar de nacimiento), además de Sol/Luna se agrega
    a cada retorno su Ascendente, MC, Vértex, Ecuador Celeste y Rueda de la
    Fortuna — los "equivalentes" de cada Fecha Gemela para esos puntos
    personales, calculados como si fuera una carta completa levantada en
    ese instante y lugar."""
    jd_origen = jd_from_local(year, month, day, hour, minute, utc_offset)
    jd_ini = jd_origen - anios_atras * 365.2425
    jd_fin = jd_origen + anios_adelante * 365.2425

    # el paso de búsqueda de Neptuno usa el mismo criterio que Plutón (más
    # rápido en heliocéntrico, que no retrograda)
    variantes = {
        "geo_tropico": dict(helio=False, sideral=False),
        "geo_sideral": dict(helio=False, sideral=True),
        "helio_tropico": dict(helio=True, sideral=False),
        "helio_sideral": dict(helio=True, sideral=True),
    }

    calcular_angulos = lat is not None and lon is not None
    if calcular_angulos:
        from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna

    resultado = {}
    for nombre, params in variantes.items():
        lon_objetivo, _ = cuerpo_base_lon(jd_origen, cuerpo_base, **params)
        paso = 20 if params["helio"] else 5
        jds = buscar_retornos(jd_origen, lon_objetivo, jd_ini, jd_fin, cuerpo=cuerpo_base,
                               paso_dias=paso, **params)
        lista = []
        for jd in jds:
            if abs(jd - jd_origen) < 1.0:
                continue  # excluir la fecha de origen (coincide trivialmente consigo misma)
            sol_lon, luna_lon = sol_luna_geo_tropical(jd)
            sol_sign, sol_deg = sign_of(sol_lon)
            luna_sign, luna_deg = sign_of(luna_lon)
            entrada = {
                "jd": jd,
                "fecha_local": jd_to_local(jd, utc_offset),
                "sol": {"lon": sol_lon, "signo": sol_sign, "grado": round(sol_deg, 4)},
                "luna": {"lon": luna_lon, "signo": luna_sign, "grado": round(luna_deg, 4)},
            }
            if calcular_angulos:
                angulos = puntos_angulares(jd, lat, lon)
                diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
                fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)
                entrada["ascendente"] = angulos["ascendente"]
                entrada["mc"] = angulos["mc"]
                entrada["vertex"] = angulos["vertex"]
                entrada["ecuador_celeste"] = angulos["ecuador_celeste"]
                entrada["rueda_de_la_fortuna"] = fortuna
            lista.append(entrada)
        resultado[nombre] = lista
    return resultado


ASPECTOS = {"Conjunción": 0, "Sextil": 60, "Cuadratura": 90, "Trígono": 120, "Oposición": 180}
ORBE_PLANETA = 1.0  # según Bonito: 1° para planetas (Sol/Luna)
ORBE_PARTIL = 0.05  # aspecto "partil" (grado, minuto, segundo casi exactos)


def _aspecto(lon1, lon2, orbe_max):
    d = abs(_diff_angular(lon1, lon2))
    for nombre, angulo in ASPECTOS.items():
        diff = abs(d - angulo)
        if diff <= orbe_max:
            return {"aspecto": nombre, "orbe": round(diff, 4), "partil": diff <= ORBE_PARTIL}
    return None


CUERPOS_COMPARABLES = ("sol", "luna", "ascendente", "mc", "vertex", "ecuador_celeste", "rueda_de_la_fortuna")
ORBE_CUSPIDE = 2.0  # según Bonito: 2° para cúspides (Asc/MC/Vértex/Ecuador Celeste/Rueda de Fortuna)
CUERPOS_ANGULARES = ("ascendente", "mc", "vertex", "ecuador_celeste", "rueda_de_la_fortuna")


def carta_natal_simple(year, month, day, hour, minute, utc_offset, lat, lon):
    """Carta natal simple (un solo instante, no 'carta muerta' de retornos):
    Sol, Luna, Ascendente, MC, Vértex, Ecuador Celeste y Rueda de la Fortuna
    — los 7 puntos que ya calcula el motor de Fechas Gemelas, usados acá para
    Sinastría entre dos personas."""
    from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna
    jd = jd_from_local(year, month, day, hour, minute, utc_offset)
    sol_lon, luna_lon = sol_luna_geo_tropical(jd)
    sol_signo, sol_grado = sign_of(sol_lon)
    luna_signo, luna_grado = sign_of(luna_lon)
    angulos = puntos_angulares(jd, lat, lon)
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)
    return {
        "sol": {"lon": sol_lon, "signo": sol_signo, "grado": round(sol_grado, 4)},
        "luna": {"lon": luna_lon, "signo": luna_signo, "grado": round(luna_grado, 4)},
        "ascendente": angulos["ascendente"],
        "mc": angulos["mc"],
        "vertex": angulos["vertex"],
        "ecuador_celeste": angulos["ecuador_celeste"],
        "rueda_de_la_fortuna": fortuna,
    }


def comparar_sinastria(cartaA, cartaB, nombreA="A", nombreB="B"):
    """Compara las 7x7 combinaciones de puntos entre dos cartas natales
    simples (carta_natal_simple), buscando aspectos mayores. Orbe 1° cuando
    ambos puntos son Sol/Luna, 2° si alguno es una cúspide/punto angular
    (Ascendente, MC, Vértex, Ecuador Celeste, Rueda de Fortuna) — la misma
    convención de orbes que usa Bonito para Fechas Gemelas."""
    coincidencias = []
    for cuerpoA, puntoA in cartaA.items():
        for cuerpoB, puntoB in cartaB.items():
            orbe_max = ORBE_CUSPIDE if (cuerpoA in CUERPOS_ANGULARES or cuerpoB in CUERPOS_ANGULARES) else ORBE_PLANETA
            asp = _aspecto(puntoA["lon"], puntoB["lon"], orbe_max)
            if asp:
                coincidencias.append({
                    "cuerpo_A": f"{nombreA}.{cuerpoA}", "cuerpo_B": f"{nombreB}.{cuerpoB}",
                    "signo_A": puntoA["signo"], "grado_A": puntoA["grado"],
                    "signo_B": puntoB["signo"], "grado_B": puntoB["grado"],
                    **asp,
                })
    coincidencias.sort(key=lambda c: c["orbe"])
    return coincidencias


def comparar_natal_vs_retornos(carta_natal, carta_muerta, nombre_natal="Natal", nombre_retornos="Retornos",
                                cuerpos=CUERPOS_COMPARABLES):
    """Sinastría Atemporal, tercera capa (documentada por Bonito en el caso
    Camilo/Rosario): compara la carta natal fija de una persona contra TODAS
    las Fechas Gemelas (retornos, base Plutón o Neptuno) de la otra — a
    diferencia de comparar_sinastria (natal contra natal, un solo instante)
    y de comparar_cartas_muertas (retornos contra retornos de ambas personas
    — la 'Sinastría Temporal', ya cubierta por la pestaña de Comparar Fechas
    Gemelas)."""
    coincidencias = []
    for variante, lista in carta_muerta.items():
        for retorno in lista:
            for cuerpo_ret in cuerpos:
                if cuerpo_ret not in retorno:
                    continue
                for cuerpo_nat in cuerpos:
                    if cuerpo_nat not in carta_natal:
                        continue
                    orbe_max = ORBE_CUSPIDE if (cuerpo_ret in CUERPOS_ANGULARES or cuerpo_nat in CUERPOS_ANGULARES) else ORBE_PLANETA
                    asp = _aspecto(retorno[cuerpo_ret]["lon"], carta_natal[cuerpo_nat]["lon"], orbe_max)
                    if asp:
                        coincidencias.append({
                            "variante": variante, "fecha_retorno": retorno["fecha_local"]["iso"],
                            "cuerpo_A": f"{nombre_retornos}.{cuerpo_ret} (retorno)",
                            "cuerpo_B": f"{nombre_natal}.{cuerpo_nat} (natal)",
                            "signo_A": retorno[cuerpo_ret]["signo"], "grado_A": retorno[cuerpo_ret]["grado"],
                            "signo_B": carta_natal[cuerpo_nat]["signo"], "grado_B": carta_natal[cuerpo_nat]["grado"],
                            **asp,
                        })
    coincidencias.sort(key=lambda c: c["orbe"])
    return coincidencias[:200]


def comparar_cartas_muertas(cartaA, cartaB, nombreA="A", nombreB="B", cuerpos=("sol", "luna")):
    """Compara todas las combinaciones de puntos de dos 'cartas muertas'
    (resultado de calcular_fechas_gemelas para cada persona/fecha), buscando
    aspectos — especialmente conjunciones/aspectos partiles, que según Bonito
    indican vínculo fuerte o confirman un horario de nacimiento correcto.

    'cuerpos' son los puntos a comparar; por defecto solo Sol/Luna (los
    únicos presentes si calcular_fechas_gemelas se llamó sin lat/lon). Si
    se calcularon los ángulos (con lat/lon), se puede pasar
    CUERPOS_COMPARABLES para comparar todos los puntos personales."""
    coincidencias = []
    for varA, listaA in cartaA.items():
        for varB, listaB in cartaB.items():
            for retA in listaA:
                for retB in listaB:
                    for cuerpoA in cuerpos:
                        if cuerpoA not in retA:
                            continue
                        for cuerpoB in cuerpos:
                            if cuerpoB not in retB:
                                continue
                            asp = _aspecto(retA[cuerpoA]["lon"], retB[cuerpoB]["lon"], ORBE_PLANETA)
                            if asp:
                                coincidencias.append({
                                    "variante_A": varA, "variante_B": varB,
                                    "fecha_A": retA["fecha_local"]["iso"],
                                    "fecha_B": retB["fecha_local"]["iso"],
                                    "cuerpo_A": f"{nombreA}.{cuerpoA}",
                                    "cuerpo_B": f"{nombreB}.{cuerpoB}",
                                    "signo_A": retA[cuerpoA]["signo"], "grado_A": retA[cuerpoA]["grado"],
                                    "signo_B": retB[cuerpoB]["signo"], "grado_B": retB[cuerpoB]["grado"],
                                    **asp,
                                })
    coincidencias.sort(key=lambda c: c["orbe"])
    return coincidencias


def progresiones_secundarias(year, month, day, hour, minute, utc_offset, lat, lon,
                              year_obj, month_obj, day_obj, hour_obj=12, minute_obj=0,
                              utc_offset_obj=None):
    """Progresiones Secundarias (1 día = 1 año), técnica mencionada por Bonito
    como triangulación adicional en Sinastría y usada también de forma
    independiente (ej. Luna Negra progresada por casas).

    Convención estándar ("day for a year"): la carta progresada para una
    fecha objetivo se calcula tomando el Día Juliano natal y sumándole tantos
    DÍAS como AÑOS de edad tiene la persona en la fecha objetivo — luego se
    calculan Sol, Luna y los puntos angulares (Ascendente, MC, Vértex,
    Ecuador Celeste, Rueda de la Fortuna) en ese instante, usando el lugar
    de nacimiento (lat/lon natales), tal como lo hace Bonito con Winstar."""
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    jd_objetivo = jd_from_local(year_obj, month_obj, day_obj, hour_obj, minute_obj,
                                 utc_offset_obj if utc_offset_obj is not None else utc_offset)
    edad_anios = (jd_objetivo - jd_natal) / 365.2425
    jd_progresado = jd_natal + edad_anios

    sol_lon, luna_lon = sol_luna_geo_tropical(jd_progresado)
    sol_signo, sol_grado = sign_of(sol_lon)
    luna_signo, luna_grado = sign_of(luna_lon)

    from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna
    angulos = puntos_angulares(jd_progresado, lat, lon)
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)

    return {
        "edad_anios": round(edad_anios, 4),
        "jd_progresado": jd_progresado,
        "fecha_objetivo": jd_to_local(jd_objetivo, utc_offset_obj if utc_offset_obj is not None else utc_offset),
        "sol": {"lon": sol_lon, "signo": sol_signo, "grado": round(sol_grado, 4)},
        "luna": {"lon": luna_lon, "signo": luna_signo, "grado": round(luna_grado, 4)},
        "ascendente": angulos["ascendente"],
        "mc": angulos["mc"],
        "vertex": angulos["vertex"],
        "ecuador_celeste": angulos["ecuador_celeste"],
        "rueda_de_la_fortuna": fortuna,
    }


def comparar_progresiones_vs_natal(carta_natal, carta_progresada, nombre_natal="Natal",
                                    nombre_progresado="Progresado"):
    """Aspectos entre la carta progresada y la carta natal fija — reutiliza la
    misma lógica de orbes que comparar_sinastria (1° Sol/Luna, 2° cúspides)."""
    return comparar_sinastria(carta_natal, carta_progresada, nombre_natal, nombre_progresado)


def _sol_progresado_lon(jd_natal, jd_objetivo):
    """Longitud del Sol progresado (1 día = 1 año) para una fecha objetivo,
    sin necesidad de lat/lon (se usa solo para el Arco Solar)."""
    edad_anios = (jd_objetivo - jd_natal) / 365.2425
    jd_progresado = jd_natal + edad_anios
    sol_lon, _ = sol_luna_geo_tropical(jd_progresado)
    return sol_lon


def arco_solar_en(jd_natal, sol_natal_lon, jd_objetivo):
    """Arco Solar acumulado (en grados, 0-360) entre el nacimiento y la fecha
    objetivo: lo que se movió el Sol progresado desde su posición natal.
    Crece de forma prácticamente monótona (~0.9856°-1.019°/año, equivalente
    a la regla de Bonito "5 minutos de arco = 1 mes")."""
    sol_prog_lon = _sol_progresado_lon(jd_natal, jd_objetivo)
    return norm360(sol_prog_lon - sol_natal_lon)


def carta_dirigida_arco_solar(carta_natal, arco):
    """Aplica el Arco Solar (mismo desplazamiento angular para todos los
    puntos) a una carta natal simple, generando la carta 'dirigida' — técnica
    de Direcciones por Arco Solar / Arco de Jonás de Bonito."""
    dirigida = {}
    for cuerpo, punto in carta_natal.items():
        lon_dirigida = norm360(punto["lon"] + arco)
        signo, grado = sign_of(lon_dirigida)
        dirigida[cuerpo] = {"lon": lon_dirigida, "signo": signo, "grado": round(grado, 4)}
    return dirigida


def arco_solar_dirigido(year, month, day, hour, minute, utc_offset, lat, lon,
                         year_obj, month_obj, day_obj, hour_obj=12, minute_obj=0,
                         utc_offset_obj=None):
    """Arco Solar / Arco de Jonás: para una fecha objetivo, calcula cuánto
    avanzó el Sol progresado desde el nacimiento (el 'arco') y dirige TODOS
    los puntos natales (Sol, Luna, Ascendente, MC, Vértex, Ecuador Celeste,
    Rueda de la Fortuna) ese mismo arco — luego compara la carta dirigida
    contra la natal fija en busca de aspectos, tal como hacía Bonito con el
    Kepler de García (función 'Fase Angular')."""
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    jd_objetivo = jd_from_local(year_obj, month_obj, day_obj, hour_obj, minute_obj,
                                 utc_offset_obj if utc_offset_obj is not None else utc_offset)
    carta_natal = carta_natal_simple(year, month, day, hour, minute, utc_offset, lat, lon)
    sol_natal_lon = carta_natal["sol"]["lon"]
    arco = arco_solar_en(jd_natal, sol_natal_lon, jd_objetivo)
    carta_dirigida = carta_dirigida_arco_solar(carta_natal, arco)
    return {
        "arco_grados": round(arco, 4),
        "meses_equivalentes": round(arco * 60 / 5, 2),  # regla de Bonito: 5' = 1 mes
        "fecha_objetivo": jd_to_local(jd_objetivo, utc_offset_obj if utc_offset_obj is not None else utc_offset),
        "carta_natal": carta_natal,
        "carta_dirigida": carta_dirigida,
    }


def _resolver_fecha_por_arco(jd_natal, sol_natal_lon, arco_objetivo, anios_max=150):
    """Bisección: encuentra la fecha en que el Arco Solar acumulado alcanza
    'arco_objetivo' grados (arco crece monótonamente con el tiempo dentro de
    un rango de vida razonable, sin necesidad de considerar vueltas de 360°)."""
    jd_ini = jd_natal
    jd_fin = jd_natal + anios_max * 365.2425
    arco_fin = arco_solar_en(jd_natal, sol_natal_lon, jd_fin)
    if arco_objetivo > arco_fin:
        return None
    lo, hi = jd_ini, jd_fin
    for _ in range(50):
        mid = (lo + hi) / 2
        arco_mid = arco_solar_en(jd_natal, sol_natal_lon, mid)
        if arco_mid < arco_objetivo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def diagrama_flujo_arco_solar(year, month, day, hour, minute, utc_offset, lat, lon,
                               anios_adelante=100):
    """'Diagrama de flujo' del Arco Solar / Arco de Jonás: para cada punto
    natal (Luna, Ascendente, MC, Vértex, Ecuador Celeste, Rueda de la
    Fortuna) calcula las fechas futuras en que el Sol dirigido por Arco Solar
    hace aspecto mayor (conjunción/sextil/cuadratura/trígono/oposición) con
    ese punto — ordenadas cronológicamente, tal como el pronóstico anual que
    armaba Bonito con Winstar/Kepler."""
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    carta_natal = carta_natal_simple(year, month, day, hour, minute, utc_offset, lat, lon)
    sol_natal_lon = carta_natal["sol"]["lon"]

    eventos = []
    for cuerpo, punto in carta_natal.items():
        if cuerpo == "sol":
            continue
        lon_punto = punto["lon"]
        for nombre_asp, angulo in ASPECTOS.items():
            deltas = [0] if angulo == 0 else [angulo, -angulo]
            for delta in deltas:
                arco_objetivo = norm360(lon_punto - sol_natal_lon + delta)
                jd_evento = _resolver_fecha_por_arco(jd_natal, sol_natal_lon, arco_objetivo, anios_adelante)
                if jd_evento is not None:
                    eventos.append({
                        "cuerpo_natal": cuerpo,
                        "signo_natal": punto["signo"], "grado_natal": punto["grado"],
                        "aspecto": nombre_asp,
                        "arco_grados": round(arco_objetivo, 4),
                        "edad_anios": round((jd_evento - jd_natal) / 365.2425, 3),
                        "fecha": jd_to_local(jd_evento, utc_offset),
                    })
    eventos.sort(key=lambda e: e["edad_anios"])
    return eventos


CATALOGO_ESTRELLAS = [
    "Alcyone", "Aldebaran", "Rigel", "Capella", "Betelgeuse", "Sirius", "Canopus",
    "Castor", "Pollux", "Alphard", "Regulus", "Denebola", "Spica", "Arcturus",
    "Alnilam", "Algol", "Antares", "Vega", "Altair", "Fomalhaut", "Deneb", "Markab",
    "Achernar", "Facies",
]  # las estrellas fijas de referencia más usadas en interpretación astrológica
ORBE_ESTRELLA = 1.0  # Bonito: orbe estricto de 1° para estrellas fijas


def estrella_lon(nombre, jd):
    """Longitud eclíptica tropical (con precesión real) de una estrella fija
    del catálogo, para el instante jd, vía Swiss Ephemeris (swe.fixstar2_ut).
    Re-fija la ruta de efemérides en cada llamada: el servidor Flask puede
    atender cada request en un hilo distinto del que hizo el set_ephe_path
    inicial (al importar el módulo), y el estado interno de la librería C de
    Swiss Ephemeris para estrellas fijas no siempre queda compartido entre
    hilos si no se refuerza así."""
    swe.set_ephe_path(EPHE_DIR)
    (lo, *_), _, _ = swe.fixstar2_ut(nombre, jd)
    return norm360(lo)


def estrellas_en_punto(lon_punto, jd_ref, orbe=ORBE_ESTRELLA, catalogo=None):
    """Estrellas fijas del catálogo en conjunción (dentro de 'orbe') con una
    longitud dada, en el instante jd_ref."""
    catalogo = catalogo or CATALOGO_ESTRELLAS
    resultado = []
    for nombre in catalogo:
        try:
            lon_estrella = estrella_lon(nombre, jd_ref)
        except swe.Error:
            continue
        d = abs(_diff_angular(lon_punto, lon_estrella))
        if d <= orbe:
            signo, grado = sign_of(lon_estrella)
            resultado.append({"estrella": nombre, "lon": round(lon_estrella, 4),
                               "signo": signo, "grado": round(grado, 4), "orbe": round(d, 4)})
    resultado.sort(key=lambda e: e["orbe"])
    return resultado


def estrellas_en_carta(carta, jd_ref, orbe=ORBE_ESTRELLA, catalogo=None):
    """Para cada punto de una carta (natal, progresada o dirigida por Arco
    Solar), busca conjunciones con estrellas fijas del catálogo."""
    resultado = {}
    for cuerpo, punto in carta.items():
        coincidencias = estrellas_en_punto(punto["lon"], jd_ref, orbe, catalogo)
        if coincidencias:
            resultado[cuerpo] = coincidencias
    return resultado


def diagrama_estrellas_progresadas(year, month, day, hour, minute, utc_offset, lat, lon,
                                    anios_adelante=100, orbe=ORBE_ESTRELLA, catalogo=None):
    """Combinación de Progresiones (Arco Solar) con Estrellas Fijas, tal como
    la usaba Bonito: fechas futuras en que el Sol dirigido por Arco Solar
    llega a conjunción (orbe 1°) con cada estrella fija del catálogo."""
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    carta_natal = carta_natal_simple(year, month, day, hour, minute, utc_offset, lat, lon)
    sol_natal_lon = carta_natal["sol"]["lon"]
    catalogo = catalogo or CATALOGO_ESTRELLAS

    eventos = []
    for nombre in catalogo:
        try:
            lon_estrella_natal = estrella_lon(nombre, jd_natal)
        except swe.Error:
            continue
        arco_objetivo = norm360(lon_estrella_natal - sol_natal_lon)
        jd_evento = _resolver_fecha_por_arco(jd_natal, sol_natal_lon, arco_objetivo, anios_adelante)
        if jd_evento is not None:
            signo, grado = sign_of(lon_estrella_natal)
            eventos.append({
                "estrella": nombre,
                "signo": signo, "grado": round(grado, 4),
                "edad_anios": round((jd_evento - jd_natal) / 365.2425, 3),
                "fecha": jd_to_local(jd_evento, utc_offset),
            })
    eventos.sort(key=lambda e: e["edad_anios"])
    return eventos


def retornos_marte(year, month, day, hour, minute, utc_offset, lat, lon,
                    anios_atras=10, anios_adelante=10, sideral=False):
    """Retornos de Marte — técnica de pronóstico de salud de Bonito: 'las
    pasadas seguro que están indicando y justificando el problema de salud,
    las futuras nos darán posibilidades de una relocación'. Marte vuelve a su
    posición natal cada ~2 años (con alguna vuelta extra por retrogradación),
    a diferencia de los retornos de Plutón/Neptuno de las Fechas Gemelas.

    Para cada retorno se arma la carta completa (Sol, Luna, Ascendente, MC,
    Vértex, Ecuador Celeste, Rueda de la Fortuna) en el lugar dado (con
    soporte de relocación, como Revolución Solar/Lunar), lista para comparar
    contra la carta natal — Bonito buscaba especialmente aspectos hostiles o
    favorables al Ascendente/Ecuador Celeste ('que corten nuestra vitalidad')."""
    from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    marte_natal_lon, _ = cuerpo_base_lon(jd_natal, "MARTE", helio=False, sideral=sideral)
    jd_ini = jd_natal - anios_atras * 365.2425
    jd_fin = jd_natal + anios_adelante * 365.2425
    jds = buscar_retornos(jd_natal, marte_natal_lon, jd_ini, jd_fin, helio=False, sideral=sideral,
                           paso_dias=2, cuerpo="MARTE", max_retornos=40)

    resultados = []
    for jd in jds:
        if abs(jd - jd_natal) < 1.0:
            continue
        sol_lon, luna_lon = sol_luna_geo_tropical(jd)
        sol_signo, sol_grado = sign_of(sol_lon)
        luna_signo, luna_grado = sign_of(luna_lon)
        angulos = puntos_angulares(jd, lat, lon)
        diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
        fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)
        resultados.append({
            "jd": jd,
            "fecha_local": jd_to_local(jd, utc_offset),
            "edad_anios": round((jd - jd_natal) / 365.2425, 3),
            "sol": {"lon": sol_lon, "signo": sol_signo, "grado": round(sol_grado, 4)},
            "luna": {"lon": luna_lon, "signo": luna_signo, "grado": round(luna_grado, 4)},
            "ascendente": angulos["ascendente"],
            "mc": angulos["mc"],
            "vertex": angulos["vertex"],
            "ecuador_celeste": angulos["ecuador_celeste"],
            "rueda_de_la_fortuna": fortuna,
        })
    resultados.sort(key=lambda r: r["jd"])
    return resultados


def comparar_retorno_marte_vs_natal(retorno_marte, carta_natal, nombre_natal="Natal"):
    """Aspectos entre una carta de Retorno de Marte y la natal fija — misma
    lógica de orbes que comparar_sinastria (reutilizada tal cual)."""
    carta_retorno = {k: v for k, v in retorno_marte.items()
                      if k in ("sol", "luna", "ascendente", "mc", "vertex",
                               "ecuador_celeste", "rueda_de_la_fortuna")}
    return comparar_sinastria(carta_natal, carta_retorno, nombre_natal, "Retorno de Marte")


def rectificar_por_luna(year, month, day, hour_aprox, minute_aprox, utc_offset,
                         lon_referencia, sideral=True, ventana_horas=2, aspecto_objetivo=None, second=0):
    """Técnica de rectificación de Bonito (caso Columbia): ajusta la HORA
    exacta de un evento hasta que la Luna en tránsito (Sideral por defecto,
    como en el ejemplo de Bonito) haga aspecto PARTIL con una posición de
    referencia (ej. un Sol de otra Fecha Gemela relacionada).
    Devuelve, para cada aspecto mayor posible, el horario exacto donde ocurre
    dentro de la ventana pedida (la Luna se mueve rápido: ~0.5°/hora, así que
    esto sí permite afinar minutos/segundos, a diferencia de comparar Soles)."""
    jd_centro = jd_from_local(year, month, day, hour_aprox, minute_aprox, utc_offset) + (second or 0) / 86400.0
    jd_ini = jd_centro - ventana_horas / 24.0
    jd_fin = jd_centro + ventana_horas / 24.0

    aspectos_a_buscar = {aspecto_objetivo: ASPECTOS[aspecto_objetivo]} if aspecto_objetivo else ASPECTOS

    def luna_en(jd):
        flag = swe.FLG_SWIEPH | swe.FLG_SPEED
        if sideral:
            flag |= swe.FLG_SIDEREAL
        (lo, *_), _ = swe.calc_ut(jd, swe.MOON, flag)
        return lo

    EPS = 1e-4  # grados; tolerancia para descartar falsos cruces en el antípoda
                # (ver nota en astro.buscar_retornos: _diff_angular también cambia
                # de signo al pasar por objetivo+180°, sin que la Luna pase
                # realmente por 'obj')

    resultados = []
    for nombre_asp, angulo in aspectos_a_buscar.items():
        objetivo = norm360(lon_referencia + angulo)
        # buscar cruce (probar también el objetivo opuesto por simetría del aspecto)
        for obj in {norm360(lon_referencia + angulo), norm360(lon_referencia - angulo)}:
            paso = 1.0 / 24 / 12  # 5 minutos, la Luna es rápida
            jd = jd_ini
            prev = _diff_angular(luna_en(jd), obj)
            while jd < jd_fin:
                jd_next = jd + paso
                curr = _diff_angular(luna_en(jd_next), obj)
                if (prev > 0) != (curr > 0):
                    lo, hi = jd, jd_next
                    dlo = prev
                    for _ in range(40):
                        mid = (lo + hi) / 2
                        dmid = _diff_angular(luna_en(mid), obj)
                        if (dmid > 0) == (dlo > 0):
                            lo, dlo = mid, dmid
                        else:
                            hi = mid
                    jd_exacto = (lo + hi) / 2
                    diff_final = abs(_diff_angular(luna_en(jd_exacto), obj))
                    if diff_final < EPS:
                        resultados.append({
                            "aspecto": nombre_asp,
                            "hora_local": jd_to_local(jd_exacto, utc_offset),
                            "luna_lon": round(luna_en(jd_exacto), 5),
                            "diferencia_arco_segundos": round(diff_final * 3600, 2),
                        })
                prev = curr
                jd = jd_next
    resultados.sort(key=lambda r: r["diferencia_arco_segundos"])
    return resultados


# --- Cartas Análogas -------------------------------------------------------
#
# Técnica propia de Bonito, descubierta y narrada por él mismo en vivo sobre
# su propia carta (archivo e9fa6dd8): distinta de Fechas Gemelas (que usa
# retornos de Plutón/Neptuno) — acá se buscan otras fechas donde el SOL
# mismo, alternando entre el sistema Sideral y el Trópico, vuelve a caer en
# la MISMA posición numérica (grado/minuto/segundo), y cada una de esas
# fechas se considera una carta "propia" más (una "gemela" del Sol).
#
# Reconstrucción del mecanismo (verificada numéricamente contra el propio
# ejemplo narrado por Bonito — su Sol natal 29°15'18" Escorpio del 21/11/1954,
# con las fechas análogas resultantes 15/12/1954 y 8/1/1955 — con Swiss
# Ephemeris, natal 23:32:57 Argentina):
#
#   1) Se parte del Sol TRÓPICO natal (L0 = 29°15'18" Escorpio = 239.255°).
#   2) Se busca, avanzando desde la fecha de partida, la primera fecha en que
#      el Sol SIDERAL (Fagan-Bradley) alcanza ese MISMO valor numérico L0
#      (238.75° sideral el 15/12/1954 en nuestro cálculo, contra 239.255°
#      objetivo — la pequeña diferencia de grado, no de fecha, se explica por
#      diferencias de efeméride/hora exacta con el software original de
#      Bonito). Como el Sol nunca retrograda, esto tarda apenas ~24-25 días
#      (lo que el Sol sideral demora en "alcanzar" al trópico, dado que están
#      separados por la ayanamsa, ~24° en esta época) — NO casi un año, que
#      es lo que tardaría un verdadero "retorno solar" en el MISMO sistema.
#      Esta fecha (D1) es la primera "carta análoga".
#   3) En D1 se lee la posición TRÓPICA del Sol en ese instante (L1 ≈ L0 +
#      ayanamsa ≈ 23°22' Sagitario, tal cual dice Bonito) y ese valor pasa a
#      ser el nuevo objetivo.
#   4) Se repite el paso 2 buscando desde D1 el Sol SIDERAL = L1 → D2 (8 de
#      enero de 1955 en el ejemplo, ~24 días después de D1). Y así sucesivamente.
#
# Esto explica el detalle que en un principio parecía un error del propio
# Bonito o una imposibilidad astronómica (fechas "análogas" separadas por
# solo ~24 días, cuando el Sol tarda ~365 días en volver a su posición): no
# es un retorno solar real, es un cruce entre los dos sistemas de referencia
# (Sideral/Trópico), que ocurre a un ritmo de aproximadamente 1 vez cada
# "ayanamsa en grados" días. Bonito llama a este ritmo, de manera informal,
# "12 meses hacia adelante y 12 meses hacia atrás" (12 pasos de esta cadena,
# no 12 meses calendario exactos — 12 pasos de ~24 días cubren en realidad
# unos 9-10 meses reales).
#
# VALIDACIÓN: con el horario natal de Bonito (21/11/1954, 23:32, Argentina)
# el resultado coincide con su propio ejemplo narrado con precisión de
# SEGUNDOS DE ARCO: Sol natal calculado 29°15'16" Escorpio (Bonito dice
# 29°15'18"), Luna natal 22°14'15" Libra (Bonito dice 22°14'19"); primera
# carta análoga el 15/12/1954 con Sol trópico 23°22'13" Sagitario (Bonito
# dice 23°22'15"); segunda carta análoga el 8/1/1955, EXACTO. Es la
# reconstrucción mejor validada de todo el proyecto hasta ahora.

def _buscar_cruce_sol(jd_desde, lon_objetivo, sideral, direccion=1, ventana_dias=90):
    """Busca, desde 'jd_desde' y avanzando (direccion=1) o retrocediendo
    (direccion=-1) en el tiempo, la primera fecha en que el Sol (en el
    sistema pedido) cruza 'lon_objetivo'. El Sol nunca retrograda, así que
    hay un único cruce en cada tramo monótono — se verifica igual la raíz
    (mismo patrón EPS que el resto del motor) para no depender de esa
    garantía si el objetivo estuviera casi opuesto (caso patológico)."""
    EPS = 1e-4

    def lon_en(jd):
        flag = swe.FLG_SWIEPH
        if sideral:
            flag |= swe.FLG_SIDEREAL
        pos, _ = swe.calc_ut(jd, swe.SUN, flag)
        return pos[0]

    paso = 1.0 * (1 if direccion >= 0 else -1)
    jd = jd_desde
    prev = _diff_angular(lon_en(jd), lon_objetivo)
    if abs(prev) < EPS:
        # ya estamos sobre el objetivo (p.ej. el propio punto de partida):
        # avanzar un paso para buscar el PRÓXIMO cruce, no reportar este.
        jd += paso
        prev = _diff_angular(lon_en(jd), lon_objetivo)

    pasos_max = int(ventana_dias / abs(paso)) + 5
    for _ in range(pasos_max):
        jd_next = jd + paso
        curr = _diff_angular(lon_en(jd_next), lon_objetivo)
        if (prev > 0) != (curr > 0):
            lo, hi = (jd, jd_next) if direccion >= 0 else (jd_next, jd)
            dlo = _diff_angular(lon_en(lo), lon_objetivo)
            for _ in range(60):
                mid = (lo + hi) / 2
                dmid = _diff_angular(lon_en(mid), lon_objetivo)
                if (dmid > 0) == (dlo > 0):
                    lo, dlo = mid, dmid
                else:
                    hi = mid
            raiz = (lo + hi) / 2
            if abs(_diff_angular(lon_en(raiz), lon_objetivo)) < EPS:
                return raiz
        prev = curr
        jd = jd_next
    return None  # no debería pasar para el Sol en una ventana de meses


def cartas_analogas(persona, pasos_adelante=12, pasos_atras=12, utc_offset_salida=None):
    """Genera la cadena de 'Cartas Análogas' de Bonito: fechas donde el Sol,
    alternando entre Sideral y Trópico, vuelve a caer en la misma posición
    numérica que en la carta anterior de la cadena (empezando por el Sol
    trópico natal). Cada fecha resultante es, según Bonito, una carta que la
    persona 'puede considerar propia'. Si se aportan lat/lon (el lugar de
    nacimiento, u otro lugar de referencia) se calculan también Ascendente,
    MC, Vértex y Ecuador Celeste de cada carta análoga; si no, solo Sol y
    Luna trópicos."""
    from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna

    jd_natal = jd_from_local(persona["year"], persona["month"], persona["day"],
                              persona["hour"], persona["minute"], persona["utc_offset"])
    sol_natal_trop, luna_natal_trop = sol_luna_geo_tropical(jd_natal)
    flag_sid = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    sol_natal_sid = swe.calc_ut(jd_natal, swe.SUN, flag_sid)[0][0]
    utc_salida = utc_offset_salida if utc_offset_salida is not None else persona["utc_offset"]
    lat, lon = persona.get("lat"), persona.get("lon")

    def _carta_en(jd, objetivo_buscado, sideral_buscado):
        sol_trop, luna_trop = sol_luna_geo_tropical(jd)
        sol_sid = swe.calc_ut(jd, swe.SUN, flag_sid)[0][0]
        sol_signo, sol_grado = sign_of(sol_trop)
        luna_signo, luna_grado = sign_of(luna_trop)
        sol_sid_signo, sol_sid_grado = sign_of(sol_sid)
        carta = {
            "fecha_local": jd_to_local(jd, utc_salida),
            "sistema_buscado": "sideral" if sideral_buscado else "trópico",
            "objetivo_buscado": round(objetivo_buscado, 5),
            "sol": {"lon": round(sol_trop, 5), "signo": sol_signo, "grado": round(sol_grado, 4)},
            "sol_sideral": {"lon": round(sol_sid, 5), "signo": sol_sid_signo, "grado": round(sol_sid_grado, 4)},
            "luna": {"lon": round(luna_trop, 5), "signo": luna_signo, "grado": round(luna_grado, 4)},
        }
        if lat is not None and lon is not None:
            angulos = puntos_angulares(jd, lat, lon)
            diurna = es_diurna(sol_trop, angulos["ascendente"]["lon"])
            fortuna = rueda_de_la_fortuna(sol_trop, luna_trop, angulos["ascendente"]["lon"], diurna)
            carta.update({
                "ascendente": angulos["ascendente"], "mc": angulos["mc"],
                "vertex": angulos["vertex"], "ecuador_celeste": angulos["ecuador_celeste"],
                "rueda_de_la_fortuna": fortuna,
            })
        return carta

    def _cadena(direccion, pasos):
        """Hacia adelante (direccion=1): se busca cuándo el Sol SIDERAL
        alcanza el valor que tiene el Sol TRÓPICO (que le lleva ~1 ayanamsa
        de ventaja) — el sideral 'lo alcanza' avanzando en el tiempo.
        Hacia atrás (direccion=-1): es la imagen espejo — el Sol TRÓPICO va
        ADELANTE del sideral, así que retrocediendo en el tiempo el trópico
        'desciende' hasta alcanzar el valor que tenía el sideral. En ambos
        casos el objetivo de cada paso siguiente es la lectura del OTRO
        sistema en la fecha recién encontrada."""
        cadena = []
        jd_cursor = jd_natal
        buscar_sideral = direccion > 0
        objetivo = sol_natal_trop if buscar_sideral else sol_natal_sid
        for _ in range(pasos):
            jd_encontrado = _buscar_cruce_sol(jd_cursor, objetivo, sideral=buscar_sideral,
                                               direccion=direccion, ventana_dias=90)
            if jd_encontrado is None:
                break
            carta = _carta_en(jd_encontrado, objetivo, buscar_sideral)
            cadena.append(carta)
            objetivo = carta["sol"]["lon"] if buscar_sideral else carta["sol_sideral"]["lon"]
            jd_cursor = jd_encontrado
        return cadena

    adelante = _cadena(1, pasos_adelante)
    atras = _cadena(-1, pasos_atras)
    atras.reverse()

    sol_natal_signo, sol_natal_grado = sign_of(sol_natal_trop)
    luna_natal_signo, luna_natal_grado = sign_of(luna_natal_trop)
    return {
        "natal": {
            "fecha_local": jd_to_local(jd_natal, utc_salida),
            "sol": {"lon": round(sol_natal_trop, 5), "signo": sol_natal_signo, "grado": round(sol_natal_grado, 4)},
            "luna": {"lon": round(luna_natal_trop, 5), "signo": luna_natal_signo, "grado": round(luna_natal_grado, 4)},
        },
        "cartas_hacia_atras": atras,
        "cartas_hacia_adelante": adelante,
        "total_cartas": len(adelante) + len(atras),
        "con_angulos": lat is not None and lon is not None,
    }
