# -*- coding: utf-8 -*-
"""
Puntos de carta: Ascendente, Medio Cielo, Vértex, Ecuador Celeste (Punto
Este / Ascendente Ecuatorial) y Rueda de la Fortuna (Parte de Fortuna).

Requieren lugar geográfico (latitud/longitud), a diferencia del Sol y la
Luna que son iguales para toda la Tierra en un instante dado.
"""
import swisseph as swe
from astro import norm360, sign_of

HSYS_DEFAULT = b'P'  # Placidus — el sistema que usa Bonito/Cristoff


def casas(jd_ut, lat, lon, hsys=HSYS_DEFAULT):
    """Devuelve (cusps, ascmc) tal cual los da swisseph.
    cusps: tupla de 12 posiciones (cusps[0] = casa I, ... cusps[11] = casa XII)
    ascmc: [Asc, MC, ARMC, Vertex, Ecuador Celeste (Punto Este), co-asc Koch,
            co-asc Munkasey, ascendente polar]
    """
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys)
    return cusps, ascmc


def puntos_angulares(jd_ut, lat, lon, hsys=HSYS_DEFAULT):
    """Ascendente, MC, Vértex, Antivértex y Ecuador Celeste (Punto Este/
    Ascendente Ecuatorial) para un instante y lugar dados. El Antivértex es
    el punto exactamente opuesto al Vértex (Vértex + 180°) — Bonito, en la
    técnica de pronóstico de nacimientos: "el vértex tiene opuesto el
    antivértex... trabaja como casa cúspide de casa cuatro" (fuente:
    83f393cf-attachment.txt)."""
    cusps, ascmc = casas(jd_ut, lat, lon, hsys)
    asc = ascmc[0]
    mc = ascmc[1]
    vertex = ascmc[3]
    ecuador_celeste = ascmc[4]  # "equatorial ascendant" / Punto Este
    return {
        "ascendente": _punto(asc),
        "mc": _punto(mc),
        "vertex": _punto(vertex),
        "antivertex": _punto(norm360(vertex + 180.0)),
        "ecuador_celeste": _punto(ecuador_celeste),
        "cusps": list(cusps),
    }


def puntos_angulares_sideral(jd_ut, lat, lon, hsys=HSYS_DEFAULT):
    """Ascendente, MC, Vértex y Ecuador Celeste SIDERALES (Fagan-Bradley):
    swe.houses_ex siempre da estos puntos en trópico (no toma el sid_mode
    activo), así que se restá la ayanamsa del instante a cada uno — mismo
    criterio que el resto del proyecto (astro.py fija SIDM_FAGAN_BRADLEY)."""
    trop = puntos_angulares(jd_ut, lat, lon, hsys)
    aya = swe.get_ayanamsa_ut(jd_ut)
    out = {}
    for clave in ("ascendente", "mc", "vertex", "antivertex", "ecuador_celeste"):
        out[clave] = _punto(norm360(trop[clave]["lon"] - aya))
    return out


def _punto(lon):
    signo, grado = sign_of(lon)
    return {"lon": lon, "signo": signo, "grado": round(grado, 4)}


def rueda_de_la_fortuna(sol_lon, luna_lon, asc_lon, es_diurna):
    """Parte de Fortuna clásica (fórmula árabe):
    diurna:   Asc + Luna - Sol
    nocturna: Asc + Sol - Luna
    'es_diurna' = True si el Sol está sobre el horizonte (entre el
    Ascendente y el Descendente, en sentido directo) en el momento natal."""
    if es_diurna:
        lon = norm360(asc_lon + luna_lon - sol_lon)
    else:
        lon = norm360(asc_lon + sol_lon - luna_lon)
    return _punto(lon)


def es_diurna(sol_lon, asc_lon):
    """El Sol está 'sobre el horizonte' cuando su distancia angular al
    Ascendente (en sentido directo, antihorario) está entre 0° y 180°."""
    diff = norm360(sol_lon - asc_lon)
    return diff < 180
