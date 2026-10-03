# -*- coding: utf-8 -*-
"""
Imantación de personajes/instituciones — Hugo Bonito.

Reconstruido de un tramo de clase (transcripción, ~primeros 22 minutos)
donde Bonito presenta esta técnica ANTES de pasar al ejemplo de Boca vs.
Banfield con el Programa Omega (ver omega.py, que reconstruye la segunda
mitad de esa misma clase). Palabras de Bonito, tal como quedaron en la
transcripción:

  "La técnica en sí es poder controlar las lunas de fechas gemelas de un
  periodo detectable... para que esa persona esté imantada... si está
  imantado y está su imagen, es porque está teniendo un dominio en una
  intervención [en lo que esté haciendo]."

  "En el caso de una persona, si nosotros en determinado momento somos
  invitados para un programa de televisión o de radio, las lunas que se
  están moviendo en el cielo en el momento que hacen conjunción con
  nuestros SOLES de fechas gemelas, BASE PLUTÓN ESPECIALMENTE Y BASE
  NEPTUNO TAMBIÉN, son los momentos donde la cámara nos va a tomar...
  ahí es donde yo digo que estamos imantados. La palabra imantada es,
  digamos, tenemos una idea de que nos genera la sensación de atracción,
  de atracción de miradas. Pasamos de una postura introvertida a una
  postura de acción y extrovertida."

  "Con las empresas, con los equipos, pasa exactamente lo mismo que con
  las personas" — ahí Bonito arma la carta de fundación de Boca Juniors
  (3/4/1905, 19:28:43, hora ya "comprobada y rectificada") y sus Fechas
  Gemelas (Retornos de Plutón, Sol y Luna, 4 variantes), y dice: "cuando
  una luna del cielo se pone en conjunción con una luna del equipo de
  Boca, el equipo está imantado. Son los momentos donde las hinchadas
  hacen cantos, hacen la ola, gritan un gol."

TÉCNICA — a diferencia de Programa Omega (que Bonito arma después, en la
misma clase, específicamente para localizar GOLES/resultado de un
partido con un banco único base Plutón): la Imantación es la técnica
MÁS GENERAL — sirve para cualquier persona, institución o equipo, y
para cualquier ventana horaria (una entrevista de TV, una gestión, un
partido, una sesión) — y agrupa DOS bancos de referencia, no uno:

  - Sol y Luna de las Fechas Gemelas base PLUTÓN (como Omega), y
  - Sol y Luna de las Fechas Gemelas base NEPTUNO (Bonito: "especialmente
    [Plutón] Y BASE NEPTUNO TAMBIÉN" — explícitamente dice que ambas
    bases sirven, algo que en Omega quedó pendiente como "no
    implementado", ver nota en omega.py).

El "cuerpo en tránsito" que se compara contra ese banco puede ser la
Luna real (el caso general — es rápida, cambia de posición cada pocos
minutos, ideal para ventanas cortas) o el Sol (más lento, para ventanas
de varios días). El momento de conjunción PARTIL (orbe muy cerrado) es
el "horario imantado": el instante en que la persona/institución está
"afuera", visible, protagonizando, con dominio sobre la situación.

RECONSTRUCCIÓN HONESTA: el mecanismo de escaneo (bisección exacta sobre
una ventana horaria real) es el MISMO que en omega.py — se reutiliza
literalmente esa función (_buscar_conjuncion_en_ventana) en vez de
reimplementarlo, porque es el mismo cálculo. Lo que agrega este módulo,
propio de la Imantación (y no de Omega), es: (1) el banco DOBLE
Plutón+Neptuno que Bonito menciona explícitamente para esta técnica, y
(2) que se ofrece como consulta de propósito general ("¿está
imantado/a en esta ventana?"), no atada al pronóstico de un resultado
deportivo. No se reconstruyó ningún "banco" adicional más allá de
Sol/Luna de Fechas Gemelas — Bonito no menciona en este tramo otros
cuerpos para la Imantación en sí (a diferencia de Horaria u otras
técnicas).
"""
from astro import calcular_fechas_gemelas, jd_to_local
from omega import _buscar_conjuncion_en_ventana

BASES_IMANTACION = ("PLUTON", "NEPTUNO")


def _banco_de_grados_con_base(fechas_gemelas, base):
    """Igual que omega._banco_de_grados, pero etiquetando también de qué
    base (Plutón/Neptuno) salió cada grado — necesario acá porque la
    Imantación pool-ea ambas bases juntas."""
    banco = []
    for variante, lista in fechas_gemelas.items():
        for entrada in lista:
            banco.append({"grado": entrada["sol"]["lon"], "cuerpo_origen": "Sol",
                           "base": base, "variante": variante, "fecha_origen": entrada["fecha_local"]})
            banco.append({"grado": entrada["luna"]["lon"], "cuerpo_origen": "Luna",
                           "base": base, "variante": variante, "fecha_origen": entrada["fecha_local"]})
    return banco


def banco_imantacion(entidad, anios_atras=150, anios_adelante=150, bases=BASES_IMANTACION):
    """Arma el banco DOBLE (Plutón + Neptuno, salvo que se pida otra cosa
    en 'bases') de Soles y Lunas de Fechas Gemelas de una persona,
    institución o equipo de referencia."""
    banco = []
    for base in bases:
        fechas_gemelas = calcular_fechas_gemelas(
            entidad["year"], entidad["month"], entidad["day"],
            entidad["hour"], entidad["minute"], entidad["utc_offset"],
            anios_atras=anios_atras, anios_adelante=anios_adelante, cuerpo_base=base)
        banco += _banco_de_grados_con_base(fechas_gemelas, base)
    return banco


def escanear_imantacion(entidad, jd_ventana_ini, jd_ventana_fin, utc_offset_salida,
                         anios_atras=150, anios_adelante=150, cuerpo_transito="LUNA",
                         bases=BASES_IMANTACION):
    """Escanea la ventana horaria real pedida buscando los 'horarios
    imantados' de una persona/institución/equipo: momentos en que el
    cuerpo en tránsito (Luna por defecto, criterio de Bonito para
    ventanas cortas) hace conjunción partil con algún grado de su banco
    (Sol/Luna de Fechas Gemelas, base Plutón y Neptuno pooleadas)."""
    banco = banco_imantacion(entidad, anios_atras, anios_adelante, bases)

    eventos = []
    for item in banco:
        for jd in _buscar_conjuncion_en_ventana(jd_ventana_ini, jd_ventana_fin, item["grado"], cuerpo_transito):
            eventos.append({
                "hora_local": jd_to_local(jd, utc_offset_salida),
                "cuerpo_en_transito": cuerpo_transito.capitalize(),
                "grado_banco": round(item["grado"], 5),
                "origen_banco": item["cuerpo_origen"],
                "base_origen": item["base"].capitalize(),
                "variante_origen": item["variante"],
                "fecha_origen": item["fecha_origen"],
            })
    eventos.sort(key=lambda e: (e["hora_local"]["hour"], e["hora_local"]["minute"], e["hora_local"]["second"]))
    return {
        "total_banco": len(banco), "total_eventos": len(eventos), "eventos": eventos,
        "nota": ("Técnica de Imantación de Bonito: 'imantado/a' es el momento en que la persona o "
                 "institución está exteriorizada, visible, con dominio sobre la situación — el "
                 "momento en que 'la cámara nos toma' o 'la hinchada grita un gol'. Cada evento "
                 "listado es un cruce EXACTO (partil) del cuerpo en tránsito con un grado del banco "
                 "de Fechas Gemelas (Sol o Luna, base Plutón o Neptuno) de la entidad consultada."),
    }
