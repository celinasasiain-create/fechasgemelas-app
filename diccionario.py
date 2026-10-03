# -*- coding: utf-8 -*-
"""
Diccionario interpretativo — Técnica de las Fechas Gemelas (Hugo Bonito).

IMPORTANTE: esto NO es un diccionario exhaustivo palabra por palabra de
cada combinación posible de planeta/aspecto. Es lo que quedó efectivamente
documentado y verificable a partir de las 30 clases: (a) el marco general
de qué significa cada punto, y (b) marcadores puntuales muy específicos que
Bonito dio con ejemplos concretos (orbe, aspecto y lectura exacta). Para
todo lo que no está en MARCADORES_ESPECIFICOS, la función interpretar()
devuelve la lectura general del punto (categoría), no un texto inventado
para esa combinación particular — así no se le atribuye a Bonito algo que
no dijo. Este archivo está pensado para crecer con el tiempo, a medida que
se van formalizando más clases.

Se excluye deliberadamente cualquier contenido que Bonito presentó como
opinión personal/anecdótico no confirmado (p. ej. generalizaciones de
género sobre infidelidad) — se deja anotado en el marcador pero no se
convierte en regla determinística.
"""

CATEGORIA_PUNTO = {
    "sol": "Personalidad y destino — la lectura más cercana a un aspecto natal clásico: describe quién sos estructuralmente.",
    "luna": "Área laboral/vocacional — actitud frente al trabajo y la vocación, no personalidad.",
    "ascendente": "El 'camino' — el objetivo de vida hacia el que te dirigís.",
    "ecuador_celeste": "El 'camino' — equivalente al Ascendente para este propósito.",
    "mc": "'Necesidad' del punto (no necesariamente positiva); en oposición (casa 4) describe a la familia de origen/hogar.",
    "vertex": "Equivalente al MC para esta lectura.",
    "rueda_de_la_fortuna": "Equivalente a MC/Vértex para esta lectura.",
    "proluna": "Disponibilidad/habilitación MOMENTÁNEA de esa energía ese día — no es rasgo de personalidad.",
}

PUNTOS_PERSONALES = {
    "sol", "luna", "mercurio", "venus", "ascendente", "ecuador_celeste",
    "mc", "vertex", "rueda_de_la_fortuna",
}

# Equivalencia signo <-> planeta regente, usada sistemáticamente en el
# diccionario de Bonito para leer con velocidad.
REGENTE_DE_SIGNO = {
    "Aries": "Marte", "Tauro": "Venus", "Géminis": "Mercurio", "Cáncer": "Luna",
    "Leo": "Sol", "Virgo": "Quirón", "Libra": "Venus", "Escorpio": "Plutón",
    "Sagitario": "Júpiter", "Capricornio": "Saturno", "Acuario": "Urano", "Piscis": "Neptuno",
}

ASPECTOS_DE_15 = {"Semisextil", "Quincuncio"}  # + 75°/105°/165°, no está en ASPECTOS base todavía


def _par(a, b):
    return frozenset((a, b))


# Cada marcador: puntos = frozenset de los dos puntos involucrados,
# aspecto = nombre exacto o None (cualquiera), orbe_max = grados,
# texto = la lectura, fuente = clase de origen, confianza = 'marcador'
# (dato concreto dado por Bonito) o 'observación personal no confirmada'
# (para que la app pueda decidir si mostrarlo o no).
MARCADORES_ESPECIFICOS = [
    {
        "puntos": _par("ascendente", "saturno"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Complicaciones de parto.",
        "fuente": "Clase 24A/B", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "marte"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Riesgo de cirugía a lo largo de la vida.",
        "fuente": "Clase 24A/B", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "neptuno"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Infidelidad.",
        "fuente": "Clase 24A/B", "confianza": "observación personal no confirmada",
        "nota": "Bonito agrega una distinción de género (sufrida/proyectada) que no está confirmada ni se codifica como regla.",
    },
    {
        "puntos": _par("ascendente", "plutón"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Destino 'importante'; sexto sentido extremo. (También asociado a Ascendente en Escorpio.)",
        "fuente": "Clase 24A/B", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "mc"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Pérdida del abuelo en el primer año de vida, o ausencia paterna.",
        "fuente": "Clase 27B", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "vertex"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Pérdida del abuelo en el primer año de vida, o ausencia paterna. (MC y Vértex se leen como equivalentes.)",
        "fuente": "Clase 27B", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "luna"), "aspecto": "Conjunción", "orbe_max": 5.0 / 60.0,
        "texto": "Extremadamente compleja para la salud.",
        "fuente": "Clase 23-24", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "luna"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Alta probabilidad de terapia psicológica por pérdida afectiva.",
        "fuente": "Clase 23-24", "confianza": "marcador",
    },
    {
        "puntos": _par("proluna", "ascendente"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "\"El enemigo\": conexión con la persona o situación equivocada ese día; camino equivocado, de corta duración.",
        "fuente": "Técnica de Contacto / Proluna-eventos", "confianza": "marcador",
    },
    {
        "puntos": _par("proluna", "mc"), "aspecto": None, "orbe_max": 1.0,
        "texto": "En aspecto adverso: viajes o problemas íntimos/familiares puntuales de ese día.",
        "fuente": "Técnica de Contacto / Proluna-eventos", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "marte"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Necesidad relacionada con Marte — posible anemia.",
        "fuente": "Clase 27B", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "neptuno"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Necesidad de protección/terapia.",
        "fuente": "Clase 27B", "confianza": "marcador",
    },

    # ------------------------------------------------------------------
    # Catálogo de Medio Cielo (MC) — fuente: 1675af50-attachment.txt
    # (Vértex se lee como equivalente al MC en todo este bloque; los
    # marcadores se duplican para ambos puntos donde Bonito lo aclara.)
    # ------------------------------------------------------------------
    {
        "puntos": _par("mc", "marte"), "aspecto": None, "orbe_max": 1.0,
        "texto": ("Conjunción: proyectos independientes/iniciativas propias; vigilar anemia/hierro en sangre "
                  "bajo. Oposición (Marte en casa 4): hogar poco tranquilo, padre autoritario, hijos "
                  "deportistas/enérgicos, riesgo de incendio (conviene seguro de hogar), posible taller/fábrica "
                  "en la casa."),
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "neptuno"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Mal momento familiar en el nacimiento (padres pasando mal momento, embarazo no querido o mal momento económico).",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "neptuno"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Familia con persona mística/vidente/curandera; altares/velas en la casa (muy común en gente de campo, casas antiguas con humedad).",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "mercurio"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": ("Sentido común, memoria, reflexión, inteligencia; vínculo con viajes, números, música, "
                   "hijos, comunicación, pedagogía. (Mercurio y Venus opuestos al MC, junto con Sol/Nodo/"
                   "Marte/Luna, casi garantizan descendencia — Mercurio es el de mayor potencial en ese "
                   "sentido; su AUSENCIA en fechas gemelas se asocia a pérdida de hijos, poca descendencia o "
                   "hijo único.)"),
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "mercurio"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Familia con tendencia intelectual; \"biblioteca en casa no falla nunca\".",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "mercurio"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Dificultades de entendimiento entre hermanos, mala comunicación familiar.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "venus"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Ayuda del área femenina; arte/artesanía/hobbies.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "venus"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": ("Hogar bonito y armonioso; hijos \"muy bonitos\" (sexo femenino predominante, aunque no es "
                   "tan puntual); posibles profesiones de los hijos: arquitecto, odontólogo, moda, salón de "
                   "belleza. (Su AUSENCIA se asocia a desencuentros familiares, comúnmente entre hermanos, "
                   "madre-hija, o con tíos/primos.)"),
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "mc"), "aspecto": None, "orbe_max": 1.0,
        "texto": ("En casa 4 (oposición): la persona nunca se va del lugar de nacimiento (arraigo forzado, "
                   "aunque le hubiera ido mejor en otro lugar); el desafío es la familia. En cuadratura (dentro "
                   "de 1° de orbe): coincide con pérdida de un abuelo antes del año de vida, separación de los "
                   "padres antes de cumplir un año, o embarazo no deseado en su momento — Bonito recomienda "
                   "evitar este aspecto en las revoluciones solares."),
        "fuente": "1675af50-attachment.txt / Clase 27B", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "mc"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Menos grave que el mismo aspecto con el Sol; indica muchas mudanzas, rechazo al ritmo/horarios estrictos, impuntualidad.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "mc"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Familia numerosa (antes 5-8 hermanos, hoy 3-4 hijos); trabajo en lugares con mucha gente (banco, municipalidad, empresas grandes).",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "quirón"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "\"Lo salva el médico\": indica necesidad médica en algún momento de la vida.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "quirón"), "aspecto": None, "orbe_max": 1.0,
        "texto": "Ausencia de Quirón con el MC: pérdida en algún momento laboral, inmobiliario o familiar.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "júpiter"), "aspecto": None, "orbe_max": 1.0,
        "texto": ("Destino importante, factor suerte, contactos poderosos, padrinazgos, cargos gerenciales. "
                   "En cuadratura: familia o entorno laboral con personas \"cretinas\" (injustas, egoístas) "
                   "aunque de perjuicio menor al aparente. Su ausencia sugiere evitar confrontación legal."),
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "plutón"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Vive en casa patrimonialmente importante, country o barrio exclusivo.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "plutón"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Junto a necesidad legal: casi indefectiblemente ligado a juicios/tribunales.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "urano"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Familia independiente, fuera de normas; favorece economía y patrimonio inmobiliario. Medios de difusión, internet, telefonía, terapias alternativas, viajes.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "urano"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Situaciones inesperadas, cambio de un día para el otro (posible fallecimiento que cambia la vida del nativo, o mudanza repentina); su ausencia es peor que la de Saturno (sensación de \"víctima de las circunstancias\").",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "saturno"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Vejez tranquila, reconocimiento laboral, jubilación con rentabilidad — muy positivo en conjunción.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "saturno"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Padres serios/poco demostrativos, casa con poca luz/fría; en el mejor caso, abuela/o importante que vivió con el niño; también limitaciones económicas de los padres.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "saturno"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Persona desapegada, se va joven de la familia/ciudad/país (relacionado con emigración); dificulta el patrimonio.",
        "fuente": "1675af50-attachment.txt", "confianza": "marcador",
    },

    # ------------------------------------------------------------------
    # Catálogo de Ascendente / Ecuador Celeste — fuente: b1ee12f6-attachment.txt
    # ------------------------------------------------------------------
    {
        "puntos": _par("ascendente", "sol"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "La persona se va a vivir lejos del lugar de nacimiento — regla fuerte (\"si la hora está bien rectificada y dentro de un grado, no falla jamás\").",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "venus"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Gusto elitista, exigencia estética en la pareja.",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "saturno"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Pérdida familiar por muerte.",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "urano"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Independencia extrema, tecnología, viajes.",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "urano"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Pérdida de libertad.",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "urano"), "aspecto": "Oposición", "orbe_max": 1.0,
        "texto": "Riesgo poco común (Bonito cita un caso de un niño fallecido electrocutado con este aspecto en casa 7).",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("ascendente", "plutón"), "aspecto": "Conjunción", "orbe_max": 1.0,
        "texto": "Sexto sentido fuerte, destino \"trascendente\", contacto con gente/países poderosos (asociado también a Ascendente en Sagitario o Escorpio).",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "ascendente"), "aspecto": "Cuadratura", "orbe_max": 1.0,
        "texto": "Sedentarismo, poca necesidad de familia, buena vista a distancia pero problemas de lectura desde los 30 y pico de años, actitud compulsiva al trabajo (ejemplo propio de Bonito).",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "ascendente"), "aspecto": "Trígono", "orbe_max": 1.0,
        "texto": "Vitalidad y buena salud (Bonito cita el caso de una persona longeva, 90 y pico de años).",
        "fuente": "b1ee12f6-attachment.txt", "confianza": "marcador",
    },

    # ------------------------------------------------------------------
    # Catálogo Luna-planetas por ACTIVIDAD/TRABAJO (distinto de Sol =
    # personalidad) — fuente: 281bd679-attachment.txt
    # ------------------------------------------------------------------
    {
        "puntos": _par("luna", "mercurio"), "aspecto": None, "orbe_max": 3.0,
        "texto": ("Buen aspecto: expresión oral, memoria, docencia, ventas, comercio, viajes. Cuadratura: "
                   "dificultad de concentración/vocabulario, \"vacíos\" mentales (empeora después de los 50 "
                   "años). Semisextil/quincuncio: desorden, ambigüedad, dos caminos que compiten (dispersión "
                   "de intereses)."),
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "venus"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Buen aspecto: actividades estéticas/artísticas, buen gusto. Mal aspecto: dificultad para cobrar/generar dinero, reacciones desagradables en el trabajo.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "marte"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Buen aspecto: trabajador compulsivo, gran constancia y ritmo. Cuadratura: persona \"alargada\"/pasiva en el trabajo.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "júpiter"), "aspecto": "Conjunción", "orbe_max": 3.0,
        "texto": "Experiencias anímicas/mediúmnicas particulares, sensibilidad/corazonada aumentada — pero también \"peligrosa\" en tránsito (situaciones sociales desagradables en público).",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "júpiter"), "aspecto": "Trígono", "orbe_max": 3.0,
        "texto": "Gran capacidad de trabajo en proyectos grandes, progreso constante.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "saturno"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Buen aspecto: capacidad de planificación, orden, tareas administrativas/manuales, perseverancia. Mal aspecto (cuadratura/semicuadratura): trabajo absorbente y agotador, sacrificio para ganar dinero.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "urano"), "aspecto": None, "orbe_max": 3.0,
        "texto": ("Buen aspecto (sextil/trígono cerrado): éxito mediático (radio, TV, artistas), espontaneidad "
                   "y magnetismo. Mal aspecto: ansiedad laboral, cambia constantemente de trabajo, "
                   "insatisfacción prolongada; también asociado a mala relación con la madre."),
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "neptuno"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Buen aspecto: actividades humanísticas (psicólogo, psiquiatra), percepción/empatía innata. Mal aspecto: personas que \"parecen tontas\" (no lo son), credulidad, trabajo estresante con desgaste físico/anímico, temperamento pausado e ingenuo.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "plutón"), "aspecto": "Conjunción", "orbe_max": 3.0,
        "texto": "Personas que escalan puestos, terminan como \"mano derecha\" del líder/gerente.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "plutón"), "aspecto": "Cuadratura", "orbe_max": 3.0,
        "texto": "No fracaso, pero tiempo perdido, sensación de estar desaprovechado (\"el ingeniero que maneja un taxi\").",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "quirón"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Actividades culturales vinculadas a medicina/salud — \"muchas enfermeras\" (según observación de Bonito).",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("luna", "nodo"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Relación con madre longeva, trabajo para toda la vida; posible actividad de intermediario.",
        "fuente": "281bd679-attachment.txt", "confianza": "marcador",
    },

    # ------------------------------------------------------------------
    # Catálogo Sol-planetas (personalidad/destino) — fuente:
    # cf3e1cc9-attachment.txt
    # ------------------------------------------------------------------
    {
        "puntos": _par("sol", "luna"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Armonioso: extroversión, buen carácter, éxito laboral relacionado con la personalidad. Adverso: introversión, padres posiblemente separados, altibajos anímicos.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "mercurio"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: comunicación, viajes, estudios. Malo: dificultad de concentración, terciario incompleto.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "venus"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: afable, atractivo, dinero fácil. Malo: baja autoestima (Bonito sugiere terapia).",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "marte"), "aspecto": None, "orbe_max": 3.0,
        "texto": ("Bueno: médicos exitosos, energía, decisión. Malo: temperamento explosivo pero pasajero, no "
                   "rencoroso (el rencor aparece con Marte+Saturno juntos negativos); posibles molestias "
                   "físicas no graves (meniscos, hemorroides, acidez)."),
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "júpiter"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: protección, generosidad, situaciones afortunadas. Malo: transgresión legal (ej. matrimonios no formalizados civilmente); con Saturno adverso, problemas dentales/óseos, bajas defensas.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "saturno"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: seriedad, responsabilidad, éxito material (no necesariamente felicidad). Conjunción: preocupación por la figura paterna, autoboicot.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "neptuno"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: piedad, humanitarismo, tranquilidad interna. Malo: susceptibilidad emocional (Bonito aclara explícitamente que NO debe leerse como \"suicida o alcohólico\", como hacía la astrología antigua).",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "plutón"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: liderazgo, seguridad, trascendencia social. Malo: retraimiento, dificultad para trascender.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "urano"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: elocuencia, ingenio, simpatía, ventas. Malo: impaciencia, reacciones imprevisibles.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "quirón"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Cultura/conocimiento fuera de lo común; cuadratura: posible relación compleja con la figura materna (Bonito declara poca experiencia con este marcador).",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "observación personal no confirmada",
    },
    {
        "puntos": _par("sol", "luna_negra"), "aspecto": "Conjunción", "orbe_max": 3.0,
        "texto": "Lectura negativa (Luna Negra: foco invisible de la elipse lunar, asociada a lo oculto/secreto/sexualidad).",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "luna_negra"), "aspecto": "Trígono", "orbe_max": 3.0,
        "texto": "Revitalización.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "luna_negra"), "aspecto": "Cuadratura", "orbe_max": 3.0,
        "texto": "No ayuda a la vida afectiva.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("mc", "luna_negra"), "aspecto": "Oposición", "orbe_max": 3.0,
        "texto": "Familia con secretos/intimidad compleja.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
    {
        "puntos": _par("sol", "nodo"), "aspecto": None, "orbe_max": 3.0,
        "texto": "Bueno: futuro asegurado, padre longevo, persona conciliadora. Malo (oposición = nodo sur): destino difícil con figuras masculinas.",
        "fuente": "cf3e1cc9-attachment.txt", "confianza": "marcador",
    },
]


def interpretar(puntoA, puntoB, aspecto, orbe):
    """Devuelve una lista de lecturas aplicables a un aspecto entre dos
    puntos: primero cualquier marcador específico documentado, y si no hay
    ninguno, la lectura general de categoría de cada punto involucrado."""
    par = _par(puntoA, puntoB)
    especificos = []
    for m in MARCADORES_ESPECIFICOS:
        if m["puntos"] != par:
            continue
        if m["aspecto"] is not None and m["aspecto"] != aspecto:
            continue
        if orbe > m["orbe_max"]:
            continue
        especificos.append(m)

    if especificos:
        limpios = [{k: v for k, v in m.items() if k != "puntos"} for m in especificos]
        return {"tipo": "marcador_especifico", "resultados": limpios}

    generales = []
    for p in (puntoA, puntoB):
        if p in CATEGORIA_PUNTO:
            generales.append({"punto": p, "lectura_general": CATEGORIA_PUNTO[p]})
    return {"tipo": "lectura_general", "resultados": generales}
