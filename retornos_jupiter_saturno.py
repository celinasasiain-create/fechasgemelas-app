# -*- coding: utf-8 -*-
"""
Retornos de Júpiter y de Saturno — Hugo Bonito.

Reconstruido de una transcripción de clase (fuente: "059b3956-attachment.txt")
donde Bonito explica, con ejemplo propio ("para mi edad, cuando llegamos
cerca de los 60..."), estas dos técnicas predictivas — la misma familia que
Retornos de Marte (ya implementado), pero con periodos mucho más largos:

  "Cuando hacemos los tránsitos de Júpiter o de Saturno, que están
  importantes, vamos a hacer el retorno de Júpiter a ver por dónde anda...
  Estos son tres retornos de Júpiter que van a estar influenciando durante
  12 años. Y el retorno de Saturno, porque también para mi edad, cuando
  llegamos cerca de los 60, ahí tenemos el 5 de noviembre del 2013, un
  retorno de Saturno que nos va a influenciar en este caso el resto, el
  resto que queda por vivir... prácticamente con un poco de suerte podrá
  haber otro retorno dentro de 29 años más."

RECONSTRUCCIÓN HONESTA — dos técnicas distintas mezcladas en la misma clase:

1. RETORNO DE JÚPITER/SATURNO COMO CARTA COMPLETA (alta confianza): exactamente
   la misma lógica que Retornos de Marte ya implementado en el proyecto —
   Júpiter (o Saturno) vuelve a su posición natal exacta, se arma la carta
   completa (Sol, Luna, Ascendente, MC, Vértex, Ecuador Celeste, Rueda de la
   Fortuna) para ese instante y lugar, y se compara contra la carta natal
   buscando aspectos. Bonito menciona explícitamente "el retorno ecuatorial
   y el retorno heliocéntrico, geocéntrico" como variantes a calcular (la
   transcripción automática del audio dice "retorno federal", que no tiene
   sentido astrológico — se interpreta con cautela como "heliocéntrico",
   pero esto NO está confirmado con certeza; por eso esta implementación
   ofrece las variantes ya estándar del proyecto —geo/helio × trópico/
   sideral— en vez de inventar una cuarta variante "ecuatorial" no
   verificable).

2. TÉCNICA DE "CADA CASA ES UN AÑO" (reconstrucción con supuestos explícitos,
   confianza media): dentro del ciclo completo de un retorno (12 años para
   Júpiter, ~29 años y medio para Saturno), Bonito divide el círculo de 360°
   de la carta de retorno en 12 casas y lee cada casa sucesiva como un tramo
   de tiempo del ciclo — "antes del quinto año, la posición del Sol...",
   "a los 6 años, este Sol en [casa] siete". Para Saturno menciona lo mismo
   con el período mayor: "Saturno nos influye cada 28 años... alrededor de
   2 años... cada cúspide" (es decir, cada casa ≈ 1/12 del ciclo de ~29
   años ≈ 2.45 años, coherente con la misma lógica que Júpiter pero a otra
   escala).

   Sistema de casas: PLACIDUS (confirmado por Celina — es el sistema que
   usaba Hugo Bonito, y ya es el default de todo el proyecto —
   puntos.HSYS_DEFAULT = b'P'). Las 12 cúspides reales de la carta de
   retorno (swe.houses_ex, ya calculadas por puntos_angulares) se usan para
   determinar en qué casa cae cada punto, en vez de dividir el círculo en
   12 arcos iguales.

   Numeración: la Casa I corresponde al primer tramo del ciclo (año 1 para
   Júpiter, ~años 0-2.45 para Saturno), la Casa II al segundo tramo, y así
   sucesivamente hasta la Casa XII. Esto sigue siendo una lectura que
   Bonito no formaliza con una regla explícita de "casa N = tramo N" en la
   transcripción disponible — es la lectura más simple y consistente con
   lo que él describe ("cada casa es un año"), pero la numeración exacta
   del tramo (por ejemplo, si el primer tramo arranca en el instante del
   retorno o unos meses antes) no está confirmada letra por letra.

   Bonito mismo aclara que esta técnica secundaria "no la utiliza para los
   clientes" — la usa para sí mismo cuando un tema no es fácil de observar
   de otra manera. Se incluye en la app con esa misma advertencia, no como
   lectura principal.
"""
from astro import (
    jd_from_local, jd_to_local, cuerpo_base_lon, buscar_retornos,
    sol_luna_geo_tropical, sign_of, comparar_sinastria, norm360,
)
from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna

# Período orbital real (usado solo para fijar la ventana/paso de búsqueda de
# cruces exactos; el retorno en sí se encuentra por búsqueda de cruce real
# con Swiss Ephemeris, no por este número).
PERIODO_ANIOS_JUPITER = 12.0        # Bonito: "durante 12 años" / "cada casa es un año"
PERIODO_ANIOS_SATURNO = 29.4571     # período orbital real; Bonito: "cada 28 años" / "29 años más"


def _retorno_generico(cuerpo, year, month, day, hour, minute, utc_offset, lat, lon,
                       anios_atras, anios_adelante, sideral, paso_dias, max_retornos):
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    lon_natal, _ = cuerpo_base_lon(jd_natal, cuerpo, helio=False, sideral=sideral)
    jd_ini = jd_natal - anios_atras * 365.2425
    jd_fin = jd_natal + anios_adelante * 365.2425
    jds = buscar_retornos(jd_natal, lon_natal, jd_ini, jd_fin, helio=False, sideral=sideral,
                           paso_dias=paso_dias, cuerpo=cuerpo, max_retornos=max_retornos)
    resultados = []
    for jd in jds:
        if abs(jd - jd_natal) < 1.0:
            continue
        sol_lon, luna_lon = sol_luna_geo_tropical(jd)
        sol_signo, sol_grado = sign_of(sol_lon)
        luna_signo, luna_grado = sign_of(luna_lon)
        angulos = puntos_angulares(jd, lat, lon)  # Placidus (puntos.HSYS_DEFAULT), incluye "cusps"
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
            "cusps": angulos["cusps"],  # las 12 cúspides Placidus, para la técnica "casa=período"
        })
    resultados.sort(key=lambda r: r["jd"])
    return resultados


def retornos_jupiter(year, month, day, hour, minute, utc_offset, lat, lon,
                      anios_atras=60, anios_adelante=60, sideral=False):
    """Retornos de Júpiter — Júpiter vuelve a su longitud natal cada ~12
    años (con alguna vuelta extra por retrogradación, igual que Marte)."""
    return _retorno_generico("JUPITER", year, month, day, hour, minute, utc_offset, lat, lon,
                              anios_atras, anios_adelante, sideral, paso_dias=8, max_retornos=60)


def retornos_saturno(year, month, day, hour, minute, utc_offset, lat, lon,
                      anios_atras=90, anios_adelante=90, sideral=False):
    """Retornos de Saturno — ciclo de ~29 años y medio; en la vida de una
    persona suele haber uno o dos retornos exactos (el clásico "retorno de
    Saturno" cerca de los 29-30 años, y para quien llega, otro cerca de los
    58-59)."""
    return _retorno_generico("SATURNO", year, month, day, hour, minute, utc_offset, lat, lon,
                              anios_atras, anios_adelante, sideral, paso_dias=15, max_retornos=20)


def _carta_comparable(retorno):
    return {k: v for k, v in retorno.items()
            if k in ("sol", "luna", "ascendente", "mc", "vertex", "ecuador_celeste", "rueda_de_la_fortuna")}


def comparar_retorno_jupiter_vs_natal(retorno_jupiter, carta_natal, nombre_natal="Natal"):
    """Aspectos entre una carta de Retorno de Júpiter y la natal fija."""
    return comparar_sinastria(carta_natal, _carta_comparable(retorno_jupiter), nombre_natal, "Retorno de Júpiter")


def comparar_retorno_saturno_vs_natal(retorno_saturno, carta_natal, nombre_natal="Natal"):
    """Aspectos entre una carta de Retorno de Saturno y la natal fija."""
    return comparar_sinastria(carta_natal, _carta_comparable(retorno_saturno), nombre_natal, "Retorno de Saturno")


def _casa_placidus_de_grado(lon_punto, cusps):
    """Casa (1 a 12) de un punto por sistema PLACIDUS, usando las 12
    cúspides reales de la carta (cusps[0]=cúspide I ... cusps[11]=cúspide
    XII, tal como las devuelve swe.houses_ex). Un punto está en la casa N
    si, avanzando en sentido directo desde la cúspide N, se lo encuentra
    antes que la cúspide N+1."""
    lon_punto = norm360(lon_punto)
    for n in range(12):
        c1 = norm360(cusps[n])
        c2 = norm360(cusps[(n + 1) % 12])
        ancho_casa = norm360(c2 - c1) or 360.0  # cúspides coincidentes (caso polar extremo): tratar como 360°
        distancia_punto = norm360(lon_punto - c1)
        if distancia_punto < ancho_casa:
            return n + 1
    return 12  # fallback de seguridad, no debería alcanzarse


def lectura_casa_periodo(retorno, carta_natal, periodo_anios_total, nombre_natal="Natal"):
    """Técnica de 'cada casa es un año' (Júpiter) / 'cada cúspide ~2 años y
    medio' (Saturno): divide el ciclo completo del retorno en 12 tramos —
    uno por casa PLACIDUS de la carta de retorno, usando sus cúspides
    reales (confirmado por Celina: Placidus es el sistema de Bonito) — y,
    para cada tramo, lista qué puntos —de la carta natal y de la carta del
    propio retorno— caen en esa casa por posición. Bonito aclara que esta
    lectura secundaria 'no la utiliza para los clientes', solo para sí mismo
    cuando un tema no es fácil de observar de otra manera — se devuelve con
    esa misma advertencia."""
    cusps = retorno["cusps"]
    anios_por_casa = periodo_anios_total / 12.0
    puntos_natal = {k: v for k, v in carta_natal.items()
                     if k in ("sol", "luna", "ascendente", "mc", "vertex", "ecuador_celeste", "rueda_de_la_fortuna")}
    puntos_retorno = _carta_comparable(retorno)

    casas = []
    for n in range(1, 13):
        anio_desde = round((n - 1) * anios_por_casa, 2)
        anio_hasta = round(n * anios_por_casa, 2)
        puntos_en_casa = []
        for nombre, p in puntos_natal.items():
            if _casa_placidus_de_grado(p["lon"], cusps) == n:
                puntos_en_casa.append({"punto": nombre.capitalize(), "origen": "natal", "signo": p["signo"], "grado": p["grado"]})
        for nombre, p in puntos_retorno.items():
            if _casa_placidus_de_grado(p["lon"], cusps) == n:
                puntos_en_casa.append({"punto": nombre.capitalize(), "origen": "retorno", "signo": p["signo"], "grado": p["grado"]})
        casas.append({
            "casa": n, "anio_desde": anio_desde, "anio_hasta": anio_hasta,
            "cuspide": round(norm360(cusps[n - 1]), 4),
            "puntos": puntos_en_casa,
        })
    return {
        "fecha_retorno": retorno["fecha_local"],
        "periodo_anios_total": periodo_anios_total,
        "anios_por_casa": round(anios_por_casa, 3),
        "casas": casas,
        "nota": ("Técnica secundaria de Bonito ('cada casa es un año' para Júpiter, cada cúspide "
                 "~2 años y medio para Saturno): él mismo dice que no la usa con clientes, sino "
                 "para sí mismo cuando un tema no se ve fácil de otra manera. Sistema de casas: "
                 "Placidus (swe.houses_ex), el mismo que usa el resto de la app."),
    }
