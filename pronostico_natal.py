# -*- coding: utf-8 -*-
"""
Antivértex y Pronóstico de Nacimientos / Mudanza — Hugo Bonito.

Reconstruido de una transcripción de clase (fuente: "83f393cf-attachment.txt",
caso real "Marisa", nacida 10/9/1953, investigando el nacimiento de su tercer
hijo; y un segundo caso de mudanza sobre la misma fecha de nacimiento, de
"Yahira").

CITAS TEXTUALES CLAVE:
  "Los nacimientos generalmente se dan con planetas humanos en casa cuatro,
  es decir, en contacto con la cúspide de la cuatro, por ende oposición al
  medio cielo. Mercurio como planeta que simboliza a los hijos... un Venus
  en casa cuatro, generalmente podemos decir que pueden hacer una niña, o
  una criatura muy bonita... un nodo lunar en casa cuatro, recordando que
  el nodo representa todo aquello que perdura en el tiempo... un Sol, un
  varón, un Marte, un varón. Recordemos que el vértex tiene opuesto el
  antivértex, de lo cual significa que como el vértex trabaja como el
  medio cielo, la conjunción de estos planetas con el antivértex está
  justificando también esa posibilidad de nacimiento."

  "Tenemos el AX, es el antiértex [antivértex], trabaja como casa cúspide
  de casa cuatro. Vemos que tenemos posiciones geocéntricas... trabajaremos
  también con posiciones heliocéntricas y con la carta ascensional."

  "Aplicar con flechita para abajo en forma directa las direcciones
  progresadas donde un día es igual a un año." / "Progresión directa = en
  contra de las agujas del reloj; progresión conversa = a favor de las
  agujas del reloj, retrocediendo desde la misma fecha." / "Tendría que
  estar a menos de un grado de orbe [para validar el contacto]."

  Regla de mudanza (segunda mitad de la misma clase, caso Yahira): contactos
  relevantes = conjunción Sol-casa 4 (o Sol-Ascendente), Rueda de la Fortuna
  en conjunción con el Sol, sextil/trígono del Ascendente progresado al Sol
  o del Medio Cielo progresado al Sol.

RECONSTRUCCIÓN HONESTA:

1. ANTIVÉRTEX (alta confianza, técnica): punto exactamente opuesto al
   Vértex (Vértex + 180°) — ya agregado a puntos.puntos_angulares().
   "Trabaja como casa cúspide de casa cuatro", es decir, se usa junto con
   la cúspide de la Casa IV natal como referencia fija de "nacimientos".

2. PROGRESIONES EXTENDIDAS (alta confianza): las mismas progresiones
   secundarias (1 día = 1 año) que ya usa el proyecto (progresiones.py),
   pero ampliadas a TODOS los puntos que Bonito nombra en este pasaje —
   Sol, Luna, Mercurio, Venus, Marte, Nodo, Luna Negra (apogeo medio),
   Saturno, Urano, Plutón, Ascendente, MC, Vértex, Antivértex — y con
   soporte de progresión CONVERSA (retrocediendo desde la fecha de
   nacimiento en vez de avanzar).

3. GEOCÉNTRICA, HELIOCÉNTRICA y CARTA ASCENSIONAL, las tres implementadas.
   La Ascensional NO estaba documentada en el material propio de Bonito
   con suficiente detalle técnico, así que —a pedido de Celina— se
   investigó la técnica estándar en fuentes públicas de astrología
   tradicional (es una técnica conocida, asociada a Sepharial y a las
   "direcciones primarias"/casas Placidus por arco semidiurno, con
   versiones en español bajo el nombre "carta ascensional" o "astrología
   ascensional"): las 12 casas de esa carta miden 30° IGUALES, pero no en
   longitud eclíptica sino en un circuito que arranca en el Ascendente
   (Este), pasa por el Fondo del Cielo/IC (Norte, casa 4), el Descendente
   (Oeste, casa 7) y el Medio Cielo/MC (Sur, casa 10) — la posición de
   cada planeta en ese circuito se obtiene por el mismo cálculo de "arco
   semidiurno" (ascensión oblicua) que ya usa Placidus para sus cúspides,
   aplicado ahora a CADA planeta individualmente, no solo a las cúspides.
   Esta implementación usa swe.house_pos (la función de Swiss Ephemeris
   que hace exactamente ese cálculo de posición-en-casa por arco
   semidiurno, con la latitud geográfica, la oblicuidad y el ARMC del
   instante) para cada punto, y convierte esa "posición de casa continua"
   (1.0 a 13.0) a un grado 0°-360° (0°=Ascendente, 90°=IC/casa 4,
   180°=Descendente, 270°=MC/casa 10) — es la misma matemática de fondo
   que las fuentes en español describen, aplicada con la función nativa de
   la librería astronómica del proyecto en vez de reimplementar a mano las
   fórmulas de arcoseno/diferencia ascensional (más seguro, menos
   propenso a errores de signo/cuadrante). Es una reconstrucción de la
   técnica ESTÁNDAR de "carta ascensional", no una cita textual de cómo
   Bonito la armaba en Winstar — no hay manera de confirmar eso sin más
   material de él específicamente.

4. ORBE: se usa 1° para TODOS los contactos de esta técnica (no 2° para
   cúspides/ángulos como en Sinastría) — Bonito es explícito: "tendría que
   estar a menos de un grado de orbe".

5. GRANULARIDAD: Bonito trabajaba año por año con el teclado del Kepler
   ("a los 22 años... a los 23-24 años..."), no por búsqueda continua de
   cruce exacto — esta implementación reproduce ese mismo criterio:
   evalúa la carta progresada en pasos de 1 año (configurable) y reporta
   qué contactos caen dentro de 1° de orbe en cada paso, en vez de refinar
   por bisección al segundo exacto (que no es como él mismo trabajaba esta
   técnica en particular).

6. INDICADORES DE NACIMIENTO Y DE MUDANZA (confianza media — son las
   reglas descriptas en el caso concreto, no una lista cerrada y
   exhaustiva que Bonito haya enunciado como regla universal): se ofrecen
   como ANOTACIONES sobre los eventos encontrados (qué podría significar
   cada contacto), no como filtro — la app muestra TODOS los contactos
   dentro de orbe y anota los que calzan con una regla conocida, para no
   ocultar aspectos que Bonito sí miraría pero que no encajan en una regla
   ya catalogada.
"""
import swisseph as swe
from astro import (
    jd_from_local, jd_to_local, cuerpo_base_lon, sol_luna_geo_tropical,
    sign_of, norm360, _aspecto,
)
from puntos import puntos_angulares, rueda_de_la_fortuna, es_diurna, casas as _casas_swe

PLANETAS_EXTRA_PRONOSTICO = ["MERCURIO", "VENUS", "MARTE", "NODO", "LUNA_NEGRA", "SATURNO", "URANO", "PLUTON"]
ORBE_PRONOSTICO = 1.0  # Bonito: "menos de un grado de orbe"

# Anotaciones de la regla de nacimientos (Mercurio/Venus/Nodo/Sol/Marte en
# casa 4 o antivértex) y de mudanza (Sol/Rueda de la Fortuna/Ascendente/MC
# en casa 4, Ascendente o en aspecto armónico al Sol).
ANOTACION_NACIMIENTO = {
    "mercurio": "hijos (indicador principal)",
    "venus": "niña / criatura muy bonita",
    "nodo": "algo que perdura en el tiempo",
    "sol": "varón",
    "marte": "varón, activo/enérgico/temperamental",
    "luna_negra": "temas sexuales/embarazo/parto (con el Sol)",
}


def _armc_y_oblicuidad(jd, lat, lon):
    _, ascmc = _casas_swe(jd, lat, lon)
    armc = ascmc[2]
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
    return armc, eps


def _lon_ascensional(lon_eclip, armc, lat, eps):
    """Posición de un punto en la Carta Ascensional (ver docstring del
    módulo): convierte la longitud eclíptica a 'posición de casa continua'
    por arco semidiurno (swe.house_pos, mismo método que usan las cúspides
    Placidus) y la reexpresa como grado 0°-360° — 0°=Ascendente (Este),
    90°=IC/casa 4 (Norte), 180°=Descendente (Oeste), 270°=MC/casa 10
    (Sur)."""
    hp = swe.house_pos(armc, lat, eps, (lon_eclip, 0.0), b'P')
    return norm360((hp - 1.0) * 30.0)


def _convertir_a_ascensional(carta, armc, lat, eps):
    """Reemplaza el 'lon' (y signo/grado) de cada punto de una carta ya
    calculada en eclíptica por su posición en la Carta Ascensional. El
    campo 'signo' pasa a ser 'Casa ascensional N' (no un signo zodiacal
    real — ver docstring del módulo) para no confundirlo con una lectura
    de signo tradicional."""
    out = {}
    for cuerpo, punto in carta.items():
        if not (isinstance(punto, dict) and "lon" in punto):
            out[cuerpo] = punto
            continue
        lon_asc = _lon_ascensional(punto["lon"], armc, lat, eps)
        casa_n = int(lon_asc // 30) + 1
        grado_en_casa = lon_asc - (casa_n - 1) * 30
        out[cuerpo] = {
            "lon": lon_asc, "lon_eclip": punto["lon"],
            "signo": f"Casa ascensional {casa_n}", "grado": round(grado_en_casa, 4),
        }
    return out


def carta_extendida(jd, lat, lon, helio=False, sideral=False, ascensional=False):
    """Carta con TODOS los puntos relevantes para esta técnica: Sol, Luna,
    Mercurio, Venus, Marte, Nodo, Luna Negra, Saturno, Urano, Plutón,
    Ascendente, MC, Vértex, Antivértex, Ecuador Celeste, Rueda de la
    Fortuna y la cúspide de la Casa IV (Placidus). Con ascensional=True,
    todas las posiciones se reexpresan en la Carta Ascensional (ver
    docstring del módulo) en vez de longitud eclíptica — en ese caso
    'helio' se ignora (la técnica ascensional es inherentemente
    geocéntrica: depende de la latitud geográfica y el horizonte local)."""
    if ascensional:
        base = carta_extendida(jd, lat, lon, helio=False, sideral=sideral, ascensional=False)
        armc, eps = _armc_y_oblicuidad(jd, lat, lon)
        carta_asc = _convertir_a_ascensional(base, armc, lat, eps)
        # Ascendente, MC y la cúspide de Casa IV son, por definición, los
        # puntos cardinales que ARMAN la Carta Ascensional (0°/270°/90°
        # siempre, en CUALQUIER carta, natal o progresada) — compararlos
        # entre sí o contra su propio progresado no aporta información,
        # solo "coincidencias" triviales garantizadas por construcción. Se
        # excluyen de esta variante (Vértex, Antivértex, Ecuador Celeste y
        # Rueda de la Fortuna sí varían de verdad y se conservan).
        for clave in ("ascendente", "mc", "casa_4"):
            carta_asc.pop(clave, None)
        return carta_asc

    sol_lon, luna_lon = sol_luna_geo_tropical(jd)  # Sol/Luna siempre geo-trópico, igual que el resto del proyecto
    sol_signo, sol_grado = sign_of(sol_lon)
    luna_signo, luna_grado = sign_of(luna_lon)
    angulos = puntos_angulares(jd, lat, lon)  # Placidus; incluye antivertex y cusps
    diurna = es_diurna(sol_lon, angulos["ascendente"]["lon"])
    fortuna = rueda_de_la_fortuna(sol_lon, luna_lon, angulos["ascendente"]["lon"], diurna)
    casa4_signo, casa4_grado = sign_of(angulos["cusps"][3])

    puntos = {
        "sol": {"lon": sol_lon, "signo": sol_signo, "grado": round(sol_grado, 4)},
        "luna": {"lon": luna_lon, "signo": luna_signo, "grado": round(luna_grado, 4)},
        "ascendente": angulos["ascendente"], "mc": angulos["mc"],
        "vertex": angulos["vertex"], "antivertex": angulos["antivertex"],
        "ecuador_celeste": angulos["ecuador_celeste"],
        "rueda_de_la_fortuna": fortuna,
        "casa_4": {"lon": angulos["cusps"][3], "signo": casa4_signo, "grado": round(casa4_grado, 4)},
    }
    for nombre in PLANETAS_EXTRA_PRONOSTICO:
        try:
            lon_p, _ = cuerpo_base_lon(jd, nombre, helio=helio, sideral=sideral)
            signo, grado = sign_of(lon_p)
            puntos[nombre.lower()] = {"lon": lon_p, "signo": signo, "grado": round(grado, 4)}
        except Exception:
            continue  # punto puntualmente no disponible (p. ej. fuera de rango de un archivo de efemérides)
    return puntos


def carta_natal_extendida(year, month, day, hour, minute, utc_offset, lat, lon,
                           helio=False, sideral=False, ascensional=False):
    jd = jd_from_local(year, month, day, hour, minute, utc_offset)
    return carta_extendida(jd, lat, lon, helio=helio, sideral=sideral, ascensional=ascensional)


def progresion_extendida(jd_natal, edad_anios, lat, lon, conversa=False, helio=False, sideral=False, ascensional=False):
    """Progresión secundaria (1 día = 1 año) de la carta extendida completa.
    Directa: avanza 'edad_anios' días desde el natal. Conversa: retrocede
    la misma cantidad de días — Bonito: 'progresión conversa... retrocede
    desde la misma fecha'."""
    delta_dias = edad_anios if not conversa else -edad_anios
    jd_prog = jd_natal + delta_dias
    carta = carta_extendida(jd_prog, lat, lon, helio=helio, sideral=sideral, ascensional=ascensional)
    carta["edad_anios"] = round(edad_anios, 3)
    carta["conversa"] = conversa
    carta["jd_progresado"] = jd_prog
    return carta


def _es_punto(v):
    return isinstance(v, dict) and "lon" in v


def escanear_pronostico(year, month, day, hour, minute, utc_offset, lat, lon,
                         anios_desde=0, anios_hasta=45, paso_anios=1.0,
                         helio=False, sideral=False, ascensional=False, incluir_conversa=True):
    """Recorre edades de anios_desde a anios_hasta (paso paso_anios, 1 año
    por defecto — el mismo criterio año-por-año que usaba Bonito con el
    Kepler), progresión directa y conversa, comparando la carta progresada
    completa contra la carta natal completa. Devuelve todos los contactos
    dentro de 1° de orbe, anotando los que calzan con la regla de
    nacimiento u de mudanza documentada. 'ascensional=True' usa la Carta
    Ascensional en vez de la eclíptica (ver docstring del módulo) — ignora
    'helio' si ambos se piden juntos, porque la técnica ascensional es
    inherentemente geocéntrica."""
    jd_natal = jd_from_local(year, month, day, hour, minute, utc_offset)
    natal = carta_extendida(jd_natal, lat, lon, helio=helio, sideral=sideral, ascensional=ascensional)

    eventos = []
    modos = [False, True] if incluir_conversa else [False]
    for conversa in modos:
        edad = anios_desde
        while edad <= anios_hasta + 1e-9:
            prog = progresion_extendida(jd_natal, edad, lat, lon, conversa=conversa,
                                         helio=helio, sideral=sideral, ascensional=ascensional)
            for cuerpo_p, punto_p in prog.items():
                if not _es_punto(punto_p):
                    continue
                for cuerpo_n, punto_n in natal.items():
                    if not _es_punto(punto_n):
                        continue
                    asp = _aspecto(punto_p["lon"], punto_n["lon"], ORBE_PRONOSTICO)
                    if not asp:
                        continue
                    nota = None
                    if cuerpo_n == "casa_4" or cuerpo_n == "antivertex":
                        if asp["aspecto"] == "Conjunción" and cuerpo_p in ANOTACION_NACIMIENTO:
                            nota = f"Posible nacimiento — {ANOTACION_NACIMIENTO[cuerpo_p]}"
                    if cuerpo_n == "mc" and asp["aspecto"] == "Oposición" and cuerpo_p in ANOTACION_NACIMIENTO:
                        nota = f"Posible nacimiento (oposición a MC natal) — {ANOTACION_NACIMIENTO[cuerpo_p]}"
                    if cuerpo_p == "sol" and cuerpo_n in ("casa_4", "ascendente") and asp["aspecto"] == "Conjunción":
                        nota = "Posible mudanza/cambio de domicilio (Sol progresado en casa 4 / Ascendente)"
                    if cuerpo_p == "rueda_de_la_fortuna" and cuerpo_n == "sol" and asp["aspecto"] == "Conjunción":
                        nota = "Posible mudanza/cambio de domicilio (Rueda de la Fortuna progresada conjunción Sol natal)"
                    if cuerpo_p in ("ascendente", "mc") and cuerpo_n == "sol" and asp["aspecto"] in ("Sextil", "Trígono"):
                        nota = f"Posible mudanza/cambio de domicilio ({cuerpo_p.capitalize()} progresado en {asp['aspecto'].lower()} al Sol natal)"
                    eventos.append({
                        "edad_anios": round(edad, 3), "conversa": conversa,
                        "punto_progresado": cuerpo_p, "punto_natal": cuerpo_n,
                        "signo_progresado": punto_p["signo"], "grado_progresado": punto_p["grado"],
                        "signo_natal": punto_n["signo"], "grado_natal": punto_n["grado"],
                        "aspecto": asp["aspecto"], "orbe": asp["orbe"], "partil": asp["partil"],
                        "nota": nota,
                    })
            edad += paso_anios

    eventos.sort(key=lambda e: (e["edad_anios"], e["conversa"], e["orbe"]))
    modo_txt = "Ascensional" if ascensional else ("Heliocéntrica" if helio else "Geocéntrica")
    return {
        "carta_natal": natal,
        "modo": modo_txt,
        "total_eventos": len(eventos),
        "eventos": eventos,
        "nota": (f"Técnica de pronóstico de nacimientos/mudanza de Bonito (caso Marisa/Yahira, "
                 f"10/9/1953), variante {modo_txt}: progresiones secundarias (1 día = 1 año, directa y "
                 "conversa) de Sol, Luna, Mercurio, Venus, Marte, Nodo, Luna Negra, Saturno, Urano, "
                 "Plutón, Ascendente, MC, Vértex y Antivértex, comparadas contra la carta natal "
                 "completa (incluida la cúspide de la Casa IV) dentro de 1° de orbe. Los contactos que "
                 "calzan con la regla documentada de nacimiento (Mercurio/Venus/Nodo/Sol/Marte en casa "
                 "4 o Antivértex) o de mudanza (Sol/Rueda de la Fortuna/Ascendente/MC en casa 4, "
                 "Ascendente o aspecto armónico al Sol) están anotados; los demás contactos se "
                 "muestran igual, sin descartarlos. La variante Ascensional es una reconstrucción de "
                 "la técnica estándar (no confirmada letra por letra con material propio de Bonito) — "
                 "ver docstring de pronostico_natal.py."),
    }
