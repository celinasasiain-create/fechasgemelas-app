# -*- coding: utf-8 -*-
"""
Revolución Solar y Revolución Lunar, con soporte de relocación.

Nota de relocación (documentada en el curso de Bonito): el MC se modifica
moviéndose ESTE-OESTE (cambio de longitud geográfica); el Vértex se
modifica moviéndose NORTE-SUR (cambio de latitud). Por eso el cálculo de
relocación siempre debe recalcular la carta completa en el lugar nuevo —
no alcanza con desplazar un solo ángulo.
"""
import swisseph as swe
import datetime as dt
from astro import norm360, sign_of, jd_from_local, jd_to_local, _diff_angular
from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna

FLAG = swe.FLG_SWIEPH | swe.FLG_SPEED


def _sol_luna(jd):
    sol, _ = swe.calc_ut(jd, swe.SUN, FLAG)
    luna, _ = swe.calc_ut(jd, swe.MOON, FLAG)
    return sol[0], luna[0]


def _buscar_retorno(lon_objetivo, jd_centro, cuerpo, ventana_dias):
    """Busca, cerca de jd_centro, el instante exacto en que 'cuerpo'
    (SUN o MOON) pasa por lon_objetivo, por bisección. Si hay más de un
    cruce dentro de la ventana, devuelve el más cercano a jd_centro."""
    EPS = 1e-4  # grados; tolerancia para descartar falsos cruces en el antípoda
                # (_diff_angular cambia de signo tanto en el objetivo real como
                # al pasar por objetivo+180°; se verifica la raíz antes de
                # aceptarla — ver nota en astro.buscar_retornos)
    jd_ini = jd_centro - ventana_dias
    jd_fin = jd_centro + ventana_dias
    paso = ventana_dias / 200.0

    def lon_en(jd):
        pos, _ = swe.calc_ut(jd, cuerpo, FLAG)
        return pos[0]

    candidatos = []
    jd = jd_ini
    prev = _diff_angular(lon_en(jd), lon_objetivo)
    while jd < jd_fin:
        jd_next = jd + paso
        curr = _diff_angular(lon_en(jd_next), lon_objetivo)
        if (prev > 0) != (curr > 0):
            lo, hi = jd, jd_next
            dlo = prev
            for _ in range(50):
                mid = (lo + hi) / 2
                dmid = _diff_angular(lon_en(mid), lon_objetivo)
                if (dmid > 0) == (dlo > 0):
                    lo, dlo = mid, dmid
                else:
                    hi = mid
            raiz = (lo + hi) / 2
            if abs(_diff_angular(lon_en(raiz), lon_objetivo)) < EPS:
                candidatos.append(raiz)
        prev = curr
        jd = jd_next

    if not candidatos:
        return None
    return min(candidatos, key=lambda c: abs(c - jd_centro))


def revolucion_solar(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset,
                      anio_revolucion, lat, lon, utc_offset,
                      lat_natal=None, lon_natal=None):
    """Calcula la Revolución Solar para 'anio_revolucion'.

    lat/lon/utc_offset = lugar y huso donde se calcula la revolución (el de
    residencia actual, o uno de prueba para evaluar una relocación).
    lat_natal/lon_natal = lugar de nacimiento (para obtener la longitud
    solar natal exacta; si no se pasan, se asume que lat/lon son también el
    lugar natal).
    """
    if lat_natal is None:
        lat_natal, lon_natal = lat, lon

    jd_natal = jd_from_local(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset)
    sol_natal_lon, _ = _sol_luna(jd_natal)

    # buscar el retorno solar cerca del cumpleaños del año pedido
    jd_aprox = jd_from_local(anio_revolucion, nac_month, nac_day, nac_hour, nac_minute, utc_offset)
    jd_rs = _buscar_retorno(sol_natal_lon, jd_aprox, swe.SUN, ventana_dias=3)
    if jd_rs is None:
        raise ValueError("No se encontró el retorno solar cerca de la fecha esperada.")

    sol_lon, luna_lon = _sol_luna(jd_rs)
    angulos = puntos_angulares(jd_rs, lat, lon)
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)

    sol_signo, sol_grado = sign_of(sol_lon)
    luna_signo, luna_grado = sign_of(luna_lon)

    return {
        "tipo": "Revolución Solar",
        "anio": anio_revolucion,
        "fecha_local": jd_to_local(jd_rs, utc_offset),
        "lugar_calculo": {"lat": lat, "lon": lon},
        "relocada": (lat, lon) != (lat_natal, lon_natal),
        "sol": {"lon": sol_lon, "signo": sol_signo, "grado": round(sol_grado, 4)},
        "luna": {"lon": luna_lon, "signo": luna_signo, "grado": round(luna_grado, 4)},
        "ascendente": angulos["ascendente"],
        "mc": angulos["mc"],
        "vertex": angulos["vertex"],
        "ecuador_celeste": angulos["ecuador_celeste"],
        "rueda_de_la_fortuna": fortuna,
    }


def revolucion_lunar(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset,
                      fecha_aproximada, lat, lon, utc_offset,
                      lat_natal=None, lon_natal=None):
    """Calcula la Revolución Lunar (mensual) más cercana a 'fecha_aproximada'
    (dict con year/month/day/hour/minute), buscando el retorno de la Luna
    a su longitud natal exacta.
    """
    if lat_natal is None:
        lat_natal, lon_natal = lat, lon

    jd_natal = jd_from_local(nac_year, nac_month, nac_day, nac_hour, nac_minute, nac_utc_offset)
    _, luna_natal_lon = _sol_luna(jd_natal)

    jd_aprox = jd_from_local(
        fecha_aproximada["year"], fecha_aproximada["month"], fecha_aproximada["day"],
        fecha_aproximada.get("hour", 12), fecha_aproximada.get("minute", 0), utc_offset,
    )
    jd_rl = _buscar_retorno(luna_natal_lon, jd_aprox, swe.MOON, ventana_dias=16)
    if jd_rl is None:
        raise ValueError("No se encontró el retorno lunar cerca de la fecha esperada.")

    sol_lon, luna_lon = _sol_luna(jd_rl)
    angulos = puntos_angulares(jd_rl, lat, lon)
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)

    sol_signo, sol_grado = sign_of(sol_lon)
    luna_signo, luna_grado = sign_of(luna_lon)

    return {
        "tipo": "Revolución Lunar",
        "fecha_local": jd_to_local(jd_rl, utc_offset),
        "lugar_calculo": {"lat": lat, "lon": lon},
        "relocada": (lat, lon) != (lat_natal, lon_natal),
        "sol": {"lon": sol_lon, "signo": sol_signo, "grado": round(sol_grado, 4)},
        "luna": {"lon": luna_lon, "signo": luna_signo, "grado": round(luna_grado, 4)},
        "ascendente": angulos["ascendente"],
        "mc": angulos["mc"],
        "vertex": angulos["vertex"],
        "ecuador_celeste": angulos["ecuador_celeste"],
        "rueda_de_la_fortuna": fortuna,
    }
