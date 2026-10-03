# -*- coding: utf-8 -*-
"""
Predicción de números de Lotería — Hugo Bonito (Programa Omega, variante
lotería).

Fuente: 62146864-attachment.txt (transcripción de clase), resumida en
revision_batch2.md entrada 5.

TÉCNICA (tal como la describe Bonito): desde ~1990-91 mantenía una base
personal de 52.564 renglones — las posiciones de Sol y Luna de las Fechas
Gemelas (retornos de Plutón, en las 4 variantes Geo/Helio x Trópico/
Sideral) calculadas para 900 números que habían salido en la Lotería
Nacional de Argentina (un "banco" por número, igual en estructura al banco
de grados de Programa Omega). Cada semana:
1. Toma la posición de Plutón HELIOCÉNTRICO TRÓPICO de "hoy" y la de 7 días
   después (el sorteo de la semana siguiente).
2. Ese pequeño arco de Plutón (Bonito da un ejemplo real: ~2' de arco en
   una semana) se compara, con un programa en Visual Basic hecho por su
   hijo, contra las 52.564 posiciones guardadas, buscando TRÍGONOS (o
   SEXTILES) — los números cuyo banco "activa" ese aspecto son los
   favorecidos para salir esa semana; una CUADRATURA marca "números
   negados" (a evitar).
3. Para la Lotería de Navidad de España (22/12, 12hs) usa una variante más
   simple: arma el banco de Soles de Fechas Gemelas del día del sorteo, y
   busca con qué semana del año el Sol real en tránsito (geocéntrico
   trópico, el que se mueve rápido) hace CONJUNCIÓN PARTIL con alguno de
   esos Soles — esa es la semana recomendada para comprar el billete
   ("momentos hermanos, gemelos, idénticos, análogos").

RECONSTRUCCIÓN HONESTA — lo que NO se pudo reconstruir:
- La base real de 900 números de Bonito (con su fecha histórica de salida
  cada uno, que es lo que arma el "banco" de cada número) NO está en el
  material subido — él la ofrece compartir en la clase, pero el archivo en
  sí no llegó a este proyecto. Sin esos 900 pares (número, fecha en que
  salió), no hay con qué generar el banco de 52.564 filas.
- Lo que SÍ se reconstruye es el MOTOR: se arma el banco de cualquier lista
  de números que Celina cargue (cada uno con su fecha de referencia), y se
  escanea el arco real de Plutón heliocéntrico trópico de la semana
  pedida, con el mismo patrón de bisección exacta que usa el resto del
  proyecto (en vez del programa en Visual Basic del hijo de Hugo). El
  "aspecto" 20 segundos de espera que menciona Bonito era la limitación
  del programa viejo escaneando 52.000 filas, no parte de la técnica.
- Orbe: Bonito no da un orbe explícito para esta técnica (habla de
  "trígono" en términos amplios, no partil, a diferencia de la Navidad que
  sí pide partil). Se usa ORBE_PLANETA (1°, la convención general del
  proyecto para Sol/Luna) para trígono/sextil/cuadratura semanales, y
  ORBE_PARTIL (0.05°) para la variante Navidad, como pide el texto.
"""
from astro import (
    calcular_fechas_gemelas, cuerpo_base_lon, jd_from_local, jd_to_local,
    _diff_angular, ORBE_PLANETA, ORBE_PARTIL, norm360,
)

ASPECTOS_LOTERIA = {"Trígono": 120, "Sextil": 60}
ASPECTO_NEGADO = {"Cuadratura": 90}


def _banco_numero(numero, year, month, day, hour=12, minute=0, utc_offset=0,
                   anios_atras=60, anios_adelante=60):
    """Banco de grados (Sol y Luna, 4 variantes) de un número, a partir de
    su fecha de referencia (histórica de salida) — mismo patrón que
    omega._banco_de_grados, acá etiquetado con el número."""
    fechas_gemelas = calcular_fechas_gemelas(year, month, day, hour, minute, utc_offset,
                                              anios_atras=anios_atras, anios_adelante=anios_adelante)
    banco = []
    for variante, lista in fechas_gemelas.items():
        for entrada in lista:
            banco.append({"numero": numero, "grado": entrada["sol"]["lon"], "cuerpo_origen": "Sol",
                           "variante": variante, "fecha_origen": entrada["fecha_local"]})
            banco.append({"numero": numero, "grado": entrada["luna"]["lon"], "cuerpo_origen": "Luna",
                           "variante": variante, "fecha_origen": entrada["fecha_local"]})
    return banco


def _pluton_helio_tropico(jd):
    lon, _ = cuerpo_base_lon(jd, "PLUTON", helio=True, sideral=False)
    return lon


def escanear_loteria_semanal(numeros, jd_ini, jd_fin, anios_atras=60, anios_adelante=60, orbe=ORBE_PLANETA):
    """Programa Omega, variante lotería semanal: para cada número de
    'numeros' (lista de dicts con numero/year/month/day/hour/minute/
    utc_offset — SU fecha histórica de referencia, ver nota de
    reconstrucción honesta en el docstring del módulo), arma su banco y
    chequea si el arco real de Plutón heliocéntrico trópico entre jd_ini y
    jd_fin forma trígono/sextil (favorecido) o cuadratura (negado) con
    algún punto del banco. Usa el punto MEDIO del arco semanal como
    posición de referencia de Plutón (se mueve solo un par de minutos de
    arco en una semana, según el propio ejemplo de Bonito)."""
    jd_medio = (jd_ini + jd_fin) / 2.0
    lon_pluton_ini = _pluton_helio_tropico(jd_ini)
    lon_pluton_fin = _pluton_helio_tropico(jd_fin)
    lon_pluton_medio = _pluton_helio_tropico(jd_medio)

    favorecidos = {}
    negados = {}
    for item in numeros:
        banco = _banco_numero(item["numero"], item["year"], item["month"], item["day"],
                               item.get("hour", 12), item.get("minute", 0), item.get("utc_offset", 0),
                               anios_atras, anios_adelante)
        for punto in banco:
            for lon_pluton, etiqueta_momento in ((lon_pluton_ini, "inicio de semana"),
                                                  (lon_pluton_medio, "mitad de semana"),
                                                  (lon_pluton_fin, "fin de semana")):
                diff = abs(_diff_angular(lon_pluton, punto["grado"]))
                for nombre_asp, angulo in ASPECTOS_LOTERIA.items():
                    if abs(diff - angulo) <= orbe:
                        bucket = favorecidos.setdefault(item["numero"], [])
                        bucket.append({"aspecto": nombre_asp, "orbe": round(abs(diff - angulo), 4),
                                       "momento": etiqueta_momento, "origen_banco": punto["cuerpo_origen"],
                                       "variante_origen": punto["variante"], "fecha_origen": punto["fecha_origen"]})
                for nombre_asp, angulo in ASPECTO_NEGADO.items():
                    if abs(diff - angulo) <= orbe:
                        bucket = negados.setdefault(item["numero"], [])
                        bucket.append({"aspecto": nombre_asp, "orbe": round(abs(diff - angulo), 4),
                                       "momento": etiqueta_momento, "origen_banco": punto["cuerpo_origen"],
                                       "variante_origen": punto["variante"], "fecha_origen": punto["fecha_origen"]})

    favorecidos_lista = sorted(
        ({"numero": n, "hits": sorted(h, key=lambda x: x["orbe"])} for n, h in favorecidos.items()),
        key=lambda x: x["hits"][0]["orbe"])
    negados_lista = sorted(
        ({"numero": n, "hits": sorted(h, key=lambda x: x["orbe"])} for n, h in negados.items()),
        key=lambda x: x["hits"][0]["orbe"])

    return {
        "pluton_helio_tropico": {"inicio": round(lon_pluton_ini, 5), "fin": round(lon_pluton_fin, 5)},
        "favorecidos": favorecidos_lista,
        "negados": negados_lista,
        "nota": ("Trígono/Sextil de Plutón Heliocéntrico Trópico (arco real de la semana) con el banco de Fechas "
                 "Gemelas de cada número = favorecido; Cuadratura = negado (a evitar). Ver loteria.py: la base "
                 "real de 900 números de Bonito no está disponible — acá se escanea la lista de números que se "
                 "haya cargado, cada uno con su propia fecha de referencia."),
    }


def loteria_navidad(sorteo_year, sorteo_month, sorteo_day, sorteo_hour, sorteo_minute, sorteo_utc_offset,
                     jd_ventana_ini, jd_ventana_fin, utc_offset_salida,
                     anios_atras=60, anios_adelante=60, orbe=ORBE_PARTIL):
    """Variante 'Lotería de Navidad de España': arma el banco de SOLES de
    Fechas Gemelas del día del sorteo (22/12, 12hs por convención, pero se
    pasa como parámetro) y escanea la ventana [jd_ventana_ini,
    jd_ventana_fin] (la fecha en que se piensa comprar el billete) buscando
    el instante exacto en que el Sol real en tránsito (Geocéntrico Trópico)
    pasa en conjunción PARTIL con algún Sol del banco — el 'momento
    gemelo/análogo' recomendado por Bonito para comprar el billete."""
    from omega import _buscar_conjuncion_en_ventana

    fechas_gemelas = calcular_fechas_gemelas(sorteo_year, sorteo_month, sorteo_day,
                                              sorteo_hour, sorteo_minute, sorteo_utc_offset,
                                              anios_atras=anios_atras, anios_adelante=anios_adelante)
    banco = []
    for variante, lista in fechas_gemelas.items():
        for entrada in lista:
            banco.append({"grado": entrada["sol"]["lon"], "variante": variante, "fecha_origen": entrada["fecha_local"]})

    eventos = []
    for item in banco:
        for jd in _buscar_conjuncion_en_ventana(jd_ventana_ini, jd_ventana_fin, item["grado"], "SOL"):
            eventos.append({
                "hora_local": jd_to_local(jd, utc_offset_salida),
                "grado_banco": round(item["grado"], 5),
                "variante_origen": item["variante"],
                "fecha_origen": item["fecha_origen"],
            })
    eventos.sort(key=lambda e: (e["hora_local"]["year"], e["hora_local"]["month"], e["hora_local"]["day"]))
    return {
        "total_banco": len(banco), "total_eventos": len(eventos), "eventos": eventos,
        "nota": ("Variante Lotería de Navidad de España: conjunción PARTIL del Sol real en tránsito con el banco "
                 "de Soles de Fechas Gemelas del día del sorteo, dentro de la ventana de fechas de compra pedida "
                 "— los días que da son los 'momentos gemelos' recomendados para comprar el billete."),
    }
