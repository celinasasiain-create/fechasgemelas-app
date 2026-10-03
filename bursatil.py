# -*- coding: utf-8 -*-
"""
Programa Omega — variante bursátil (pronóstico de tendencia de mercado).

Fuente: 0cb35a23-attachment.txt (transcripción de clase, ~538 líneas),
resumida en revision_batch0.md entrada 4, y el material gráfico asociado
(graficobursatil.txt + imagen b4281d11, IBEX 35 nov. 2011) en
revision_omega_imagenes.md.

TÉCNICA (tal como la describe Bonito): los aspectos REALES que van
formando entre sí los cuatro planetas lentos — Saturno, Urano, Neptuno y
Plutón — en sus posiciones HELIOCÉNTRICAS (Trópicas y Sidérales
Fagan-Bradley), acompañan las subas y bajadas del mercado bursátil. Usa
solo los aspectos "menores/de fricción o ajuste": 45° (semicuadratura),
60° (sextil), 90° (cuadratura), 120° (trígono) y 135° (sesquicuadratura)
— EXCLUYE explícitamente la conjunción (0°) y la oposición (180°), que
Bonito no contempla para esta técnica en particular. Caso real verificado
por Bonito: cuadratura Saturno-Neptuno (1/oct/2011) y la secuencia de
aspectos entre planetas lentos durante oct-dic 2011 correlacionada con los
altibajos reales del IBEX 35 (bolsa de Madrid); y, a mayor escala, la
cuadratura Plutón-Urano de 2012-2014 como indicio de una caída general
prolongada del mercado.

RECONSTRUCCIÓN HONESTA — lo que se simplifica: el procedimiento original
(Winstar + Excel + Omega) sorteaba una limitación del software de la
época: Omega no podía escanear una efeméride continua, así que Bonito
tomaba varias fechas gemelas de cada planeta (carta base + retornos
heliocéntricos adelante/atrás, "10 posiciones por planeta") como una
muestra discreta de posiciones, las exportaba a Excel y las cruzaba a
mano. Acá, con Swiss Ephemeris disponible, se escanea la efeméride REAL y
CONTINUA de los 4 planetas lentos dentro del rango de fechas pedido,
encontrando el instante EXACTO de cada aspecto por bisección (mismo
patrón que el resto del proyecto) — el rodeo de "10 posiciones por
planeta" era la limitación de 2011, no parte de la técnica astrológica en
sí. El paso de búsqueda es de 1 día (los 4 cuerpos son lentos y su
separación angular avanza de forma suave dentro de ese margen).
"""
from astro import cuerpo_base_lon, jd_to_local, _diff_angular

PLANETAS_LENTOS = ["SATURNO", "URANO", "NEPTUNO", "PLUTON"]
ASPECTOS_BURSATIL = {
    "Semicuadratura": 45, "Sextil": 60, "Cuadratura": 90,
    "Trígono": 120, "Sesquicuadratura": 135,
}
PARES_PLANETAS = [(a, b) for i, a in enumerate(PLANETAS_LENTOS) for b in PLANETAS_LENTOS[i + 1:]]


def _lon(jd, cuerpo, sideral):
    lon, _ = cuerpo_base_lon(jd, cuerpo, helio=True, sideral=sideral)
    return lon


def _separacion(jd, cuerpoA, cuerpoB, sideral):
    return abs(_diff_angular(_lon(jd, cuerpoA, sideral), _lon(jd, cuerpoB, sideral)))


def _buscar_aspectos_par(cuerpoA, cuerpoB, sideral, jd_ini, jd_fin, paso_dias=1.0):
    """Busca, por bisección, todos los instantes exactos dentro de
    [jd_ini, jd_fin] en que la separación angular heliocéntrica entre
    cuerpoA y cuerpoB (Trópica o Sideral según 'sideral') cruza alguno de
    los 5 aspectos bursátiles."""
    EPS = 1e-4
    resultados = []
    jd = jd_ini
    prev = _separacion(jd, cuerpoA, cuerpoB, sideral)
    while jd < jd_fin:
        jd_next = min(jd + paso_dias, jd_fin)
        curr = _separacion(jd_next, cuerpoA, cuerpoB, sideral)
        for nombre_asp, angulo in ASPECTOS_BURSATIL.items():
            if (prev - angulo > 0) != (curr - angulo > 0):
                lo, hi = jd, jd_next
                dlo = prev - angulo
                for _ in range(40):
                    mid = (lo + hi) / 2
                    dmid = _separacion(mid, cuerpoA, cuerpoB, sideral) - angulo
                    if (dmid > 0) == (dlo > 0):
                        lo, dlo = mid, dmid
                    else:
                        hi = mid
                raiz = (lo + hi) / 2
                if abs(_separacion(raiz, cuerpoA, cuerpoB, sideral) - angulo) < EPS:
                    resultados.append({"jd": raiz, "aspecto": nombre_asp, "angulo": angulo})
        prev, jd = curr, jd_next
    return resultados


def escanear_bursatil(jd_ini, jd_fin, utc_offset_salida, sideral=False, paso_dias=1.0):
    """Escanea, para los 6 pares posibles entre Saturno/Urano/Neptuno/
    Plutón heliocéntricos (Trópico o Sideral Fagan-Bradley según
    'sideral'), todos los instantes exactos de aspecto (45/60/90/120/135°)
    dentro de [jd_ini, jd_fin] — la secuencia cronológica resultante es la
    que Bonito correlaciona con los giros de tendencia del mercado."""
    eventos = []
    for cuerpoA, cuerpoB in PARES_PLANETAS:
        for hit in _buscar_aspectos_par(cuerpoA, cuerpoB, sideral, jd_ini, jd_fin, paso_dias):
            eventos.append({
                "fecha_local": jd_to_local(hit["jd"], utc_offset_salida),
                "par": f"{cuerpoA.capitalize()} - {cuerpoB.capitalize()}",
                "aspecto": hit["aspecto"], "angulo": hit["angulo"],
            })
    eventos.sort(key=lambda e: (e["fecha_local"]["year"], e["fecha_local"]["month"], e["fecha_local"]["day"],
                                 e["fecha_local"]["hour"], e["fecha_local"]["minute"]))
    return {
        "total_eventos": len(eventos),
        "eventos": eventos,
        "modo": "Heliocéntrico Sideral (Fagan-Bradley)" if sideral else "Heliocéntrico Trópico",
        "nota": ("Técnica bursátil de Bonito: aspectos reales (45/60/90/120/135°, sin conjunción ni oposición) "
                 "entre los 4 planetas lentos (Saturno, Urano, Neptuno, Plutón) Heliocéntricos — la secuencia "
                 "cronológica de estos instantes es la que él correlaciona con los giros de tendencia del "
                 "mercado (verificado por él contra el IBEX 35, oct-dic 2011). No agrega interpretación "
                 "alcista/bajista automática — esa lectura la hace Bonito caso a caso comparando contra el "
                 "gráfico real del índice."),
    }
