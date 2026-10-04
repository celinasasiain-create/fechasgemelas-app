# -*- coding: utf-8 -*-
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from astro import (
    calcular_fechas_gemelas, comparar_cartas_muertas, rectificar_por_luna,
    CUERPOS_COMPARABLES, carta_natal_simple, comparar_sinastria, comparar_natal_vs_retornos,
    progresiones_secundarias, comparar_progresiones_vs_natal,
    arco_solar_dirigido, diagrama_flujo_arco_solar,
    estrellas_en_carta, diagrama_estrellas_progresadas, CATALOGO_ESTRELLAS,
    retornos_marte, comparar_retorno_marte_vs_natal,
    cartas_analogas,
)
from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna
from astro import jd_from_local
from revolucion import revolucion_solar, revolucion_lunar
from proluna import (casas_natales, proluna as calcular_proluna, resona as calcular_resona,
                      reluna as calcular_reluna, rectificar_hora_proluna)
from interpretacion import interpretar_aspecto, interpretar_evento_libre, ia_disponible
from mellizos import analizar_mellizo
from contacto import (
    contacto_puntual, diagrama_contacto,
    contacto_cotidian_cardinal, diagrama_cotidian_cardinal,
)
from horaria import carta_horaria
from omega import escanear_omega, comparar_omega
from imantacion import escanear_imantacion
from electivas_riesgo import escanear_electiva, escanear_manchas_solares
from discriminacion import discriminar_por_orbe
from retornos_jupiter_saturno import (
    retornos_jupiter, retornos_saturno,
    comparar_retorno_jupiter_vs_natal, comparar_retorno_saturno_vs_natal,
    lectura_casa_periodo, PERIODO_ANIOS_JUPITER, PERIODO_ANIOS_SATURNO,
)
from pronostico_natal import escanear_pronostico
from eventos_vida import evaluar_eventos_vida
from loteria import escanear_loteria_semanal, loteria_navidad
from bursatil import escanear_bursatil
from casino import escanear_casino

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)


@app.route("/api/health")
def health():
    return jsonify({"ok": True})


@app.route("/api/retornos", methods=["POST"])
def retornos():
    """Calcula las Fechas Gemelas (retornos de Plutón, 4 variantes) de una
    fecha de nacimiento u otro evento. Si se envían lat/lon, cada retorno
    incluye también Ascendente/MC/Vértex/Ecuador Celeste/Rueda de la
    Fortuna (no solo Sol/Luna)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400

    anios_adelante = data.get("anios_adelante", 250)
    anios_atras = data.get("anios_atras", 250)
    lat = data.get("lat")
    lon = data.get("lon")

    try:
        resultado = calcular_fechas_gemelas(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], data["utc_offset"],
            anios_adelante=anios_adelante, anios_atras=anios_atras,
            lat=lat, lon=lon,
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500

    total = sum(len(v) for v in resultado.values())
    return jsonify({"carta_muerta": resultado, "total_retornos": total})


@app.route("/api/comparar", methods=["POST"])
def comparar():
    """Recibe dos fechas (o dos cartas muertas ya calculadas) y devuelve
    las coincidencias (aspectos, especialmente partiles) entre ambas.
    Por defecto compara solo Sol/Luna; con "comparar_angulos": true y
    lat/lon en cada fecha, compara también Ascendente/MC/Vértex/Ecuador
    Celeste/Rueda de la Fortuna."""
    data = request.get_json(force=True)
    try:
        comparar_angulos = data.get("comparar_angulos", False)
        cuerpos = CUERPOS_COMPARABLES if comparar_angulos else ("sol", "luna")

        if "carta_A" in data and "carta_B" in data:
            cartaA, cartaB = data["carta_A"], data["carta_B"]
        else:
            fa, fb = data["fecha_A"], data["fecha_B"]
            cartaA = calcular_fechas_gemelas(
                fa["year"], fa["month"], fa["day"], fa["hour"], fa["minute"], fa["utc_offset"],
                anios_adelante=fa.get("anios_adelante", 250), anios_atras=fa.get("anios_atras", 250),
                lat=fa.get("lat") if comparar_angulos else None,
                lon=fa.get("lon") if comparar_angulos else None,
            )
            cartaB = calcular_fechas_gemelas(
                fb["year"], fb["month"], fb["day"], fb["hour"], fb["minute"], fb["utc_offset"],
                anios_adelante=fb.get("anios_adelante", 250), anios_atras=fb.get("anios_atras", 250),
                lat=fb.get("lat") if comparar_angulos else None,
                lon=fb.get("lon") if comparar_angulos else None,
            )
        nombreA = data.get("nombre_A", "A")
        nombreB = data.get("nombre_B", "B")
        coincidencias = comparar_cartas_muertas(cartaA, cartaB, nombreA, nombreB, cuerpos=cuerpos)
    except Exception as e:
        return jsonify({"error": f"No se pudo comparar: {e}"}), 500

    return jsonify({
        "coincidencias": coincidencias[:200],  # limitar respuesta
        "total_coincidencias": len(coincidencias),
        "total_partiles": sum(1 for c in coincidencias if c["partil"]),
        "ia_disponible": ia_disponible(),
    })


@app.route("/api/rectificar", methods=["POST"])
def rectificar():
    """Rectifica la HORA exacta de un evento buscando cuándo la Luna en
    tránsito (Sideral por defecto) hace aspecto partil con una posición de
    referencia dada (ej. un Sol de otra Fecha Gemela relacionada)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lon_referencia"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = rectificar_por_luna(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], data["utc_offset"],
            data["lon_referencia"],
            sideral=data.get("sideral", True),
            ventana_horas=data.get("ventana_horas", 2),
            aspecto_objetivo=data.get("aspecto_objetivo"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo rectificar: {e}"}), 500
    return jsonify({"resultados": resultado})


@app.route("/api/carta_puntos", methods=["POST"])
def carta_puntos():
    """Ascendente/MC/Vértex/Ecuador Celeste/Rueda de la Fortuna para un
    instante y lugar dados (carta natal simple, sin Fechas Gemelas)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd = jd_from_local(data["year"], data["month"], data["day"],
                            data["hour"], data["minute"], data["utc_offset"])
        angulos = puntos_angulares(jd, data["lat"], data["lon"])
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(angulos)


@app.route("/api/revolucion_solar", methods=["POST"])
def api_revolucion_solar():
    """Revolución Solar para el año pedido, con soporte de relocación
    (lat/lon del lugar donde se calcula, que puede ser distinto al natal)."""
    data = request.get_json(force=True)
    required = ["nac_year", "nac_month", "nac_day", "nac_hour", "nac_minute", "nac_utc_offset",
                "anio_revolucion", "lat", "lon", "utc_offset"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = revolucion_solar(
            data["nac_year"], data["nac_month"], data["nac_day"],
            data["nac_hour"], data["nac_minute"], data["nac_utc_offset"],
            data["anio_revolucion"], data["lat"], data["lon"], data["utc_offset"],
            lat_natal=data.get("lat_natal"), lon_natal=data.get("lon_natal"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/revolucion_lunar", methods=["POST"])
def api_revolucion_lunar():
    """Revolución Lunar más cercana a una fecha aproximada dada."""
    data = request.get_json(force=True)
    required = ["nac_year", "nac_month", "nac_day", "nac_hour", "nac_minute", "nac_utc_offset",
                "fecha_aproximada", "lat", "lon", "utc_offset"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = revolucion_lunar(
            data["nac_year"], data["nac_month"], data["nac_day"],
            data["nac_hour"], data["nac_minute"], data["nac_utc_offset"],
            data["fecha_aproximada"], data["lat"], data["lon"], data["utc_offset"],
            lat_natal=data.get("lat_natal"), lon_natal=data.get("lon_natal"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/proluna", methods=["POST"])
def api_proluna():
    """Proluna (PLN) para una fecha objetivo, dados los datos natales
    (incluyendo lat/lon, necesarios para las casas)."""
    data = request.get_json(force=True)
    required = ["nac_year", "nac_month", "nac_day", "nac_hour", "nac_minute", "nac_utc_offset",
                "nac_lat", "nac_lon",
                "year", "month", "day", "hour", "minute", "utc_offset"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        cusps = casas_natales(
            data["nac_year"], data["nac_month"], data["nac_day"],
            data["nac_hour"], data["nac_minute"], data["nac_utc_offset"],
            data["nac_lat"], data["nac_lon"],
        )
        resultado = calcular_proluna(
            cusps,
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["nac_year"], data["nac_month"], data["nac_day"],
            data["nac_hour"], data["nac_minute"], data["nac_utc_offset"],
        )
        resultado["cusps_natales"] = cusps
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/resona", methods=["POST"])
def api_resona():
    """RSN (Resona) — refinamiento anual de la Proluna, basado en las casas
    de la Revolución Solar vigente en la fecha objetivo."""
    data = request.get_json(force=True)
    required = ["nac_year", "nac_month", "nac_day", "nac_hour", "nac_minute", "nac_utc_offset",
                "year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = calcular_resona(
            data["nac_year"], data["nac_month"], data["nac_day"],
            data["nac_hour"], data["nac_minute"], data["nac_utc_offset"],
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/reluna", methods=["POST"])
def api_reluna():
    """RLN (Reluna) — refinamiento mensual de la Proluna, basado en las
    casas de la Revolución Lunar vigente en la fecha objetivo."""
    data = request.get_json(force=True)
    required = ["nac_year", "nac_month", "nac_day", "nac_hour", "nac_minute", "nac_utc_offset",
                "year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = calcular_reluna(
            data["nac_year"], data["nac_month"], data["nac_day"],
            data["nac_hour"], data["nac_minute"], data["nac_utc_offset"],
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/sinastria", methods=["POST"])
def api_sinastria():
    """Sinastría entre dos cartas natales completas: compara Sol, Luna,
    Ascendente, MC, Vértex, Ecuador Celeste y Rueda de la Fortuna de cada
    persona contra los de la otra (7x7 combinaciones), buscando aspectos
    mayores (orbe 1° Sol/Luna, 2° puntos angulares)."""
    data = request.get_json(force=True)
    required = ["persona_A", "persona_B"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for clave in ("persona_A", "persona_B"):
        for c in campos:
            if c not in data[clave]:
                return jsonify({"error": f"Falta el campo {clave}.{c}"}), 400
    try:
        pa, pb = data["persona_A"], data["persona_B"]
        cartaA = carta_natal_simple(pa["year"], pa["month"], pa["day"], pa["hour"], pa["minute"],
                                     pa["utc_offset"], pa["lat"], pa["lon"])
        cartaB = carta_natal_simple(pb["year"], pb["month"], pb["day"], pb["hour"], pb["minute"],
                                     pb["utc_offset"], pb["lat"], pb["lon"])
        nombreA = data.get("nombre_A", "A")
        nombreB = data.get("nombre_B", "B")
        coincidencias = comparar_sinastria(cartaA, cartaB, nombreA, nombreB)
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({
        "carta_A": cartaA, "carta_B": cartaB,
        "coincidencias": coincidencias,
        "total_coincidencias": len(coincidencias),
        "total_partiles": sum(1 for c in coincidencias if c["partil"]),
    })


@app.route("/api/sinastria_retornos", methods=["POST"])
def api_sinastria_retornos():
    """Sinastría Atemporal, tercera capa (caso Camilo/Rosario de Bonito):
    compara TODAS las Fechas Gemelas (retornos, base Plutón y Neptuno) de
    una persona contra la carta natal fija de la otra."""
    data = request.get_json(force=True)
    for r in ["natal", "retornos"]:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for clave in ("natal", "retornos"):
        for c in campos:
            if c not in data[clave]:
                return jsonify({"error": f"Falta el campo {clave}.{c}"}), 400
    anios_adelante = data.get("anios_adelante", 250)
    anios_atras = data.get("anios_atras", 250)
    cuerpo_base = data.get("cuerpo_base")  # None = probar Plutón y Neptuno
    try:
        n, rt = data["natal"], data["retornos"]
        carta_natal = carta_natal_simple(n["year"], n["month"], n["day"], n["hour"], n["minute"],
                                          n["utc_offset"], n["lat"], n["lon"])
        nombre_natal = data.get("nombre_natal", "Natal")
        nombre_retornos = data.get("nombre_retornos", "Retornos")

        coincidencias = []
        for cb in ([cuerpo_base] if cuerpo_base else ["PLUTON", "NEPTUNO"]):
            carta_muerta = calcular_fechas_gemelas(
                rt["year"], rt["month"], rt["day"], rt["hour"], rt["minute"], rt["utc_offset"],
                anios_adelante=anios_adelante, anios_atras=anios_atras,
                lat=rt["lat"], lon=rt["lon"], cuerpo_base=cb,
            )
            coincidencias += comparar_natal_vs_retornos(carta_natal, carta_muerta,
                                                          nombre_natal, f"{nombre_retornos} ({cb.capitalize()})")
        coincidencias.sort(key=lambda c: c["orbe"])
        coincidencias = coincidencias[:200]
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({
        "coincidencias": coincidencias,
        "total_coincidencias": len(coincidencias),
        "total_partiles": sum(1 for c in coincidencias if c["partil"]),
    })


@app.route("/api/mellizos", methods=["POST"])
def api_mellizos():
    """Etapa Mellizos: arma el 'radix en reposo' (Soles natales y de Fechas
    Gemelas) de los familiares de referencia (madre/padre/hijo), escanea las
    Fechas Gemelas del mellizo (hora aproximada) buscando qué Lunas caen
    cerca de esas referencias, y afina por bisección la hora de nacimiento
    hasta lograr la conjunción partil exacta en el retorno identificado."""
    data = request.get_json(force=True)
    required = ["mellizo"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    mellizo = data["mellizo"]
    for r in ["year", "month", "day", "hour_aprox", "minute_aprox", "utc_offset"]:
        if r not in mellizo:
            return jsonify({"error": f"Falta el campo mellizo.{r}"}), 400

    personas = {
        "madre": data.get("madre"),
        "padre": data.get("padre"),
        "hijo": data.get("hijo"),
    }
    cuerpo_base = data.get("cuerpo_base")  # None = probar Plutón y Neptuno
    try:
        resultado = analizar_mellizo(
            mellizo, personas,
            cuerpo_base=cuerpo_base,
            anios_adelante=data.get("anios_adelante", 250),
            anios_atras=data.get("anios_atras", 250),
            orbe_escaneo=data.get("orbe_escaneo", 0.5),
            ventana_horas=data.get("ventana_horas", 1.5),
            top=data.get("top", 8),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/progresiones", methods=["POST"])
def api_progresiones():
    """Progresiones Secundarias (1 día = 1 año): calcula la carta progresada
    de una persona para una fecha objetivo (Sol, Luna, Ascendente, MC,
    Vértex, Ecuador Celeste, Rueda de la Fortuna progresados) y sus aspectos
    contra la carta natal fija — usada por Bonito como triangulación en
    Sinastría y como técnica de pronóstico independiente."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon",
                "year_obj", "month_obj", "day_obj"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        carta_natal = carta_natal_simple(data["year"], data["month"], data["day"],
                                          data["hour"], data["minute"], data["utc_offset"],
                                          data["lat"], data["lon"])
        progresada = progresiones_secundarias(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
            data["year_obj"], data["month_obj"], data["day_obj"],
            hour_obj=data.get("hour_obj", 12), minute_obj=data.get("minute_obj", 0),
            utc_offset_obj=data.get("utc_offset_obj"),
        )
        carta_progresada = {k: v for k, v in progresada.items()
                             if k in ("sol", "luna", "ascendente", "mc", "vertex",
                                      "ecuador_celeste", "rueda_de_la_fortuna")}
        coincidencias = comparar_progresiones_vs_natal(carta_natal, carta_progresada,
                                                         data.get("nombre_natal", "Natal"),
                                                         data.get("nombre_progresado", "Progresado"))
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({
        "edad_anios": progresada["edad_anios"],
        "fecha_objetivo": progresada["fecha_objetivo"],
        "carta_natal": carta_natal,
        "carta_progresada": carta_progresada,
        "coincidencias": coincidencias,
        "total_coincidencias": len(coincidencias),
        "total_partiles": sum(1 for c in coincidencias if c["partil"]),
    })


@app.route("/api/arco_solar", methods=["POST"])
def api_arco_solar():
    """Arco Solar / Arco de Jonás — carta dirigida para una fecha puntual:
    dirige todos los puntos natales por el Arco Solar (lo que avanzó el Sol
    progresado desde el nacimiento) y compara la carta dirigida contra la
    natal fija."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon",
                "year_obj", "month_obj", "day_obj"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = arco_solar_dirigido(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
            data["year_obj"], data["month_obj"], data["day_obj"],
            hour_obj=data.get("hour_obj", 12), minute_obj=data.get("minute_obj", 0),
            utc_offset_obj=data.get("utc_offset_obj"),
        )
        nombre_natal = data.get("nombre_natal", "Natal")
        nombre_dirigido = data.get("nombre_dirigido", "Dirigido")
        coincidencias = comparar_sinastria(resultado["carta_natal"], resultado["carta_dirigida"],
                                            nombre_natal, nombre_dirigido)
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({
        "arco_grados": resultado["arco_grados"],
        "meses_equivalentes": resultado["meses_equivalentes"],
        "fecha_objetivo": resultado["fecha_objetivo"],
        "carta_natal": resultado["carta_natal"],
        "carta_dirigida": resultado["carta_dirigida"],
        "coincidencias": coincidencias,
        "total_coincidencias": len(coincidencias),
        "total_partiles": sum(1 for c in coincidencias if c["partil"]),
    })


@app.route("/api/arco_solar_diagrama", methods=["POST"])
def api_arco_solar_diagrama():
    """Arco Solar / Arco de Jonás — 'diagrama de flujo': lista cronológica de
    las fechas futuras en que el Sol dirigido por Arco Solar hace aspecto
    mayor con cada punto natal (Luna, Ascendente, MC, Vértex, Ecuador
    Celeste, Rueda de la Fortuna)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        eventos = diagrama_flujo_arco_solar(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
            anios_adelante=data.get("anios_adelante", 100),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"eventos": eventos, "total_eventos": len(eventos)})


@app.route("/api/estrellas_natal", methods=["POST"])
def api_estrellas_natal():
    """Estrellas Fijas: busca conjunciones (orbe 1°) entre los puntos de la
    carta natal y el catálogo de estrellas fijas de referencia (posiciones
    reales con precesión, vía Swiss Ephemeris)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd = jd_from_local(data["year"], data["month"], data["day"],
                            data["hour"], data["minute"], data["utc_offset"])
        carta_natal = carta_natal_simple(data["year"], data["month"], data["day"],
                                          data["hour"], data["minute"], data["utc_offset"],
                                          data["lat"], data["lon"])
        orbe = data.get("orbe", 1.0)
        conjunciones = estrellas_en_carta(carta_natal, jd, orbe=orbe)
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"carta_natal": carta_natal, "conjunciones": conjunciones,
                     "catalogo": CATALOGO_ESTRELLAS})


@app.route("/api/estrellas_diagrama", methods=["POST"])
def api_estrellas_diagrama():
    """Estrellas Fijas + Progresiones: fechas futuras en que el Sol dirigido
    por Arco Solar llega a conjunción con cada estrella fija del catálogo."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        eventos = diagrama_estrellas_progresadas(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
            anios_adelante=data.get("anios_adelante", 100),
            orbe=data.get("orbe", 1.0),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"eventos": eventos, "total_eventos": len(eventos)})


@app.route("/api/retornos_marte", methods=["POST"])
def api_retornos_marte():
    """Retornos de Marte — pronóstico de salud de Bonito: revisa los retornos
    pasados (justifican problemas de salud) y futuros (posibilidad de
    relocación) de Marte a su posición natal, con la carta completa de cada
    retorno y sus aspectos contra la natal (especialmente al Ascendente y al
    Ecuador Celeste, indicadores de vitalidad)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        carta_natal = carta_natal_simple(data["year"], data["month"], data["day"],
                                          data["hour"], data["minute"], data["utc_offset"],
                                          data["lat"], data["lon"])
        retornos = retornos_marte(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data.get("lat_calculo", data["lat"]), data.get("lon_calculo", data["lon"]),
            anios_atras=data.get("anios_atras", 10), anios_adelante=data.get("anios_adelante", 10),
            sideral=data.get("sideral", False),
        )
        for r in retornos:
            r["coincidencias"] = comparar_retorno_marte_vs_natal(r, carta_natal, data.get("nombre_natal", "Natal"))
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"carta_natal": carta_natal, "retornos": retornos, "total_retornos": len(retornos)})


def _api_retorno_planeta(retornos_fn, comparar_fn, periodo_anios_total,
                          anios_atras_default, anios_adelante_default):
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        carta_natal = carta_natal_simple(data["year"], data["month"], data["day"],
                                          data["hour"], data["minute"], data["utc_offset"],
                                          data["lat"], data["lon"])
        retornos = retornos_fn(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data.get("lat_calculo", data["lat"]), data.get("lon_calculo", data["lon"]),
            anios_atras=data.get("anios_atras", anios_atras_default),
            anios_adelante=data.get("anios_adelante", anios_adelante_default),
            sideral=data.get("sideral", False),
        )
        for r in retornos:
            r["coincidencias"] = comparar_fn(r, carta_natal, data.get("nombre_natal", "Natal"))
            if data.get("con_casa_periodo"):
                r["casa_periodo"] = lectura_casa_periodo(r, carta_natal, periodo_anios_total, data.get("nombre_natal", "Natal"))
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"carta_natal": carta_natal, "retornos": retornos, "total_retornos": len(retornos)})


@app.route("/api/retornos_jupiter", methods=["POST"])
def api_retornos_jupiter():
    """Retornos de Júpiter — Bonito: 'vamos a hacer el retorno de Júpiter a
    ver por dónde anda... estos son tres retornos de Júpiter que van a estar
    influenciando durante 12 años'. Carta completa de cada retorno, aspectos
    contra la natal, y opcionalmente la técnica secundaria de 'cada casa es
    un año' (con_casa_periodo=true) — ver retornos_jupiter_saturno.py para
    la reconstrucción honesta de los supuestos que esa técnica requirió."""
    return _api_retorno_planeta(retornos_jupiter, comparar_retorno_jupiter_vs_natal,
                                 PERIODO_ANIOS_JUPITER, 60, 60)


@app.route("/api/retornos_saturno", methods=["POST"])
def api_retornos_saturno():
    """Retornos de Saturno — Bonito: 'Saturno nos influye cada 28 años...
    para mi edad, cuando llegamos cerca de los 60, ahí tenemos un retorno de
    Saturno que nos va a influenciar el resto que queda por vivir'. Carta
    completa de cada retorno, aspectos contra la natal, y opcionalmente la
    técnica secundaria de 'cada cúspide ~2 años y medio' (con_casa_periodo=true)."""
    return _api_retorno_planeta(retornos_saturno, comparar_retorno_saturno_vs_natal,
                                 PERIODO_ANIOS_SATURNO, 90, 90)


@app.route("/api/contacto", methods=["POST"])
def api_contacto():
    """Técnica de Contacto (distinta de la Sinastría): progresa el Sol y la
    Luna de persona_a a la fecha de contacto pedida y los compara contra
    TODOS los Soles de Fechas Gemelas (natal + retornos base Plutón/Neptuno)
    de persona_b — el criterio de Bonito para justificar un encuentro,
    validar una rectificación ajena, o pronosticar un posible reencuentro."""
    data = request.get_json(force=True)
    for r in ["persona_a", "persona_b", "fecha_contacto"]:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos_persona = ["year", "month", "day", "hour", "minute", "utc_offset"]
    for clave in ("persona_a", "persona_b"):
        for c in campos_persona:
            if c not in data[clave]:
                return jsonify({"error": f"Falta el campo {clave}.{c}"}), 400
    if "year" not in data["fecha_contacto"]:
        return jsonify({"error": "Falta el campo fecha_contacto.year (y month/day)"}), 400
    try:
        resultado = contacto_puntual(
            data["persona_a"], data["persona_b"], data["fecha_contacto"],
            orbe=data.get("orbe", 1.0),
            anios_adelante=data.get("anios_adelante", 250), anios_atras=data.get("anios_atras", 250),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/contacto_diagrama", methods=["POST"])
def api_contacto_diagrama():
    """Ventanas de acercamiento futuras: fechas (desde hoy) en que el Sol o
    la Luna progresados de persona_a hacen aspecto mayor con algún Sol de
    Fechas Gemelas de persona_b."""
    data = request.get_json(force=True)
    for r in ["persona_a", "persona_b"]:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos_persona = ["year", "month", "day", "hour", "minute", "utc_offset"]
    for clave in ("persona_a", "persona_b"):
        for c in campos_persona:
            if c not in data[clave]:
                return jsonify({"error": f"Falta el campo {clave}.{c}"}), 400
    try:
        eventos = diagrama_contacto(
            data["persona_a"], data["persona_b"],
            utc_offset_salida=data.get("utc_offset_salida"),
            anios_adelante=data.get("anios_adelante", 5),
            orbe=data.get("orbe", 1.0),
            anios_referencias=data.get("anios_referencias", 250),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"eventos": eventos, "total_eventos": len(eventos)})


@app.route("/api/cotidian_cardinal", methods=["POST"])
def api_cotidian_cardinal():
    """Técnica de Contacto usando Cotidian Cardinal 1 (dirige Ascendente/MC/
    Vértex/Ecuador Celeste de persona_a en vez de Sol/Luna). Requiere
    lat/lon de persona_a."""
    data = request.get_json(force=True)
    for r in ["persona_a", "persona_b", "fecha_contacto"]:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos_persona = ["year", "month", "day", "hour", "minute", "utc_offset"]
    for c in campos_persona:
        if c not in data["persona_a"]:
            return jsonify({"error": f"Falta el campo persona_a.{c}"}), 400
    for c in ("lat", "lon"):
        if c not in data["persona_a"]:
            return jsonify({"error": f"Falta el campo persona_a.{c} (Cotidian Cardinal 1 necesita el lugar de nacimiento)"}), 400
    for c in campos_persona:
        if c not in data["persona_b"]:
            return jsonify({"error": f"Falta el campo persona_b.{c}"}), 400
    if "year" not in data["fecha_contacto"]:
        return jsonify({"error": "Falta el campo fecha_contacto.year (y month/day)"}), 400
    try:
        resultado = contacto_cotidian_cardinal(
            data["persona_a"], data["persona_b"], data["fecha_contacto"],
            orbe=data.get("orbe", 1.0),
            anios_adelante=data.get("anios_adelante", 250), anios_atras=data.get("anios_atras", 250),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/cotidian_cardinal_diagrama", methods=["POST"])
def api_cotidian_cardinal_diagrama():
    data = request.get_json(force=True)
    for r in ["persona_a", "persona_b"]:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos_persona = ["year", "month", "day", "hour", "minute", "utc_offset"]
    for c in campos_persona:
        if c not in data["persona_a"]:
            return jsonify({"error": f"Falta el campo persona_a.{c}"}), 400
    for c in ("lat", "lon"):
        if c not in data["persona_a"]:
            return jsonify({"error": f"Falta el campo persona_a.{c} (Cotidian Cardinal 1 necesita el lugar de nacimiento)"}), 400
    for c in campos_persona:
        if c not in data["persona_b"]:
            return jsonify({"error": f"Falta el campo persona_b.{c}"}), 400
    try:
        eventos = diagrama_cotidian_cardinal(
            data["persona_a"], data["persona_b"],
            utc_offset_salida=data.get("utc_offset_salida"),
            anios_adelante=data.get("anios_adelante", 5),
            orbe=data.get("orbe", 1.0),
            anios_referencias=data.get("anios_referencias", 250),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify({"eventos": eventos, "total_eventos": len(eventos)})


@app.route("/api/cartas_analogas", methods=["POST"])
def api_cartas_analogas():
    """Cartas Análogas: cadena de fechas donde el Sol, alternando entre
    Sideral y Trópico, vuelve a caer en la misma posición numérica que la
    carta anterior de la cadena (empezando por el Sol trópico natal). Cada
    fecha es, según Bonito, una carta que la persona puede considerar propia.
    lat/lon son opcionales: si se aportan (el lugar de nacimiento), se
    calculan también Ascendente/MC/Vértex/Ecuador Celeste de cada carta."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = cartas_analogas(
            data,
            pasos_adelante=data.get("pasos_adelante", 12),
            pasos_atras=data.get("pasos_atras", 12),
            utc_offset_salida=data.get("utc_offset_salida"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/horaria", methods=["POST"])
def api_horaria():
    """Astrología Horaria de Bonito: carta del momento exacto de la
    pregunta (Medio Cielo=persona, Ascendente=pregunta, Ecuador
    Celeste/Vértex=alternos, Rueda de la Fortuna=asuntos patrimoniales),
    en trópico y sideral, con los tránsitos actuales de los planetas
    lentos y la fecha real (pasada o futura) en que cada aspecto se
    vuelve exacto."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = carta_horaria(
            data,
            orbe_vinculo=data.get("orbe_vinculo", 3.0),
            orbe_transito=data.get("orbe_transito", 3.0),
            anios_busqueda=data.get("anios_busqueda", 3),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/omega", methods=["POST"])
def api_omega():
    """Programa Omega de Bonito: arma el banco de grados (Sol/Luna de las
    Fechas Gemelas de Retornos de Plutón) de una persona/equipo/evento de
    referencia y escanea una ventana horaria real corta (un partido, una
    sesión) buscando conjunciones partiles de la Luna (o el Sol) en
    tránsito real contra ese banco."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset",
                "ventana_year", "ventana_month", "ventana_day",
                "ventana_hora_ini", "ventana_min_ini", "ventana_hora_fin", "ventana_min_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_ini"], data["ventana_min_ini"], data["utc_offset"])
        jd_fin = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_fin"], data["ventana_min_fin"], data["utc_offset"])
        if jd_fin <= jd_ini:
            jd_fin += 1  # ventana cruza medianoche
        resultado = escanear_omega(
            data, jd_ini, jd_fin, data["utc_offset"],
            anios_atras=data.get("anios_atras", 80), anios_adelante=data.get("anios_adelante", 80),
            cuerpo_transito=data.get("cuerpo_transito", "LUNA"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/omega_comparar", methods=["POST"])
def api_omega_comparar():
    """Programa Omega, versión comparativa: corre el escaneo para dos
    entidades (por ejemplo, dos equipos) sobre la misma ventana horaria y
    devuelve cuál acumula más conjunciones — el criterio de Bonito para
    "el ganador"."""
    data = request.get_json(force=True)
    required = ["a", "b", "nombre_a", "nombre_b", "utc_offset",
                "ventana_year", "ventana_month", "ventana_day",
                "ventana_hora_ini", "ventana_min_ini", "ventana_hora_fin", "ventana_min_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_ini"], data["ventana_min_ini"], data["utc_offset"])
        jd_fin = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_fin"], data["ventana_min_fin"], data["utc_offset"])
        if jd_fin <= jd_ini:
            jd_fin += 1
        resultado = comparar_omega(
            data["a"], data["nombre_a"], data["b"], data["nombre_b"], jd_ini, jd_fin, data["utc_offset"],
            anios_atras=data.get("anios_atras", 80), anios_adelante=data.get("anios_adelante", 80),
            cuerpo_transito=data.get("cuerpo_transito", "LUNA"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/imantacion", methods=["POST"])
def api_imantacion():
    """Imantación de personajes/instituciones de Bonito: arma el banco DOBLE
    (Sol/Luna de Fechas Gemelas base Plutón Y base Neptuno) de una persona,
    equipo o institución de referencia, y escanea una ventana horaria real
    (una entrevista, un partido, una gestión) buscando los 'horarios
    imantados' — momentos de conjunción partil del cuerpo en tránsito
    (Luna por defecto) contra ese banco."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset",
                "ventana_year", "ventana_month", "ventana_day",
                "ventana_hora_ini", "ventana_min_ini", "ventana_hora_fin", "ventana_min_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_ini"], data["ventana_min_ini"], data["utc_offset"])
        jd_fin = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_fin"], data["ventana_min_fin"], data["utc_offset"])
        if jd_fin <= jd_ini:
            jd_fin += 1  # ventana cruza medianoche
        bases = data.get("bases", ["PLUTON", "NEPTUNO"])
        resultado = escanear_imantacion(
            data, jd_ini, jd_fin, data["utc_offset"],
            anios_atras=data.get("anios_atras", 150), anios_adelante=data.get("anios_adelante", 150),
            cuerpo_transito=data.get("cuerpo_transito", "LUNA"),
            bases=bases,
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/electiva", methods=["POST"])
def api_electiva():
    """Electiva de riesgo de Bonito: escanea una ventana horaria corta
    buscando aspectos exactos (sextil/trígono=bueno; semicuadratura/
    cuadratura/sesquicuadratura=malo) entre el Sol real en tránsito (por
    defecto) y la posición real y dinámica de un planeta lento de
    referencia (Plutón geo/helio por defecto) — para decidir si un
    momento es favorable o desfavorable para actuar."""
    data = request.get_json(force=True)
    required = ["ventana_year", "ventana_month", "ventana_day",
                "ventana_hora_ini", "ventana_min_ini", "ventana_hora_fin", "ventana_min_fin",
                "utc_offset"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_ini"], data["ventana_min_ini"], data["utc_offset"])
        jd_fin = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_fin"], data["ventana_min_fin"], data["utc_offset"])
        if jd_fin <= jd_ini:
            jd_fin += 1
        resultado = escanear_electiva(
            jd_ini, jd_fin, data["utc_offset"],
            cuerpo_banco=data.get("cuerpo_banco", "PLUTON"),
            helio_banco=data.get("helio_banco", False),
            sideral_banco=data.get("sideral_banco", False),
            cuerpo_transito=data.get("cuerpo_transito", "SOL"),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/manchas_solares", methods=["POST"])
def api_manchas_solares():
    """Técnica de Manchas Solares de Bonito: arma el banco de todos los
    Soles de las Fechas Gemelas de una carta de referencia y escanea una
    ventana horaria buscando oposiciones exactas del Sol real contra ese
    banco — el único aspecto que Bonito usa para detectar 'manchas
    solares' (riesgo de interferencia en comunicaciones)."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset",
                "ventana_year", "ventana_month", "ventana_day",
                "ventana_hora_ini", "ventana_min_ini", "ventana_hora_fin", "ventana_min_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_ini"], data["ventana_min_ini"], data["utc_offset"])
        jd_fin = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_fin"], data["ventana_min_fin"], data["utc_offset"])
        if jd_fin <= jd_ini:
            jd_fin += 1
        resultado = escanear_manchas_solares(
            data, jd_ini, jd_fin, data["utc_offset"],
            anios_atras=data.get("anios_atras", 150), anios_adelante=data.get("anios_adelante", 150),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/discriminacion", methods=["POST"])
def api_discriminacion():
    """Discriminación de cartas casi idénticas por orbe (técnica de Bonito
    para mellizas/hermanas con horarios de nacimiento muy próximos): arma
    la carta completa de cada retorno de Fechas Gemelas de las dos
    personas, empareja por índice, y en cada posición dice a cuál de las
    dos le corresponde cada aspecto compartido según cuál tiene el orbe
    más cerrado."""
    data = request.get_json(force=True)
    for r in ["persona_a", "persona_b"]:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    campos = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for clave in ("persona_a", "persona_b"):
        for c in campos:
            if c not in data[clave]:
                return jsonify({"error": f"Falta el campo {clave}.{c}"}), 400
    try:
        resultado = discriminar_por_orbe(
            data["persona_a"], data["persona_b"],
            nombreA=data.get("nombre_a", "A"), nombreB=data.get("nombre_b", "B"),
            variante=data.get("variante", "geo_tropico"),
            anios_atras=data.get("anios_atras", 250), anios_adelante=data.get("anios_adelante", 250),
            orbe_max=data.get("orbe_max", 1.0),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/pronostico_natal", methods=["POST"])
def api_pronostico_natal():
    """Antivértex y pronóstico de nacimientos/mudanza — Bonito (caso
    Marisa/Yahira): progresiones secundarias extendidas (directa y
    conversa) de Sol, Luna, Mercurio, Venus, Marte, Nodo, Luna Negra,
    Saturno, Urano, Plutón, Ascendente, MC, Vértex y Antivértex, comparadas
    contra la carta natal (incluida la cúspide de Casa IV) dentro de 1° de
    orbe. Variante 'ascensional=True': usa la Carta Ascensional (reconstrucción
    del horóscopo ascensional estándar, no transcripción letra por letra de
    Bonito). Ver pronostico_natal.py para la reconstrucción honesta completa."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = escanear_pronostico(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"],
            anios_desde=data.get("anios_desde", 0), anios_hasta=data.get("anios_hasta", 45),
            paso_anios=data.get("paso_anios", 1.0),
            helio=data.get("helio", False), sideral=data.get("sideral", False),
            ascensional=data.get("ascensional", False),
            incluir_conversa=data.get("incluir_conversa", True),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/interpretar", methods=["POST"])
def api_interpretar():
    """Devuelve la lectura para un aspecto entre dos puntos: primero un
    marcador específico documentado de Hugo si existe (ver diccionario.py);
    si no, y hay ANTHROPIC_API_KEY configurada, una lectura generada por IA
    siguiendo el estilo/método de Bonito (ver interpretacion.py); si
    tampoco hay IA disponible, la lectura general de categoría de cada
    punto. El campo 'fuente' de la respuesta dice siempre cuál de las tres
    se usó.

    'mismo_individuo' (opcional, default true): si los dos puntos vienen de
    la carta de una sola persona (Progresiones, Retornos, Antivértex, o una
    fila de Comparar Fechas Gemelas donde nombre_A == nombre_B) o de dos
    personas distintas (Sinastría, Contacto, Discriminación, Mellizos, o
    una fila de Comparar Fechas Gemelas entre dos personas con nombres
    distintos). Los marcadores fijos de Hugo están documentados siempre
    para una sola carta, así que cuando mismo_individuo=false la app los
    salta a propósito y arma una lectura de vínculo (sinastría) en vez de
    aplicar, fuera de contexto, una lectura de personalidad individual a
    una comparación entre dos personas. 'nombre_a'/'nombre_b' (opcionales)
    se usan para nombrar a cada persona en esa lectura de vínculo."""
    data = request.get_json(force=True)
    required = ["punto_a", "punto_b", "aspecto", "orbe"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    resultado = interpretar_aspecto(
        data["punto_a"], data["punto_b"], data["aspecto"], data["orbe"],
        tecnica=data.get("tecnica", "Fechas Gemelas (comparación de cartas)"),
        mismo_individuo=data.get("mismo_individuo", True),
        nombre_a=data.get("nombre_a"), nombre_b=data.get("nombre_b"),
    )
    return jsonify(resultado)


@app.route("/api/interpretar_evento", methods=["POST"])
def api_interpretar_evento():
    """Lectura para un evento que NO se reduce a un aspecto entre dos puntos
    natales (Programa Omega, Imantación, Electiva de riesgo, Manchas
    Solares, Lotería, Bursátil, Casino, Horaria, Mellizos, Proluna, etc.):
    solo hay generación por IA siguiendo el método de Bonito (no existen
    marcadores fijos de Hugo para cruces de tránsito contra un banco de
    grados). Si no hay ANTHROPIC_API_KEY configurada, devuelve
    disponible=false y el frontend muestra el evento sin lectura adicional
    (la tabla ya es legible por sí sola)."""
    data = request.get_json(force=True)
    required = ["tecnica", "descripcion"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    resultado = interpretar_evento_libre(
        data["tecnica"], data["descripcion"], contexto_extra=data.get("contexto_extra", ""))
    if resultado is None:
        return jsonify({"disponible": False,
                         "texto": "No hay lectura de IA disponible para este evento (falta configurar ANTHROPIC_API_KEY)."})
    resultado["disponible"] = True
    return jsonify(resultado)


@app.route("/api/eventos_vida", methods=["POST"])
def api_eventos_vida():
    """Reglas de Eventos de Vida de Bonito (ver eventos_vida.py): chequeo de
    aspectos fijos (no un escaneo temporal) sobre la carta Natal y,
    opcionalmente, la Revolución Solar de un año dado — noviazgo,
    nacimiento de hijo, cirugía, divorcio, finanzas, problema judicial,
    mudanzas, envidia/pérdidas, viudez, embarazo, inversión inmobiliaria."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        carta_natal = carta_natal_simple(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
            data["lat"], data["lon"])
        jd_natal = jd_from_local(data["year"], data["month"], data["day"], data["hour"], data["minute"],
                                  data["utc_offset"])
        jd_revo = None
        rs = None
        anio_revo = data.get("anio_revolucion")
        if anio_revo:
            lat_revo = data.get("lat_revolucion", data["lat"])
            lon_revo = data.get("lon_revolucion", data["lon"])
            utc_revo = data.get("utc_offset_revolucion", data["utc_offset"])
            rs = revolucion_solar(
                data["year"], data["month"], data["day"], data["hour"], data["minute"], data["utc_offset"],
                int(anio_revo), lat_revo, lon_revo, utc_revo,
                lat_natal=data["lat"], lon_natal=data["lon"])
            jd_revo = jd_from_local(rs["fecha_local"]["year"], rs["fecha_local"]["month"], rs["fecha_local"]["day"],
                                     rs["fecha_local"]["hour"], rs["fecha_local"]["minute"], utc_revo)
        resultado = evaluar_eventos_vida(carta_natal, jd_natal, jd_revo=jd_revo, anio_revo=anio_revo,
                                          carta_revo_dict=rs)
        resultado["revolucion_solar"] = rs
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/loteria_semanal", methods=["POST"])
def api_loteria_semanal():
    """Programa Omega, variante lotería semanal (ver loteria.py): para cada
    número cargado (con su fecha histórica de referencia) arma el banco de
    Fechas Gemelas y chequea el arco real de Plutón Heliocéntrico Trópico
    de la semana pedida — trígono/sextil = favorecido, cuadratura = negado.
    NOTA: la base real de 900 números de Bonito no está disponible; se
    escanea la lista de números que Celina cargue."""
    data = request.get_json(force=True)
    required = ["numeros", "ventana_year", "ventana_month", "ventana_day"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    numeros = data["numeros"]
    if not isinstance(numeros, list) or not numeros:
        return jsonify({"error": "'numeros' debe ser una lista no vacía de {numero, year, month, day}."}), 400
    try:
        utc_offset = data.get("utc_offset", -3)
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"], 0, 0, utc_offset)
        jd_fin = jd_ini + 7
        resultado = escanear_loteria_semanal(
            numeros, jd_ini, jd_fin,
            anios_atras=data.get("anios_atras", 60), anios_adelante=data.get("anios_adelante", 60),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/loteria_navidad", methods=["POST"])
def api_loteria_navidad():
    """Programa Omega, variante Lotería de Navidad de España (ver
    loteria.py): banco de Soles de Fechas Gemelas del día del sorteo,
    escaneado contra el Sol real en tránsito dentro de la ventana de
    compra pedida, buscando conjunción partil ('momento gemelo')."""
    data = request.get_json(force=True)
    required = ["sorteo_year", "sorteo_month", "sorteo_day", "sorteo_hour", "sorteo_minute", "sorteo_utc_offset",
                "ventana_year_ini", "ventana_month_ini", "ventana_day_ini",
                "ventana_year_fin", "ventana_month_fin", "ventana_day_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        utc_salida = data.get("utc_offset_salida", data["sorteo_utc_offset"])
        jd_ini = jd_from_local(data["ventana_year_ini"], data["ventana_month_ini"], data["ventana_day_ini"],
                                0, 0, utc_salida)
        jd_fin = jd_from_local(data["ventana_year_fin"], data["ventana_month_fin"], data["ventana_day_fin"],
                                23, 59, utc_salida)
        resultado = loteria_navidad(
            data["sorteo_year"], data["sorteo_month"], data["sorteo_day"],
            data["sorteo_hour"], data["sorteo_minute"], data["sorteo_utc_offset"],
            jd_ini, jd_fin, utc_salida,
            anios_atras=data.get("anios_atras", 60), anios_adelante=data.get("anios_adelante", 60),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/bursatil", methods=["POST"])
def api_bursatil():
    """Programa Omega, variante bursátil (ver bursatil.py): aspectos reales
    (45/60/90/120/135°) entre los 4 planetas lentos (Saturno, Urano,
    Neptuno, Plutón) Heliocéntricos, Trópicos o Sidérales, dentro de un
    rango de fechas — la secuencia cronológica de estos instantes es la
    que Bonito correlaciona con los giros de tendencia del mercado."""
    data = request.get_json(force=True)
    required = ["ventana_year_ini", "ventana_month_ini", "ventana_day_ini",
                "ventana_year_fin", "ventana_month_fin", "ventana_day_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        utc_offset = data.get("utc_offset", -3)
        jd_ini = jd_from_local(data["ventana_year_ini"], data["ventana_month_ini"], data["ventana_day_ini"],
                                0, 0, utc_offset)
        jd_fin = jd_from_local(data["ventana_year_fin"], data["ventana_month_fin"], data["ventana_day_fin"],
                                23, 59, utc_offset)
        resultado = escanear_bursatil(jd_ini, jd_fin, utc_offset, sideral=data.get("sideral", False),
                                       paso_dias=data.get("paso_dias", 1.0))
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/rectificar_proluna", methods=["POST"])
def api_rectificar_proluna():
    """Rectificación de hora natal con Proluna directa/conversa (ver
    proluna.rectificar_hora_proluna): prueba la hora de nacimiento minuto
    a minuto alrededor de la hora aproximada, buscando la que deja la
    Proluna directa y conversa en aspecto exacto (múltiplo de 15°) en el
    momento de un evento conocido."""
    data = request.get_json(force=True)
    required = ["nac_year", "nac_month", "nac_day", "nac_hour", "nac_minute", "nac_utc_offset", "lat", "lon",
                "evento_year", "evento_month", "evento_day"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        resultado = rectificar_hora_proluna(
            data["nac_year"], data["nac_month"], data["nac_day"], data["nac_hour"], data["nac_minute"],
            data["nac_utc_offset"], data["lat"], data["lon"],
            data["evento_year"], data["evento_month"], data["evento_day"],
            data.get("evento_hour", 12), data.get("evento_minute", 0),
            data.get("evento_utc_offset", data["nac_utc_offset"]),
            rango_minutos=data.get("rango_minutos", 90), paso_minutos=data.get("paso_minutos", 1),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/api/casino", methods=["POST"])
def api_casino():
    """Programa Omega, variante 'casino' (ver casino.py): dentro de una
    ventana horaria corta, escanea Venus/Júpiter/Saturno/Urano (Geo y
    Helio) en sextil/trígono, y la Luna en conjunción/sextil/trígono/
    oposición, contra el banco de Sol/Ascendente/MC/Rueda de la Fortuna
    de Fechas Gemelas de la persona — excluye Mercurio y Marte a
    propósito."""
    data = request.get_json(force=True)
    required = ["year", "month", "day", "hour", "minute", "utc_offset", "lat", "lon",
                "ventana_year", "ventana_month", "ventana_day",
                "ventana_hora_ini", "ventana_min_ini", "ventana_hora_fin", "ventana_min_fin"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"Falta el campo {r}"}), 400
    try:
        persona = {
            "year": data["year"], "month": data["month"], "day": data["day"],
            "hour": data["hour"], "minute": data["minute"], "utc_offset": data["utc_offset"],
            "lat": data["lat"], "lon": data["lon"],
        }
        utc_salida = data.get("utc_offset_salida", data["utc_offset"])
        jd_ini = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_ini"], data["ventana_min_ini"], utc_salida)
        jd_fin = jd_from_local(data["ventana_year"], data["ventana_month"], data["ventana_day"],
                                data["ventana_hora_fin"], data["ventana_min_fin"], utc_salida)
        if jd_fin <= jd_ini:
            jd_fin += 1.0  # ventana cruza medianoche
        resultado = escanear_casino(
            persona, jd_ini, jd_fin, utc_salida,
            anios_atras=data.get("anios_atras", 60), anios_adelante=data.get("anios_adelante", 60),
        )
    except Exception as e:
        return jsonify({"error": f"No se pudo calcular: {e}"}), 500
    return jsonify(resultado)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
