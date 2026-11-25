"""
Configuración global, perfiles de dispositivos médicos y marco regulatorio DIGEMID.
Soporte UNIVERSAL para cualquier dispositivo médico o producto sanitario (Clases I, II, III, IV).
"""

from pathlib import Path
from typing import Dict, List, Any

# Rutas del entorno local
DEFAULT_TEST_DATA_DIR = Path(r"G:\Mi unidad\PC\APORTE PERU\INFORMACION DISPOSITIVOS\Documentos Cateter")
VAGINAL_SLING_DATA_DIR = Path(r"G:\Mi unidad\PC\APORTE PERU\INFORMACION DISPOSITIVOS\Documentos Cinta Vaginal de libre tensión")
REPORTS_DIR = Path(__file__).parent / "reports"

# Parámetros Oficiales del Titular Solicitante por Defecto
BASE_CASE_INFO = {
    "titular": "APORTE MÉDICO PERÚ S.A.C.",
    "ruc_titular": "20610321268",
    "pais_titular": "Perú",
    "direccion_titular": "Lima, Perú",
    "fabricante": "ACE Medical Devices Pvt. Ltd. / Orion Surgichem",
    "producto": "Dispositivo Médico para Registro Sanitario DIGEMID",
    "clasificacion_riesgo": "Clase I, II, III o IV según D.S. 016-2011-SA",
}

# Familias de Productos Médicos Regulados ante DIGEMID (Catálogo completo Aporte Médico / urotienda.com)
PRODUCT_FAMILIES = {
    "UNIVERSAL": {
        "nombre": "🎯 Detección Automática Universal (Cualquier Dispositivo DIGEMID)",
        "descripcion": "Identifica automáticamente el dispositivo médico del expediente y aplica las reglas transversales y específicas del D.S. 016-2011-SA para Clases I, IIa, IIb, III y IV.",
        "clase_defecto": "Clase I / IIa / IIb / III / IV",
        "norma_base": "D.S. 016-2011-SA Arts. 126°, 128°, 129°, 130°, 137°",
    },
    "URETERAL_STENTS": {
        "nombre": "Catéteres y Stents Urológicos (Doble J, Mono J, Sets)",
        "descripcion": "Dispositivos invasivos urológicos de drenaje interno (Clase III). Valida rangos 2–12 Fr / 6–32 cm, exclusión de 70–90 cm, EO SAL 10^-6, permanencia y 5 componentes del Set.",
        "clase_defecto": "Clase III",
        "unidades_esperadas": ["Fr", "cm"],
        "rango_fr_tipico": (2.0, 12.0),
        "rango_cm_tipico": (6.0, 32.0),
        "longitudes_prohibidas": [(70.0, 90.0, "Catéter Ureteral simple (no Doble J)")],
        "materiales": ["Poliuretano", "Silicona"],
        "vida_util_esperada": [36, 60],
        "norma_base": "Art. 130° D.S. 016-2011-SA / ISO 11135 / ISO 10993",
    },
    "VAGINAL_SLINGS_MESHES": {
        "nombre": "Cintas Vaginales (TOT / TVT) y Mallas Quirúrgicas Pélvicas",
        "descripcion": "Implantes permanentes de suspensión de polipropileno monofilamento macroporoso para incontinencia urinaria y prolapso (Clase III). Valida dimensiones en cm/mm, densidad g/m2, agujas Gauge y biocompatibilidad crónica.",
        "clase_defecto": "Clase III (Implante Permanente)",
        "unidades_esperadas": ["cm x cm", "mm x mm", "g/m2", "Gauge"],
        "materiales": ["Polipropileno monofilamento macroporoso"],
        "tiempo_permanencia_tipico": "Permanente (> 30 días / implante definitivo)",
        "vida_util_esperada": [36, 60],
        "norma_base": "Art. 130° D.S. 016-2011-SA / ISO 10993 completos",
    },
    "NITINOL_BASKETS_ACCESS": {
        "nombre": "Canastillas de Nitinol (3/4 hilos) y Camisas de Acceso Ureteral",
        "descripcion": "Dispositivos endourológicos para extracción de cálculos y acceso ureteral (Clase IIa / IIb / III). Valida longitudes de trabajo (45–120 cm), calibres Fr, resistencia a la tracción y recubrimiento hidrofílico/PTFE.",
        "clase_defecto": "Clase IIb / III",
        "unidades_esperadas": ["Fr", "cm longitud de trabajo (45-120 cm)", "hilos (3 o 4)"],
        "materiales": ["Nitinol (Níquel-Titanio)", "PTFE", "Poliamida", "Acero Inoxidable"],
        "norma_base": "Art. 129° / 130° D.S. 016-2011-SA / ISO 11135",
    },
    "ELECTROSURGICAL_LOOPS": {
        "nombre": "Asas de Corte Monopolares/Bipolares y Electrodos (Storz, Wolf, Olympus)",
        "descripcion": "Electrodos activos quirúrgicos de alta frecuencia para resección endoscópica TURP/TURBT (Clase IIb / III). Valida compatibilidad de marca, seguridad eléctrica IEC 60601-2-2, aislamiento dieléctrico y advertencias de electrocirugía.",
        "clase_defecto": "Clase IIb / III (Activo Quirúrgico)",
        "unidades_esperadas": ["Fr (24-27 Fr)", "mm", "grados ángulo"],
        "materiales": ["Tungsteno", "Acero inoxidable", "Aislamiento cerámico/PTFE"],
        "norma_base": "Art. 129° / 130° D.S. 016-2011-SA / IEC 60601-1 / IEC 60601-2-2",
    },
    "REUSABLE_INSTRUMENTS": {
        "nombre": "Conductores Uretrales Metálicos e Instrumental Reutilizable",
        "descripcion": "Instrumental quirúrgico metálico reutilizable en acero inoxidable (Clase I / IIa). Valida instrucciones de limpieza, desinfección y reesterilización en autoclave (ISO 17664 / ISO 17665) y consistencia No Estéril / Reutilizable.",
        "clase_defecto": "Clase I / IIa (Reutilizable)",
        "unidades_esperadas": ["Fr", "cm", "ciclos de esterilización"],
        "materiales": ["Acero Inoxidable grado quirúrgico (AISI 316L / 304)"],
        "norma_base": "Art. 128° / 129° D.S. 016-2011-SA / ISO 17664-1 / ISO 7153-1",
    },
    "NON_INVASIVE_INCONTINENCE": {
        "nombre": "Uroclamp® y Dispositivos No Quirúrgicos (Uicop® Mujer / Kids)",
        "descripcion": "Dispositivos externos de control de incontinencia masculina (pinza anatómica reutilizable tipo Cunningham) y accesorios higiénicos femeninos (Clase I). Valida condición No Estéril, biocompatibilidad cutánea ISO 10993-5/-10 e instrucciones de lavado/uso en español.",
        "clase_defecto": "Clase I (No Invasivo)",
        "unidades_esperadas": ["Tallas (S/M/L)", "mm", "horas de uso continuo"],
        "materiales": ["Silicona médica", "Polímero libre de látex", "Celulosa sanitaria"],
        "norma_base": "Art. 128° y 137° D.S. 016-2011-SA / ISO 10993-5/-10",
    },
    "PELVIC_REHAB_ACTIVE": {
        "nombre": "Rehabilitadores de Piso Pélvico (KM 526 / Electroestimuladores)",
        "descripcion": "Equipos biomédicos activos terapéuticos de electroestimulación neuromuscular y biofeedback con sondas intracavitarias (Clase IIa / IIb). Exige IEC 60601-1, EMC IEC 60601-1-2, manual en español y contraindicaciones (marcapasos/embarazo).",
        "clase_defecto": "Clase IIa / IIb (Equipo Biomédico Activo)",
        "unidades_esperadas": ["Hz", "mA", "µs", "Voltios"],
        "materiales": ["ABS grado médico", "Acero inoxidable (electrodos)", "Silicona médica (sonda)"],
        "norma_base": "Art. 129° y 137° D.S. 016-2011-SA / IEC 60601-1 / IEC 60601-1-2",
    },
    "PELVIC_REHAB_WEIGHTS": {
        "nombre": "Pesas Íntimas / Conos Vaginales y Pesarios Ginecológicos",
        "descripcion": "Dispositivos invasivos temporales por orificio corporal para rehabilitación del suelo pélvico y soporte de prolapso (Clase I / IIa). Valida pesos en gramos (g), tallas en mm, silicona USP Class VI / ISO 10993-5/-10 e instrucciones de higiene ISO 17664.",
        "clase_defecto": "Clase I / IIa (Invasivo por orificio corporal)",
        "unidades_esperadas": ["gramos (g)", "mm diámetro", "horas/día"],
        "materiales": ["Silicona grado médico", "Elastómero libre de ftalatos y látex"],
        "norma_base": "Art. 128° / 129° y 137° D.S. 016-2011-SA / ISO 10993-10",
    },
    "IV_CATHETERS_INFUSION": {
        "nombre": "Catéteres Intravenosos, Equipos de Venoclisis y Cánulas",
        "descripcion": "Dispositivos de acceso vascular y terapia de infusión (Clase IIa / IIb).",
        "clase_defecto": "Clase IIa / IIb",
        "unidades_esperadas": ["Gauge (G)", "mm", "ml/min"],
        "materiales": ["FEP", "Poliuretano", "PVC grado médico libre de DEHP"],
        "norma_base": "Art. 129° D.S. 016-2011-SA",
    },
    "SURGICAL_SUTURES": {
        "nombre": "Suturas Quirúrgicas e Implantes de Fijación",
        "descripcion": "Material de sutura absorbible y no absorbible (Clase IIb / III).",
        "clase_defecto": "Clase IIb / III",
        "unidades_esperadas": ["USP", "EP", "cm longitud hilo", "mm aguja"],
        "materiales": ["Ácido poliglicólico", "Poliglactina", "Polidioxanona", "Seda", "Nylon"],
        "norma_base": "Art. 130° D.S. 016-2011-SA",
    },
    "DISPOSABLES_GLOVES": {
        "nombre": "Guantes Quirúrgicos, Jeringas y Material Descartable",
        "descripcion": "Material médico de curación y protección biológica (Clase I / IIa).",
        "clase_defecto": "Clase I / IIa",
        "unidades_esperadas": ["ml", "Gauge", "tallas XS-XL"],
        "norma_base": "Art. 128° / 129° D.S. 016-2011-SA",
    },
}

# Matriz Maestra Dimensional y Clínica Válida (Caso Base Doble J)
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
        "regex": r'\bISO\s*14971\s*:\s*2012\b',
    },
    "ISO 14971:2007": {
        "status": "DEROGADA",
        "vigente": "ISO 14971:2019 / A11:2021",
        "materia": "Gestión del riesgo en dispositivos médicos",
        "norma_peruana": "D.S. 003-2020-SA",
        "regex": r'\bISO\s*14971\s*:\s*2007\b',
    },
    "MDD 93/42/EEC": {
        "status": "DEROGADA",
        "vigente": "Reglamento (UE) 2017/745 (EU MDR)",
        "materia": "Directiva de Dispositivos Médicos de la Unión Europea",
        "norma_peruana": "D.S. 016-2011-SA",
        "regex": r'\b(?:MDD\s*93/42/EEC|93/42/CEE|Council\s+Directive\s+93/42)\b',
    },
    "EN 980:2008": {
        "status": "DEROGADA",
        "vigente": "ISO 15223-1:2021",
        "materia": "Símbolos gráficos para el etiquetado de dispositivos médicos",
        "norma_peruana": "D.S. 016-2011-SA Art. 137°",
        "regex": r'\bEN\s*980(?:\s*:\s*2008)?\b',
    },
    "ISO 13485:2003": {
        "status": "DEROGADA",
        "vigente": "ISO 13485:2016",
        "materia": "Sistemas de gestión de la calidad para dispositivos médicos",
        "norma_peruana": "D.S. 014-2011-SA (BPA / BPM)",
        "regex": r'\bISO\s*13485\s*:\s*2003\b',
    },
    "ISO 10993-1:2009": {
        "status": "DEROGADA",
        "vigente": "ISO 10993-1:2018",
        "materia": "Evaluación biológica de productos sanitarios - Evaluación y ensayos",
        "norma_peruana": "D.S. 016-2011-SA Art. 130°",
        "regex": r'\bISO\s*10993-1\s*:\s*2009\b',
    },
    "ISO 11135-1:2007": {
        "status": "DEROGADA",
        "vigente": "ISO 11135:2014 (+ Amd 1:2018)",
        "materia": "Esterilización de productos para el cuidado de la salud por Óxido de Etileno",
        "norma_peruana": "D.S. 016-2011-SA Art. 130°",
        "regex": r'\bISO\s*11135-1\s*:\s*2007\b',
    },
    "ISO 11607-1:2006": {
        "status": "DEROGADA",
        "vigente": "ISO 11607-1:2019",
        "materia": "Envases para productos sanitarios esterilizados terminalmente",
        "norma_peruana": "D.S. 016-2011-SA Art. 130°",
        "regex": r'\bISO\s*11607-1\s*:\s*2006\b',
    },
    "ISO 17664:2004": {
        "status": "DEROGADA",
        "vigente": "ISO 17664-1:2021 / ISO 17664-2:2021",
        "materia": "Información del fabricante para reprocesamiento de dispositivos médicos reutilizables",
        "norma_peruana": "D.S. 016-2011-SA Art. 128° y 137°",
        "regex": r'\bISO\s*17664\s*:\s*2004\b',
    },
    "ISO 111737": {
        "status": "INEXISTENTE / TYPO",
        "vigente": "ISO 11737-1:2018 (Bioburden) / ISO 11737-2 (Esterilidad)",
        "materia": "Esterilización de productos sanitarios - Métodos microbiológicos",
        "norma_peruana": "D.S. 016-2011-SA Art. 130°",
        "regex": r'\bISO\s*111737\b',
    },
    "ZSO 9001": {
        "status": "ERROR OCR",
        "vigente": "ISO 9001:2015",
        "materia": "Gestión de Calidad",
        "norma_peruana": "Lectura corrupta",
        "regex": r'\bZSO\s*9001\b',
    },
}

# Catálogo de Traducciones Absurdas y Errores Léxicos Transversales
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

# Referencias Normativas de DIGEMID según Clase de Riesgo
DIGEMID_LEGAL_FRAMEWORK = {
    "DS_016_2011_SA_ART_126": {
        "articulo": "D.S. 016-2011-SA, Artículo 126°",
        "clase": "Universal (Clases I, II, III, IV)",
        "descripcion": "Carta de Autorización del Fabricante detallando facultades exclusivas, marcas, modelos, códigos y concordancia íntegra con el Certificado de Libre Venta (CLV) y RUC del titular en Perú.",
    },
    "DS_016_2011_SA_ART_128": {
        "articulo": "D.S. 016-2011-SA, Artículo 128°",
        "clase": "Clase I (Bajo Riesgo)",
        "descripcion": "Requisitos para dispositivos Clase I: Certificado de Libre Venta, Certificado BPM/ISO 13485, especificaciones técnicas y proyectos de rotulado.",
    },
    "DS_016_2011_SA_ART_129": {
        "articulo": "D.S. 016-2011-SA, Artículo 129°",
        "clase": "Clase II (Moderado Riesgo)",
        "descripcion": "Requisitos para dispositivos Clase II: Añade flujograma de fabricación, validación de esterilización (si aplica) y estudios de estabilidad.",
    },
    "DS_016_2011_SA_ART_130": {
        "articulo": "D.S. 016-2011-SA, Artículo 130°",
        "clase": "Clase III y IV (Alto Riesgo e Implantes)",
        "descripcion": "Informe Técnico detallado con fórmula cuali-cuantitativa de materias primas, flujograma con descripción resumida de etapas, estudios de estabilidad, validación de esterilización con residuales, evaluación clínica (CER) firmada por médico y batería de biocompatibilidad completa ISO 10993.",
    },
    "DS_016_2011_SA_ART_137": {
        "articulo": "D.S. 016-2011-SA, Artículo 137°",
        "clase": "Universal (Clases I, II, III, IV)",
        "descripcion": "Rotulados e IFU: Todo texto de advertencias, contraindicaciones y modo de uso debe estar obligatoriamente en idioma español, con RUC del titular en Perú.",
    },
    "DS_003_2020_SA": {
        "articulo": "D.S. 003-2020-SA",
        "clase": "Universal (Clases I, II, III, IV)",
        "descripcion": "Lista de Principios Esenciales de Seguridad y Desempeño (GSPR) para dispositivos médicos en Perú, alineado a directrices IMDRF/GHTF.",
    },
    "DS_014_2011_SA": {
        "articulo": "D.S. 014-2011-SA",
        "clase": "Universal",
        "descripcion": "Reglamento de Establecimientos Farmacéuticos: BPA, horario de permanencia de Dirección Técnica y trazabilidad de almacenamiento.",
    },
    "LEY_29459": {
        "articulo": "Ley N° 29459, Arts. 5°, 8°, 10°, 12°, 44°-52°",
        "clase": "Universal",
        "descripcion": "Ley de Productos Farmacéuticos, Dispositivos Médicos y Productos Sanitarios. Responsabilidad objetiva del titular por veracidad y calidad.",
    },
}
