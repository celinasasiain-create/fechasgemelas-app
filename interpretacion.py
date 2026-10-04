# -*- coding: utf-8 -*-
"""
Motor de interpretación — Hugo Bonito.

Genera el TEXTO de lectura para un evento (aspecto entre dos puntos, o un
evento de tránsito/electiva sin estructura de dos puntos), combinando dos
fuentes, en este orden de prioridad:

1. MARCADOR FIJO de Hugo: un texto que él mismo dio, documentado y
   verificable a partir de las clases (ver diccionario.py). Cuando existe,
   se usa tal cual — es lo más fiel posible a lo que Bonito dijo.

2. GENERADO POR IA, estilo Bonito: cuando no hay marcador fijo para esa
   combinación exacta, se le pide al modelo (API de Anthropic) que redacte
   una lectura siguiendo los principios y el estilo documentados de Bonito
   (ver PRINCIPIOS_BONITO más abajo) — aclarando siempre que es una
   interpretación generada, no una cita textual de Hugo.

3. Si no hay marcador fijo NI hay clave de API configurada (ANTHROPIC_API_KEY),
   se cae a la lectura general de categoría del punto (lo que ya hacía
   diccionario.interpretar() antes de este módulo) — la app sigue
   funcionando igual, solo sin el texto interpretativo fino.

Este archivo es intencionalmente honesto sobre la procedencia de cada
lectura: toda interpretación devuelta incluye un campo "fuente" que dice
si es un marcador de Hugo, una generación de IA, o una lectura general —
para que Celina (o cualquier usuaria de la app) sepa siempre qué tan
literal es el texto que está leyendo.
"""
import os
import re

from diccionario import (
    CATEGORIA_PUNTO,
    MARCADORES_ESPECIFICOS,
    REGENTE_DE_SIGNO,
    interpretar as _interpretar_fijo,
)

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Principios de estilo y contenido de Hugo Bonito, reconstruidos a partir de
# todas las clases y técnicas revisadas en este proyecto (Fechas Gemelas,
# Horaria, Programa Omega, Imantación, Electiva/Manchas Solares,
# Discriminación por orbe, Retornos, Proluna, etc.). Esto NO reemplaza los
# marcadores fijos — es el contexto de estilo para cuando no hay un
# marcador documentado y hace falta generar una lectura razonable.
PRINCIPIOS_BONITO = """\
Sos un asistente que redacta interpretaciones astrológicas siguiendo el \
estilo y el método del astrólogo uruguayo Hugo Bonito (ya fallecido), tal \
como se documentó en sus clases. Reglas de estilo y contenido que Bonito \
sigue sistemáticamente:

- Es concreto y empírico: da lecturas puntuales, con ejemplos de vida real \
(salud, familia, trabajo, vínculos, viajes, riesgo, dinero), nunca \
generalidades vagas tipo horóscopo.
- Privilegia el ORBE: cuanto más cerrado (exacto) el aspecto, más fuerte y \
literal es la lectura. Un aspecto partil (orbe menor a algunos minutos de \
arco) es mucho más determinante que uno con varios grados de orbe.
- Lee la CUALIDAD del aspecto (armónico: sextil/trígono = favorable, \
fluido; tenso: cuadratura/semicuadratura/sesquicuadratura = fricción, \
crisis, esfuerzo; oposición = tensión que se resuelve por polaridad, a \
veces la persona/situación "opuesta"; conjunción = fusión, identificación \
directa con la energía del otro punto).
- Usa la equivalencia signo <-> planeta regente para leer con velocidad \
(por ejemplo, un aspecto con Marte se lee también en clave de Aries).
- Distingue el tipo de punto: Sol y Luna leen personalidad/vocación; \
Ascendente/Ecuador Celeste leen el "camino" u objetivo de vida; Medio \
Cielo/Vértex/Rueda de la Fortuna leen una "necesidad" (no necesariamente \
positiva) y, en oposición, a la familia de origen; Proluna lee \
disponibilidad MOMENTÁNEA de una energía ese día, no un rasgo estable.
- Es sobrio: no dramatiza, no promete, y cuando algo es una observación \
personal no confirmada (no un patrón verificado en muchos casos) lo dice \
como tal, no como regla.
- Es breve: sus lecturas orales suelen ser dos o tres frases, muy densas, \
sin relleno.

Tu tarea es escribir UNA lectura breve (2 a 4 frases, en español rioplatense \
sobrio, sin exclamaciones ni tono new-age) para el evento astrológico \
puntual que se te describe, siguiendo estos principios. Nunca digas que es \
una cita textual de Hugo Bonito — es una interpretación generada siguiendo \
su método, y así debe quedar claro implícitamente por el tono, sin \
necesidad de aclararlo dentro del texto (la app ya marca la procedencia \
aparte). Si el evento no da para una lectura específica, sé honesto y \
ceñite a la categoría general del/los punto(s) involucrados."""


def _cliente_ia():
    """Devuelve un cliente de Anthropic si hay ANTHROPIC_API_KEY configurada
    en el entorno, o None si no (para que el resto de la app siga andando
    sin IA, solo con marcadores fijos y lectura general)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


def _llamar_ia(descripcion_evento, contexto_extra=""):
    """Le pide al modelo una lectura de 2-4 frases para el evento descripto.
    Devuelve None ante cualquier error (sin API key, sin red, error de la
    API, etc.) para que el llamador pueda caer al siguiente nivel de
    fallback sin romper la técnica que lo está usando."""
    cliente = _cliente_ia()
    if cliente is None:
        return None
    prompt = descripcion_evento
    if contexto_extra:
        prompt += f"\n\nContexto adicional de la técnica: {contexto_extra}"
    try:
        respuesta = cliente.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            system=PRINCIPIOS_BONITO,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = "".join(
            bloque.text for bloque in respuesta.content if getattr(bloque, "type", None) == "text"
        ).strip()
        return texto or None
    except Exception:
        return None


def _descripcion_aspecto(puntoA, puntoB, aspecto, orbe, tecnica, mismo_individuo=True,
                          nombre_a=None, nombre_b=None):
    orbe_txt = f"{orbe:.4f}°" if isinstance(orbe, (int, float)) else str(orbe)
    if mismo_individuo:
        return (
            f"Técnica: {tecnica}. Aspecto: {puntoA} en {aspecto} con {puntoB}, "
            f"orbe {orbe_txt}, dentro de la carta de UNA sola persona. Escribí la "
            f"lectura de este aspecto puntual (personalidad/destino propio, no un "
            f"vínculo entre dos personas)."
        )
    etiqueta_a = nombre_a or "la Persona A"
    etiqueta_b = nombre_b or "la Persona B"
    return (
        f"Técnica: {tecnica}. Aspecto de SINASTRÍA entre dos personas distintas: "
        f"el {puntoA} de {etiqueta_a} está en {aspecto} con el {puntoB} de {etiqueta_b}, "
        f"orbe {orbe_txt}. Escribí una lectura de vínculo (cómo esa energía de "
        f"{etiqueta_a} se relaciona con esa energía de {etiqueta_b}), NO una lectura "
        f"de personalidad individual — no le atribuyas a una sola persona lo que "
        f"describe la relación entre ambas."
    )


def _lectura_general_cruzada(puntoA, puntoB):
    """Lectura de categoría (sin marcador) para un aspecto entre puntos de
    DOS personas distintas — usa solo CATEGORIA_PUNTO, nunca
    MARCADORES_ESPECIFICOS (esos están documentados por Hugo para la carta
    de una sola persona, no para un cruce de sinastría)."""
    generales = []
    for p in (puntoA, puntoB):
        if p in CATEGORIA_PUNTO:
            generales.append({"punto": p, "lectura_general": CATEGORIA_PUNTO[p]})
    return generales


def interpretar_aspecto(puntoA, puntoB, aspecto, orbe, tecnica="Fechas Gemelas", usar_ia=True,
                         mismo_individuo=True, nombre_a=None, nombre_b=None):
    """Interpretación para un evento de dos puntos + aspecto + orbe (el caso
    más común: Fechas Gemelas, Horaria, Discriminación por orbe, Retornos).
    Devuelve siempre un dict con 'texto' y 'fuente' ('marcador_hugo',
    'ia_estilo_bonito' o 'lectura_general'). 'usar_ia=False' salta el
    llamado a la API (para listas largas de eventos, donde solo conviene
    generar con IA los primeros N más relevantes — ver LIMITE_IA_POR_LISTA
    en las rutas de app.py).

    'mismo_individuo' distingue si los dos puntos pertenecen a la carta de
    UNA sola persona (True, el caso de Progresiones, Arco Solar, Retornos,
    Antivértex, etc.) o si vienen de DOS personas distintas (False: una
    fila de sinastría dentro de Comparar Fechas Gemelas, Sinastría,
    Contacto, Discriminación por orbe, Mellizos). Los marcadores fijos de
    diccionario.py (MARCADORES_ESPECIFICOS) fueron documentados por Hugo
    siempre para la carta de una sola persona — cuando mismo_individuo es
    False, se saltan a propósito (no corresponden a un cruce entre dos
    cartas) y se va directo a una lectura de sinastría generada por IA, o
    si no hay IA, a la lectura general de categoría de cada punto."""
    if mismo_individuo:
        fijo = _interpretar_fijo(puntoA, puntoB, aspecto, orbe)
        if fijo["tipo"] == "marcador_especifico":
            textos = [r["texto"] for r in fijo["resultados"]]
            fuentes = sorted({r["fuente"] for r in fijo["resultados"]})
            confianzas = sorted({r["confianza"] for r in fijo["resultados"]})
            return {
                "texto": " / ".join(textos),
                "fuente": "marcador_hugo",
                "detalle_fuente": ", ".join(fuentes),
                "confianza": ", ".join(confianzas),
            }
        generales = fijo["resultados"]
    else:
        generales = _lectura_general_cruzada(puntoA, puntoB)

    texto_ia = _llamar_ia(_descripcion_aspecto(
        puntoA, puntoB, aspecto, orbe, tecnica, mismo_individuo, nombre_a, nombre_b,
    )) if usar_ia else None
    if texto_ia:
        return {"texto": texto_ia, "fuente": "ia_estilo_bonito", "detalle_fuente": ANTHROPIC_MODEL}

    if generales:
        if mismo_individuo or len(generales) < 2:
            texto = " ".join(f"{g['punto'].capitalize()}: {g['lectura_general']}" for g in generales)
        else:
            # Dos personas distintas: en vez de pegar las dos definiciones
            # sueltas, las redactamos como una lectura de vínculo — qué
            # trae cada una a la relación, no qué es cada punto en abstracto.
            etiqueta_a = (nombre_a or "la Persona A").capitalize()
            etiqueta_b = (nombre_b or "la Persona B").capitalize()
            ga, gb = generales[0], generales[1]
            texto = (
                f"Lectura de vínculo (sin marcador de Hugo ni IA disponible para esta "
                f"combinación): {etiqueta_a} aporta {ga['punto']} — {ga['lectura_general']} "
                f"{etiqueta_b} aporta {gb['punto']} — {gb['lectura_general']} El aspecto entre "
                f"ambos puntos indica cómo esas dos energías se cruzan en el vínculo, no un "
                f"rasgo de personalidad de una sola persona."
            )
    else:
        texto = "No hay lectura documentada para esta combinación de puntos."
    return {"texto": texto, "fuente": "lectura_general", "detalle_fuente": "categoría del punto"}


def interpretar_evento_libre(tecnica, descripcion, contexto_extra=""):
    """Interpretación para eventos que NO se reducen a un aspecto entre dos
    puntos natales (Imantación, Electiva de riesgo, Manchas Solares,
    Programa Omega): solo hay generación por IA (no existen marcadores
    fijos de Hugo para estas combinaciones puntuales, porque son cruces de
    tránsito contra un banco de grados, no aspectos entre dos cartas). Si no
    hay API key configurada, devuelve None y la técnica sigue funcionando
    igual, solo sin el campo de interpretación."""
    texto_ia = _llamar_ia(f"Técnica: {tecnica}. {descripcion}", contexto_extra)
    if texto_ia:
        return {"texto": texto_ia, "fuente": "ia_estilo_bonito", "detalle_fuente": ANTHROPIC_MODEL}
    return None


def ia_disponible():
    """True si hay ANTHROPIC_API_KEY configurada (para que el frontend/las
    rutas puedan avisar cuándo el motor de IA no está activo)."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
