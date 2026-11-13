"""
Configuración global y banco de reglas maestras para el Auditor Documental DIGEMID.
Caso Base: Aporte Médico Perú S.A.C. / ACE Medical Devices Pvt. Ltd. (Catéteres Ureterales Doble J).
"""

from pathlib import Path
from typing import Dict, List, Any

# Rutas del entorno local
DEFAULT_TEST_DATA_DIR = Path(r"G:\Mi unidad\PC\APORTE PERU\INFORMACION DISPOSITIVOS\Documentos Cateter")
REPORTS_DIR = Path(__file__).parent / "reports"

# Parámetros Oficiales del Caso Base
BASE_CASE_INFO = {
    "titular": "APORTE MÉDICO PERÚ S.A.C.",
    "ruc_titular": "20610321268",
    "pais_titular": "Perú",
    "fabricante": "ACE Medical Devices Pvt. Ltd.",
    "direccion_planta": "401A, Gera 77, East Avenue, Kalyani Nagar, Pune 411006, India",
    "producto": "Catéteres Ureterales (Doble J / Stent Ureteral y Set)",
    "clasificacion_riesgo": "Clase III (Dispositivo invasivo quirúrgico de uso prolongado/implante)",
    "expedientes_rechazados": ["25039778", "25157794"],
    "resolucion_denegatoria": "R.D. N° 4453-2026",
    "notificacion_oficial": "Notificación N° 2026068505 (13/03/2026)",
}

# Matriz Maestra Dimensional y Clínica Válida
MASTER_SPECIFICATIONS = {
    "valid_diameters_fr": (2.0, 12.0),
    "typical_diameters_fr": (3.0, 8.0),
    "valid_lengths_cm": (6.0, 32.0),
    "invalid_length_infiltrations": [(70.0, 90.0, "Catéter Ureteral simple (no Doble J)")],
    "invalid_diameter_infiltrations": [(8.0, 28.0, "Catéter balón Foley / Urológico")],
    "valid_shelf_life_months": [36, 60],
    "fatal_shelf_life_values": [1 / 30, 0, 1], # 1 día es fatal
    "valid_indwelling_days_short": 25,
    "valid_indwelling_days_max": 90,
    "forbidden_indwelling_days": 180, # 6 meses para poliuretano no es aceptable sin estudio prolongado
    "expected_set_components": [
        "Catéter ureteral Doble J",
        "Guía hidrofílica o PTFE",
        "Empujador / Pusher / Posicionador",
        "Clamp urológico (o pinza)",
        "Hilo de sujeción / Sutura",
    ],
    "forbidden_components": [
        "Umbilical cord clamp", # Abrazadera de cordón umbilical
        "Balón de 3-50 ml",    # Balón de Foley
        "Bottle/grenade type",  # Botella/granada de drenaje quirúrgico
    ],
}

# Catálogo de Normas ISO/EN Derogadas vs Vigentes
STANDARDS_COMPLIANCE_MAP = {
    "ISO 14971:2012": {
        "status": "DEROGADA",
        "vigente": "ISO 14971:2019 / A11:2021",
        "materia": "Gestión del riesgo en dispositivos médicos",
        "norma_peruana": "D.S. 003-2020-SA / D.S. 016-2011-SA",
    },
    "MDD 93/42/EEC": {
        "status": "DEROGADA",
        "vigente": "Reglamento (UE) 2017/745 (EU MDR)",
        "materia": "Directiva de Dispositivos Médicos de la Unión Europea",
        "norma_peruana": "D.S. 016-2011-SA",
    },
    "EN 980:2008": {
        "status": "DEROGADA",
        "vigente": "ISO 15223-1:2021",
        "materia": "Símbolos gráficos para el etiquetado de dispositivos médicos",
        "norma_peruana": "D.S. 016-2011-SA Art. 137°",
    },
    "ISO 13485:2003": {
        "status": "DEROGADA",
        "vigente": "ISO 13485:2016",
        "materia": "Sistemas de gestión de la calidad para dispositivos médicos",
        "norma_peruana": "D.S. 014-2011-SA (BPA / BPM)",
    },
    "ISO 111737": {
        "status": "INEXISTENTE / TYPO",
        "vigente": "ISO 11737-1:2018 (Bioburden) / ISO 11737-2 (Esterilidad)",
        "materia": "Esterilización de productos sanitarios - Métodos microbiológicos",
        "norma_peruana": "D.S. 016-2011-SA Art. 130°",
    },
    "ZSO 9001": {
        "status": "ERROR OCR",
        "vigente": "ISO 9001:2015",
        "materia": "Gestión de Calidad",
        "norma_peruana": "Lectura corrupta",
    },
}

# Catálogo de Traducciones Absurdas y Errores Léxicos
ABSURD_TRANSLATIONS = {
    "no debe mantenerse mora": {
        "origen": "do not delay / not to be kept indwelling",
        "correccion": "No debe mantenerse colocado / tiempo máximo de permanencia",
        "gravedad": "CRITICAL",
    },
    "el doble coleta": {
        "origen": "Double Pigtail",
        "correccion": "Doble J / Doble espiral / Doble cola de cochino",
        "gravedad": "MINOR",
    },
    "de la vegiga": {
        "origen": "of the bladder",
        "correccion": "de la vejiga (falta ortográfica con 'g')",
        "gravedad": "MINOR",
    },
    "el gato no.": {
        "origen": "Cat. No. (Catalogue Number)",
        "correccion": "N° de Catálogo / Código de Producto",
        "gravedad": "MINOR",
    },
    "el gato nº": {
        "origen": "Cat. Nº (Catalogue Number)",
        "correccion": "N° de Catálogo / Código de Producto",
        "gravedad": "MINOR",
    },
    "por el tubo": {
        "origen": "Per tube",
        "correccion": "Por tubo / Por unidad",
        "gravedad": "MINOR",
    },
    "pelar las juntas": {
        "origen": "peel pouches / seal peeling",
        "correccion": "apertura o pelado de sellos del blíster/empaque",
        "gravedad": "MINOR",
    },
    "sacudidas de calor": {
        "origen": "heat shocks / thermal shock",
        "correccion": "estrés térmico / choque térmico",
        "gravedad": "MINOR",
    },
    "taction": {
        "origen": "traction",
        "correccion": "tracción (resistencia a la tracción)",
        "gravedad": "MINOR",
    },
    "ifi": {
        "origen": "orifices",
        "correccion": "orificios laterales de drenaje (texto truncado por OCR)",
        "gravedad": "MINOR",
    },
    "silicon stents": {
        "origen": "silicon (elemento silicio) vs silicone (silicona)",
        "correccion": "Silicone Stents (Stents de silicona médica)",
        "gravedad": "MINOR",
    },
    "columbia": {
        "origen": "Columbia (distrito/marca) vs Colombia (país)",
        "correccion": "Colombia",
        "gravedad": "CRITICAL",
    },
}

# Referencias Normativas de DIGEMID
DIGEMID_LEGAL_FRAMEWORK = {
    "DS_016_2011_SA_ART_130": {
        "articulo": "D.S. 016-2011-SA, Artículo 130°",
        "descripcion": "Requisitos técnicos para inscripción de dispositivos médicos Clase III: Informe Técnico detallado, materias primas, estudios de estabilidad, validación de esterilización, flujograma con descripción resumida de etapas.",
    },
    "DS_016_2011_SA_ART_126": {
        "articulo": "D.S. 016-2011-SA, Artículo 126°",
        "descripcion": "Carta de Autorización del Fabricante detallando facultades, modelos, códigos y concordancia íntegra con el Certificado de Libre Venta (CLV).",
    },
    "DS_003_2020_SA": {
        "articulo": "D.S. 003-2020-SA",
        "descripcion": "Principios Esenciales de Seguridad y Desempeño (GSPR) para dispositivos médicos en Perú, alineado a directrices IMDRF/GHTF.",
    },
    "DS_014_2011_SA": {
        "articulo": "D.S. 014-2011-SA",
        "descripcion": "Reglamento de Establecimientos Farmacéuticos: BPA, horario de permanencia de Dirección Técnica y trazabilidad de almacenamiento.",
    },
    "LEY_29459": {
        "articulo": "Ley N° 29459, Arts. 5°, 8°, 10°, 12°, 44°-52°",
        "descripcion": "Ley de Productos Farmacéuticos, Dispositivos Médicos y Productos Sanitarios. Responsabilidad objetiva y veracidad documental.",
    },
    "LEY_27444_ART_34": {
        "articulo": "TUO Ley N° 27444, Art. 34° y Código Penal Arts. 411° y 427°",
        "descripcion": "Privilegio de controles posteriores y fiscalización: Prohibición expresa de adulteración, montaje de firmas o alteración de fechas en informes oficiales.",
    },
}
