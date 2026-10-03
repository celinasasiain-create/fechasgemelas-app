# -*- coding: utf-8 -*-
"""
Etapa Mellizos — técnica de rectificación de horarios de mellizos/gemelos de
Hugo Bonito.

Mecanismo reconstruido a partir de la transcripción real de la clase (caso
Pablo/Alejandro) y de Gemelos.doc (caso Jazmín/Sofía):

1) Se arma primero el "radix en reposo" de la madre (y, si se tienen, del
   padre y de un hijo): TODOS los Soles de sus propias Fechas Gemelas, base
   Plutón y base Neptuno, en las 4 variantes Geo/Helio x Trópico/Sideral —
   más su Sol natal. Esa es la lista de longitudes de REFERENCIA.

2) Se parte de un horario aproximado del mellizo (Bonito usa el punto medio
   entre los dos horarios aproximados que suele dar la madre) y se calculan
   sus propias Fechas Gemelas. Se recorre retorno por retorno buscando cuál
   Luna cae cerca de alguna de las longitudes de referencia — eso da un
   candidato: "este retorno, de esta variante, apunta a esta referencia".

3) Recién ahí se afina: se ajusta la HORA de nacimiento del mellizo (no la
   fecha del retorno) hasta que, al recalcular ESE MISMO retorno con la hora
   ajustada, su Luna caiga en conjunción PARTIL exacta con la referencia. Es
   sensible porque el retorno puede estar a cientos de años de distancia: un
   pequeño corrimiento en la hora de origen desplaza levemente la longitud
   natal del cuerpo base, lo que desplaza la fecha exacta del retorno lejano
   (amplificado por la distancia), lo que mueve la Luna varios minutos de
   arco — así se puede "buscar por bisección" igual que con la Luna natal en
   rectificar_por_luna, pero aplicado al retorno identificado, no a la Luna
   natal del mellizo.

4) Como triangulación adicional, Bonito cruza cada candidato con Proluna:
   calcula la edad de la madre en el momento del nacimiento candidato
   (directa y conversa = 84 - directa) — informativo, no se usa acá para
   descartar candidatos automáticamente, se lo dejamos ver a la astróloga.

NO implementado (deliberadamente): la asignación final "quién es quién"
comparando, retorno por retorno, los aspectos de la carta interceptada de
cada mellizo contra TODOS sus planetas natales — el motor actual no calcula
un tema natal completo (solo Sol/Luna/ángulos), y es una etapa mayor aparte.
"""
import datetime as dt
from astro import (
    jd_from_local, jd_to_local, sol_luna_geo_tropical, calcular_fechas_gemelas,
    cuerpo_base_lon, buscar_retornos, sign_of, norm360, _diff_angular,
)

VARIANTES = {
    "geo_tropico": dict(helio=False, sideral=False),
    "geo_sideral": dict(helio=False, sideral=True),
    "helio_tropico": dict(helio=True, sideral=False),
    "helio_sideral": dict(helio=True, sideral=True),
}
VARIANTE_LABEL = {
    "geo_tropico": "Geo/Tróp", "geo_sideral": "Geo/Sid",
    "helio_tropico": "Helio/Tróp", "helio_sideral": "Helio/Sid",
}


def _edad_en_anios(fecha_nacimiento, fecha_objetivo):
    delta = fecha_objetivo - fecha_nacimiento
    return delta.total_seconds() / (365.2425 * 86400.0)


def _sol_natal(persona):
    jd = jd_from_local(persona["year"], persona["month"], persona["day"],
                        persona["hour"], persona["minute"], persona["utc_offset"])
    sol_lon, _ = sol_luna_geo_tropical(jd)
    return sol_lon


def _referencias_de_persona(clave, datos, anios_adelante, anios_atras):
    """Sol natal + todos los Soles de las Fechas Gemelas (base Plutón y
    Neptuno, 4 variantes) de una persona — su 'radix en reposo'."""
    referencias = []
    sol_lon = _sol_natal(datos)
    signo, grado = sign_of(sol_lon)
    referencias.append({
        "lon": sol_lon, "signo": signo, "grado": round(grado, 4),
        "etiqueta": f"Sol natal de {clave}", "persona": clave, "origen": "natal",
    })
    for cuerpo_base in ("PLUTON", "NEPTUNO"):
        carta = calcular_fechas_gemelas(
            datos["year"], datos["month"], datos["day"],
            datos["hour"], datos["minute"], datos["utc_offset"],
            anios_adelante=anios_adelante, anios_atras=anios_atras,
            cuerpo_base=cuerpo_base,
        )
        for variante, lista in carta.items():
            for r in lista:
                referencias.append({
                    "lon": r["sol"]["lon"], "signo": r["sol"]["signo"], "grado": r["sol"]["grado"],
                    "etiqueta": (f"Sol de {clave} — Fecha Gemela base {cuerpo_base.capitalize()} "
                                 f"({VARIANTE_LABEL[variante]}, {r['fecha_local']['year']})"),
                    "persona": clave, "origen": f"retorno_{cuerpo_base.lower()}",
                })
    return referencias


def construir_referencias(personas, anios_adelante=250, anios_atras=250):
    referencias = []
    for clave, datos in personas.items():
        if datos:
            referencias += _referencias_de_persona(clave, datos, anios_adelante, anios_atras)
    return referencias


def escanear_candidatos(mellizo, referencias, cuerpo_base=None,
                         anios_adelante=250, anios_atras=250, orbe_max=0.5, top=8):
    """Calcula las Fechas Gemelas del mellizo (hora aproximada) y busca, entre
    todas las combinaciones retorno x referencia, cuáles Lunas caen más cerca
    de algún Sol de referencia. Devuelve los mejores candidatos (crudos, sin
    afinar todavía)."""
    cuerpos = [cuerpo_base] if cuerpo_base else ["PLUTON", "NEPTUNO"]
    candidatos = []
    for cb in cuerpos:
        carta = calcular_fechas_gemelas(
            mellizo["year"], mellizo["month"], mellizo["day"],
            mellizo["hour_aprox"], mellizo["minute_aprox"], mellizo["utc_offset"],
            anios_adelante=anios_adelante, anios_atras=anios_atras, cuerpo_base=cb,
        )
        for variante, lista in carta.items():
            for r in lista:
                for ref in referencias:
                    d = abs(_diff_angular(r["luna"]["lon"], ref["lon"]))
                    if d <= orbe_max:
                        candidatos.append({
                            "cuerpo_base": cb, "variante": variante,
                            "jd_ancla": r["jd"], "fecha_retorno_aprox": r["fecha_local"],
                            "luna_inicial": r["luna"], "orbe_inicial": round(d, 4),
                            "referencia": ref,
                        })
    candidatos.sort(key=lambda c: c["orbe_inicial"])
    return candidatos[:top]


def _luna_del_retorno_mas_cercano(jd_origen_trial, cuerpo_base, helio, sideral, jd_ancla, ventana_dias=90):
    """Para un origen de prueba, recalcula ese retorno puntual (el más
    cercano a jd_ancla) y devuelve (jd_retorno, luna_lon). Búsqueda acotada
    (rápida) porque solo interesa el cruce más cercano al ancla original."""
    lon_objetivo, _ = cuerpo_base_lon(jd_origen_trial, cuerpo_base, helio=helio, sideral=sideral)
    jd_ini = jd_ancla - ventana_dias
    jd_fin = jd_ancla + ventana_dias
    paso = 2.0 if helio else 0.5
    jds = buscar_retornos(jd_origen_trial, lon_objetivo, jd_ini, jd_fin, helio, sideral,
                           paso_dias=paso, cuerpo=cuerpo_base, max_retornos=20)
    jds = [jd for jd in jds if abs(jd - jd_origen_trial) > 1.0]
    if not jds:
        return None
    jd_ret = min(jds, key=lambda jd: abs(jd - jd_ancla))
    _, luna_lon = sol_luna_geo_tropical(jd_ret)
    return jd_ret, luna_lon


def rectificar_candidato(mellizo, candidato, ventana_horas=1.5, tolerancia_segundos=200):
    """Ajusta la hora de nacimiento del mellizo (por bisección, dentro de
    +-ventana_horas alrededor de la hora aproximada) hasta que el retorno
    identificado en 'candidato' haga conjunción partil con su referencia."""
    cuerpo_base = candidato["cuerpo_base"]
    helio = VARIANTES[candidato["variante"]]["helio"]
    sideral = VARIANTES[candidato["variante"]]["sideral"]
    jd_ancla = candidato["jd_ancla"]
    lon_ref = candidato["referencia"]["lon"]
    utc_offset = mellizo["utc_offset"]

    jd_centro = jd_from_local(mellizo["year"], mellizo["month"], mellizo["day"],
                               mellizo["hour_aprox"], mellizo["minute_aprox"], utc_offset)
    jd_ini = jd_centro - ventana_horas / 24.0
    jd_fin = jd_centro + ventana_horas / 24.0

    def f(jd_origen_trial):
        r = _luna_del_retorno_mas_cercano(jd_origen_trial, cuerpo_base, helio, sideral, jd_ancla)
        if r is None:
            return None
        jd_ret, luna_lon = r
        return _diff_angular(luna_lon, lon_ref), jd_ret, luna_lon

    flo = f(jd_ini)
    fhi = f(jd_fin)
    if flo is None or fhi is None:
        return None
    dlo, dhi = flo[0], fhi[0]
    if (dlo > 0) == (dhi > 0):
        # no cambia de signo en la ventana: no hay conjunción exacta ahí dentro
        return None

    lo, hi = jd_ini, jd_fin
    for _ in range(35):
        mid = (lo + hi) / 2
        fm = f(mid)
        if fm is None:
            return None
        dmid = fm[0]
        if (dmid > 0) == (dlo > 0):
            lo, dlo = mid, dmid
        else:
            hi = mid

    jd_origen_final = (lo + hi) / 2
    diff, jd_ret, luna_lon = f(jd_origen_final)
    diff_arcsec = abs(diff) * 3600
    if diff_arcsec > tolerancia_segundos:
        return None

    return {
        "hora_local": jd_to_local(jd_origen_final, utc_offset),
        "diferencia_arco_segundos": round(diff_arcsec, 2),
        "retorno_fecha_local": jd_to_local(jd_ret, utc_offset),
        "luna_retorno": {"lon": round(luna_lon, 5), **dict(zip(("signo", "grado"), sign_of(luna_lon)))},
        "cuerpo_base": cuerpo_base, "variante": candidato["variante"],
        "referencia": candidato["referencia"],
    }


def analizar_mellizo(mellizo, personas, cuerpo_base=None,
                      anios_adelante=250, anios_atras=250,
                      orbe_escaneo=0.5, ventana_horas=1.5, top=8):
    """Punto de entrada principal: arma referencias, escanea candidatos y
    afina cada uno por bisección. Devuelve los horarios rectificados
    encontrados, ordenados por precisión (segundos de arco de la conjunción
    final), con triangulación Proluna (edad de la madre) si hay datos de
    madre."""
    referencias = construir_referencias(personas, anios_adelante, anios_atras)
    if not referencias:
        raise ValueError("Debe aportar al menos los datos natales de un familiar de referencia "
                          "(madre, padre o hijo/a).")

    crudos = escanear_candidatos(mellizo, referencias, cuerpo_base=cuerpo_base,
                                  anios_adelante=anios_adelante, anios_atras=anios_atras,
                                  orbe_max=orbe_escaneo, top=max(top * 3, 20))

    resultados = []
    for c in crudos:
        afinado = rectificar_candidato(mellizo, c, ventana_horas=ventana_horas)
        if afinado:
            resultados.append(afinado)

    resultados.sort(key=lambda r: r["diferencia_arco_segundos"])
    resultados = resultados[:top]

    madre = personas.get("madre")
    if madre:
        madre_local = dt.datetime(madre["year"], madre["month"], madre["day"],
                                   madre["hour"], madre["minute"])
        madre_ut = madre_local - dt.timedelta(hours=madre["utc_offset"])
        for r in resultados:
            h = r["hora_local"]
            obj_local = dt.datetime(h["year"], h["month"], h["day"], h["hour"], h["minute"], h["second"])
            edad = _edad_en_anios(madre_ut, obj_local)
            edad_ciclo = edad % 84.0
            r["proluna_triangulacion"] = {
                "edad_madre_anios": round(edad, 4),
                "directa": round(edad_ciclo, 4),
                "conversa": round(84.0 - edad_ciclo, 4),
            }

    return {
        "candidatos_escaneados": len(crudos),
        "total_referencias": len(referencias),
        "resultados": resultados,
    }
