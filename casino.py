# -*- coding: utf-8 -*-
"""
Programa Omega — variante "casino" (ventana corta, suerte económica).

Fuente: f5ffa7ea-attachment.txt (transcripción de clase), resumida en
revision_batch5.md entrada 6.

TÉCNICA (tal como la describe Bonito): dentro de una ventana horaria corta
(el ejemplo real es de 2 horas, 18:00-20:00), escanea los planetas en
tránsito real — Venus (Geo Y Helio — "duplica las ventanas de contacto"),
Júpiter, Saturno y Urano (Geo y Helio) — buscando Sextil o Trígono contra
el BANCO de posiciones fijas personales de Fechas Gemelas (Ascendente,
Sol, Medio Cielo y Rueda de la Fortuna — el mismo banco de 4 variantes
Geo/Helio x Trópico/Sideral que usa Programa Omega). Además cruza la Luna
en tránsito (rápida) contra ese mismo banco con los 4 aspectos mayores
(conjunción, oposición, sextil, trígono) — "momentos de imantación".
EXCLUYE explícitamente Mercurio y Marte ("Marte no permite ganar
dinero" — están vinculados a acción/decisión, no a finanzas). Los
instantes donde varios de estos tránsitos caen muy cerca en el tiempo
("cuanto más exacta la coincidencia en segundos, mayor la probabilidad de
ganar") son los horarios recomendados para jugar.

RECONSTRUCCIÓN HONESTA: el procedimiento original (Winstar → Excel →
Omega 2, columnas pegadas a mano, bug de duplicados del programa viejo)
se reemplaza acá por el mismo patrón de bisección exacta que usa el resto
del proyecto, aplicado a cada cuerpo/variante contra el banco — el rodeo
de Excel/Omega 2 era la limitación del software de 2011, no parte de la
técnica. No se implementa un "puntaje de confianza" propio: se listan
todos los instantes encontrados, ordenados por orbe/hora, para que Celina
identifique a simple vista los agrupamientos (varios aspectos cayendo
casi en el mismo minuto), tal como hacía Bonito a mano ordenando por
columna de horario.
"""
from astro import cuerpo_base_lon, jd_to_local, _diff_angular

CUERPOS_FAVORABLES = ["VENUS", "JUPITER", "SATURNO", "URANO"]
ASPECTOS_CASINO = {"Sextil": 60, "Trígono": 120}
ASPECTOS_LUNA_SOL = {"Conjunción": 0, "Sextil": 60, "Trígono": 120, "Oposición": 180}
PUNTOS_BANCO = ("sol", "ascendente", "mc", "rueda_de_la_fortuna")


def _lon_transito(jd, cuerpo, helio):
    if cuerpo == "LUNA":
        from astro import sol_luna_geo_tropical
        _, luna_lon = sol_luna_geo_tropical(jd)
        return luna_lon
    lon, _ = cuerpo_base_lon(jd, cuerpo, helio=helio, sideral=False)
    return lon


def _banco_persona(year, month, day, hour, minute, utc_offset, lat, lon, anios_atras, anios_adelante):
    from astro import calcular_fechas_gemelas
    fechas_gemelas = calcular_fechas_gemelas(year, month, day, hour, minute, utc_offset,
                                              anios_atras=anios_atras, anios_adelante=anios_adelante,
                                              lat=lat, lon=lon)
    banco = []
    for variante, lista in fechas_gemelas.items():
        for entrada in lista:
            for clave in PUNTOS_BANCO:
                punto = entrada.get(clave)
                if punto:
                    banco.append({"grado": punto["lon"], "punto": clave, "variante": variante,
                                  "fecha_origen": entrada["fecha_local"]})
    return banco


def _buscar_aspectos_en_ventana(jd_ini, jd_fin, objetivo, cuerpo, helio, aspectos, paso_segundos=20):
    EPS = 1e-4
    paso = paso_segundos / 86400.0
    resultados = []
    jd = jd_ini

    def sep(j):
        return _diff_angular(_lon_transito(j, cuerpo, helio), objetivo)

    prev = sep(jd)
    while jd < jd_fin:
        jd_next = min(jd + paso, jd_fin)
        curr = sep(jd_next)
        for nombre_asp, angulo in aspectos.items():
            d_prev = abs(prev) - angulo
            d_curr = abs(curr) - angulo
            if (d_prev > 0) != (d_curr > 0):
                lo, hi = jd, jd_next
                dlo = d_prev
                for _ in range(40):
                    mid = (lo + hi) / 2
                    dmid = abs(sep(mid)) - angulo
                    if (dmid > 0) == (dlo > 0):
                        lo, dlo = mid, dmid
                    else:
                        hi = mid
                raiz = (lo + hi) / 2
                if abs(abs(sep(raiz)) - angulo) < EPS:
                    resultados.append({"jd": raiz, "aspecto": nombre_asp})
        prev, jd = curr, jd_next
    return resultados


def escanear_casino(persona, jd_ventana_ini, jd_ventana_fin, utc_offset_salida,
                     anios_atras=60, anios_adelante=60):
    """'persona' = dict con year/month/day/hour/minute/utc_offset/lat/lon
    (los datos de nacimiento/referencia). Devuelve todos los instantes
    dentro de [jd_ventana_ini, jd_ventana_fin] en que Venus/Júpiter/
    Saturno/Urano (Geo y Helio) hacen sextil/trígono, o la Luna hace
    conjunción/sextil/trígono/oposición, con el banco de Sol/Ascendente/
    MC/Rueda de la Fortuna de Fechas Gemelas de la persona."""
    banco = _banco_persona(persona["year"], persona["month"], persona["day"],
                            persona["hour"], persona["minute"], persona["utc_offset"],
                            persona["lat"], persona["lon"], anios_atras, anios_adelante)

    eventos = []
    for cuerpo in CUERPOS_FAVORABLES:
        for helio in (False, True):
            for punto in banco:
                for hit in _buscar_aspectos_en_ventana(jd_ventana_ini, jd_ventana_fin, punto["grado"],
                                                        cuerpo, helio, ASPECTOS_CASINO):
                    eventos.append({
                        "hora_local": jd_to_local(hit["jd"], utc_offset_salida),
                        "cuerpo_en_transito": f"{cuerpo.capitalize()} {'Helio' if helio else 'Geo'}",
                        "aspecto": hit["aspecto"], "objetivo": punto["punto"],
                        "variante_origen": punto["variante"], "fecha_origen": punto["fecha_origen"],
                    })
    for punto in banco:
        for hit in _buscar_aspectos_en_ventana(jd_ventana_ini, jd_ventana_fin, punto["grado"],
                                                "LUNA", False, ASPECTOS_LUNA_SOL):
            eventos.append({
                "hora_local": jd_to_local(hit["jd"], utc_offset_salida),
                "cuerpo_en_transito": "Luna", "aspecto": hit["aspecto"], "objetivo": punto["punto"],
                "variante_origen": punto["variante"], "fecha_origen": punto["fecha_origen"],
            })

    eventos.sort(key=lambda e: (e["hora_local"]["hour"], e["hora_local"]["minute"], e["hora_local"]["second"]))
    return {
        "total_banco": len(banco), "total_eventos": len(eventos), "eventos": eventos,
        "nota": ("Técnica de 'casino' de Bonito: Venus/Júpiter/Saturno/Urano (Geo y Helio) en sextil/trígono, y "
                 "Luna en conjunción/sextil/trígono/oposición, contra el banco de Sol/Ascendente/MC/Rueda de la "
                 "Fortuna de las Fechas Gemelas de la persona — excluye Mercurio y Marte a propósito ('Marte no "
                 "permite ganar dinero'). Los horarios recomendados son los que muestran VARIOS de estos "
                 "instantes agrupados muy cerca en el tiempo — a simple vista en la tabla, ordenada por hora."),
    }
