# -*- coding: utf-8 -*-
"""
Técnica de Contacto (distinta de la Sinastría, según Bonito: "esto es
progresión y aplicable... a un contacto"). Se usa Winstar 1.5 y progresiones
secundarias (1 día = 1 año): se dirige el Sol y la Luna progresados de una
persona a una fecha puntual (el momento de contacto, o cualquier fecha a
investigar) y se los compara contra TODOS los Soles de Fechas Gemelas
(natal + retornos, base Plutón y base Neptuno) de la otra persona — la
misma "batería de referencias" que ya arma mellizos.py para la Etapa
Mellizos.

Casos de uso documentados por Bonito:
  - Justificar un encuentro/contacto puntual entre dos personas (caso
    real: Marisa y Bonito, contacto 1/6/2011 18hs Barcelona).
  - Pronosticar "ventanas de acercamiento" futuras entre alguien que se fue
    y quien fue abandonado (aplicando la progresión sobre quien se fue,
    comparando contra los soles de quien espera).
  - Corroborar un horario de nacimiento rectificado de un tercero: si uno
    se ocupa de investigar la carta de alguien, debe encontrarse un Sol o
    Luna propios progresados en contacto con los soles de esa persona.

Nota: Bonito menciona una variante alternativa llamada "Cotidian Cardinal 1"
("una especie de revolución de progresión secundaria vinculada con las
posiciones cardinales") como igualmente válida por experiencia — no se
reconstruye acá por no contar con una definición operativa clara en el
material disponible; se documenta como técnica pendiente de mayor detalle.
"""
from astro import (
    jd_from_local, jd_to_local, sol_luna_geo_tropical, norm360, _diff_angular,
    _aspecto, ORBE_PLANETA, cotidian_cardinal_1, _resolver_fecha_cotidian_cardinal,
)
from mellizos import _referencias_de_persona
from puntos import _punto


def _progresar(jd_natal, jd_objetivo):
    """Sol y Luna progresados (1 día = 1 año) de una persona para una fecha
    objetivo."""
    edad_anios = (jd_objetivo - jd_natal) / 365.2425
    jd_progresado = jd_natal + edad_anios
    return sol_luna_geo_tropical(jd_progresado)


def contacto_puntual(persona_a, persona_b, fecha_contacto, orbe=ORBE_PLANETA,
                      anios_adelante=250, anios_atras=250):
    """Para una fecha de contacto puntual: progresa el Sol y la Luna de
    persona_a a esa fecha y los compara contra TODOS los Soles de Fechas
    Gemelas (natal + retornos base Plutón/Neptuno) de persona_b, buscando
    aspectos mayores — el "sí o sí" de Bonito para justificar un encuentro."""
    jd_natal_a = jd_from_local(persona_a["year"], persona_a["month"], persona_a["day"],
                                persona_a["hour"], persona_a["minute"], persona_a["utc_offset"])
    jd_contacto = jd_from_local(fecha_contacto["year"], fecha_contacto["month"], fecha_contacto["day"],
                                 fecha_contacto.get("hour", 12), fecha_contacto.get("minute", 0),
                                 fecha_contacto.get("utc_offset", persona_a["utc_offset"]))
    sol_prog_lon, luna_prog_lon = _progresar(jd_natal_a, jd_contacto)

    referencias = _referencias_de_persona("B", persona_b, anios_adelante, anios_atras)

    resultados = []
    for punto_nombre, punto_lon in (("Sol progresado", sol_prog_lon), ("Luna progresada", luna_prog_lon)):
        for ref in referencias:
            asp = _aspecto(punto_lon, ref["lon"], orbe)
            if asp:
                resultados.append({
                    "punto_A": punto_nombre,
                    "referencia_B": ref["etiqueta"],
                    "signo_B": ref["signo"], "grado_B": ref["grado"],
                    **asp,
                })
    resultados.sort(key=lambda r: r["orbe"])
    return {
        "fecha_contacto": jd_to_local(jd_contacto, fecha_contacto.get("utc_offset", persona_a["utc_offset"])),
        "sol_progresado_A": {"lon": round(sol_prog_lon, 5)},
        "luna_progresada_A": {"lon": round(luna_prog_lon, 5)},
        "total_referencias_B": len(referencias),
        "coincidencias": resultados,
    }


def _resolver_fecha_por_progresion(jd_natal, lon_objetivo, cuerpo_progresado, anios_max, jd_desde):
    """Bisección: encuentra la fecha en que el Sol o la Luna progresados de
    una persona (cuerpo_progresado = 'sol' o 'luna') pasan por lon_objetivo,
    dentro de una ventana [jd_desde, jd_desde + anios_max*365.2425]. Al ser
    progresiones (1 día = 1 año), el punto avanza siempre hacia adelante,
    así que se buscan cruces por cambio de signo en pasos finos."""
    jd_ini = jd_desde
    jd_fin = jd_desde + anios_max * 365.2425
    paso = 3.0  # días reales de paso (equivalen a ~3 años de progresión; suficiente para no saltear cruces)

    def lon_en(jd):
        sol_lon, luna_lon = _progresar(jd_natal, jd)
        return sol_lon if cuerpo_progresado == "sol" else luna_lon

    EPS = 1e-4  # grados; tolerancia para aceptar la raíz como cruce genuino (no antipodal)

    resultados = []
    jd = jd_ini
    prev = _diff_angular(lon_en(jd), lon_objetivo)
    while jd < jd_fin:
        jd_next = jd + paso
        curr = _diff_angular(lon_en(jd_next), lon_objetivo)
        if (prev > 0) != (curr > 0):
            lo, hi = jd, jd_next
            dlo = prev
            for _ in range(40):
                mid = (lo + hi) / 2
                dmid = _diff_angular(lon_en(mid), lon_objetivo)
                if (dmid > 0) == (dlo > 0):
                    lo, dlo = mid, dmid
                else:
                    hi = mid
            raiz = (lo + hi) / 2
            # _diff_angular envuelve en (-180,180] y también cambia de signo en
            # el antípoda del objetivo (objetivo+180), no solo en el objetivo
            # mismo. Se verifica que la raíz hallada realmente corresponda al
            # objetivo (diferencia angular ~0) y se descarta si en realidad
            # convergió al punto antipodal (diferencia angular ~180).
            if abs(_diff_angular(lon_en(raiz), lon_objetivo)) < EPS:
                resultados.append(raiz)
        prev, jd = curr, jd_next
    return resultados


def diagrama_contacto(persona_a, persona_b, utc_offset_salida=None, anios_adelante=5, orbe=ORBE_PLANETA,
                       anios_referencias=250):
    """'Ventanas de acercamiento' futuras (o pasadas, con anios_adelante
    negativo no soportado — usar jd_desde distinto si se necesita): fechas en
    que el Sol o la Luna progresados de persona_a llegan a conjunción,
    sextil, cuadratura, trígono u oposición con cada Sol de Fechas Gemelas de
    persona_b, a partir de HOY. Pensada para el caso de Bonito: pronosticar
    cuándo alguien que se alejó podría volver a estar en contacto."""
    import datetime as dt
    jd_natal_a = jd_from_local(persona_a["year"], persona_a["month"], persona_a["day"],
                                persona_a["hour"], persona_a["minute"], persona_a["utc_offset"])
    utc_salida = utc_offset_salida if utc_offset_salida is not None else persona_a["utc_offset"]
    hoy = dt.datetime.utcnow()
    jd_desde = jd_from_local(hoy.year, hoy.month, hoy.day, hoy.hour, hoy.minute, 0)

    referencias = _referencias_de_persona("B", persona_b, anios_referencias, anios_referencias)

    eventos = []
    for ref in referencias:
        for cuerpo in ("sol", "luna"):
            for delta in (0, 60, 90, 120, 180, -60, -90, -120):
                lon_objetivo = norm360(ref["lon"] + delta)
                for jd_evento in _resolver_fecha_por_progresion(jd_natal_a, lon_objetivo, cuerpo,
                                                                 anios_adelante, jd_desde):
                    nombre_asp = {0: "Conjunción", 60: "Sextil", -60: "Sextil", 90: "Cuadratura",
                                  -90: "Cuadratura", 120: "Trígono", -120: "Trígono", 180: "Oposición"}[delta]
                    eventos.append({
                        "cuerpo_progresado": "Sol" if cuerpo == "sol" else "Luna",
                        "aspecto": nombre_asp,
                        "referencia_B": ref["etiqueta"],
                        "fecha": jd_to_local(jd_evento, utc_salida),
                    })
    eventos.sort(key=lambda e: (e["fecha"]["year"], e["fecha"]["month"], e["fecha"]["day"]))
    return eventos[:100]


NOMBRES_CARDINALES = {"ascendente": "Ascendente", "mc": "MC", "vertex": "Vértex",
                       "ecuador_celeste": "Ecuador Celeste"}


def contacto_cotidian_cardinal(persona_a, persona_b, fecha_contacto, orbe=ORBE_PLANETA,
                                anios_adelante=250, anios_atras=250):
    """Variante de contacto_puntual usando Cotidian Cardinal 1 (ver
    astro.cotidian_cardinal_1): en vez de progresar Sol/Luna de persona_a,
    dirige sus 4 puntos cardinales (Ascendente, MC, Vértex, Ecuador
    Celeste) a la fecha de contacto y los compara contra TODOS los Soles
    de Fechas Gemelas de persona_b. Requiere lat/lon de persona_a (los
    puntos cardinales, a diferencia del Sol/Luna, dependen del lugar).

    NOTA: técnica reconstruida a partir de referencias indirectas de
    Bonito ("revolución de progresión secundaria vinculada con las
    posiciones cardinales") combinadas con documentación pública del
    Winstar ("Daily House Progressed Chart" / Quotidian). Validada en
    signo (no en grado exacto) contra un caso real disponible; tratar
    resultados con ese margen hasta validar con más casos propios."""
    jd_natal_a = jd_from_local(persona_a["year"], persona_a["month"], persona_a["day"],
                                persona_a["hour"], persona_a["minute"], persona_a["utc_offset"])
    jd_contacto = jd_from_local(fecha_contacto["year"], fecha_contacto["month"], fecha_contacto["day"],
                                 fecha_contacto.get("hour", 12), fecha_contacto.get("minute", 0),
                                 fecha_contacto.get("utc_offset", persona_a["utc_offset"]))
    dirigida = cotidian_cardinal_1(jd_natal_a, persona_a["lat"], persona_a["lon"], jd_contacto)

    referencias = _referencias_de_persona("B", persona_b, anios_adelante, anios_atras)

    resultados = []
    for clave, nombre in NOMBRES_CARDINALES.items():
        punto_lon = dirigida[clave]["lon"]
        for ref in referencias:
            asp = _aspecto(punto_lon, ref["lon"], orbe)
            if asp:
                resultados.append({
                    "punto_A": f"{nombre} dirigido (Cotidian Cardinal 1)",
                    "referencia_B": ref["etiqueta"],
                    "signo_B": ref["signo"], "grado_B": ref["grado"],
                    **asp,
                })
    resultados.sort(key=lambda r: r["orbe"])
    return {
        "fecha_contacto": jd_to_local(jd_contacto, fecha_contacto.get("utc_offset", persona_a["utc_offset"])),
        "puntos_dirigidos_A": {clave: {"lon": round(v["lon"], 5), "signo": v["signo"], "grado": v["grado"]}
                                for clave, v in dirigida.items() if clave in NOMBRES_CARDINALES},
        "total_referencias_B": len(referencias),
        "coincidencias": resultados,
    }


def diagrama_cotidian_cardinal(persona_a, persona_b, utc_offset_salida=None, anios_adelante=5,
                                orbe=ORBE_PLANETA, anios_referencias=250):
    """Ventanas de acercamiento futuras usando Cotidian Cardinal 1 en vez de
    progresión secundaria: fechas en que el Ascendente, MC, Vértex o
    Ecuador Celeste dirigidos de persona_a hacen aspecto mayor con algún
    Sol de Fecha Gemela de persona_b."""
    import datetime as dt
    jd_natal_a = jd_from_local(persona_a["year"], persona_a["month"], persona_a["day"],
                                persona_a["hour"], persona_a["minute"], persona_a["utc_offset"])
    utc_salida = utc_offset_salida if utc_offset_salida is not None else persona_a["utc_offset"]
    hoy = dt.datetime.utcnow()
    jd_desde = jd_from_local(hoy.year, hoy.month, hoy.day, hoy.hour, hoy.minute, 0)

    referencias = _referencias_de_persona("B", persona_b, anios_referencias, anios_referencias)

    eventos = []
    for ref in referencias:
        for clave, nombre in NOMBRES_CARDINALES.items():
            for delta in (0, 60, 90, 120, 180, -60, -90, -120):
                lon_objetivo = norm360(ref["lon"] + delta)
                for jd_evento in _resolver_fecha_cotidian_cardinal(
                        jd_natal_a, persona_a["lat"], persona_a["lon"], clave, lon_objetivo,
                        jd_desde, anios_adelante):
                    nombre_asp = {0: "Conjunción", 60: "Sextil", -60: "Sextil", 90: "Cuadratura",
                                  -90: "Cuadratura", 120: "Trígono", -120: "Trígono", 180: "Oposición"}[delta]
                    eventos.append({
                        "punto_progresado": f"{nombre} (Cotidian Cardinal 1)",
                        "aspecto": nombre_asp,
                        "referencia_B": ref["etiqueta"],
                        "fecha": jd_to_local(jd_evento, utc_salida),
                    })
    eventos.sort(key=lambda e: (e["fecha"]["year"], e["fecha"]["month"], e["fecha"]["day"]))
    return eventos[:100]
