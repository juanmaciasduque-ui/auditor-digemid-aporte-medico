"""
Mini-Agente y Motor de Búsqueda Regulatorio DIGEMID.
Consulta normas legales actualizadas (D.S. 016, D.S. 003, D.S. 014, D.S. 029, Ley 29459),
bases de datos de precedentes de registros sanitarios en Perú y genera
soluciones y redactados técnicos oficiales para subsanar observaciones de VUCE.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RegulatoryNorm:
    codigo: str
    nombre: str
    articulos_clave: Dict[str, str]
    temas: List[str]
    vigencia: str
    enlace_oficial: str


@dataclass
class ApprovedPrecedent:
    registro_sanitario: str
    titular: str
    fabricante: str
    producto: str
    calibres_fr: str
    longitudes_cm: str
    vida_util: str
    tiempo_permanencia: str
    material: str


class DigemidAgent:
    """
    Mini-agente regulatorio especializado en Dispositivos Médicos (Clase III / DIGEMID Perú).
    Permite buscar normas, consultar precedentes aprobados y redactar cartas y subsanaciones oficiales.
    """

    def __init__(self):
        self._load_knowledge_base()
        self._load_precedents()

    def _load_knowledge_base(self):
        self.normativa_db: Dict[str, RegulatoryNorm] = {
            "DS_016_2011_SA": RegulatoryNorm(
                codigo="D.S. N° 016-2011-SA",
                nombre="Reglamento para el Registro, Control y Vigilancia Sanitaria de Productos Farmacéuticos, Dispositivos Médicos y Productos Sanitarios",
                articulos_clave={
                    "Art. 126": (
                        "Carta de Autorización del Fabricante: Debe ser emitida por el titular o fabricante del producto, "
                        "dirigida a la DIGEMID y al importador en Perú (indicando RUC y razón social exacta). Debe detallar "
                        "los modelos, marcas, códigos de catálogo y sustentar expresamente los componentes de los Sets o Kits."
                    ),
                    "Art. 130": (
                        "Requisitos para la inscripción de Dispositivos Médicos Clase III: "
                        "1. Certificado de Libre Venta (CLV) emitido por autoridad competente del país de origen o exportador. "
                        "2. Certificado de Buenas Prácticas de Manufactura (BPM) o ISO 13485:2016 vigente. "
                        "3. Informe Técnico detallado con especificaciones de materias primas y producto terminado. "
                        "4. Estudios de estabilidad y sustento de vida útil (tiempo real o acelerado bajo ASTM F1980 / ISO 11607). "
                        "5. Flujograma de fabricación con una BREVE DESCRIPCIÓN RESUMIDA DE CADA ETAPA del proceso. "
                        "6. Validación de esterilización (óxido de etileno según ISO 11135 con SAL 10^-6 y residuales ISO 10993-7). "
                        "7. Reporte de Evaluación Clínica (CER) firmado por profesional médico calificado. "
                        "8. Batería de biocompatibilidad completa según ISO 10993-1 según la naturaleza y duración del contacto."
                    ),
                    "Art. 137": (
                        "Rotulado mediato, inmediato y Manual de Instrucciones de Uso (IFU): "
                        "Todo el texto de indicaciones, precauciones y advertencias debe estar obligatoriamente en idioma español. "
                        "Debe contener razón social, RUC y dirección de la droguería titular en Perú, número de lote, fecha de vencimiento "
                        "y símbolo unívoco de estéril y un solo uso."
                    ),
                },
                temas=["registro sanitario", "clase iii", "catéter", "flujograma", "esterilizacion", "rotulado", "vida util"],
                vigencia="VIGENTE (Modificado por D.S. 029-2023-SA)",
                enlace_oficial="https://www.digemid.minsa.gob.pe"
            ),
            "DS_003_2020_SA": RegulatoryNorm(
                codigo="D.S. N° 003-2020-SA",
                nombre="Reglamento que aprueba los Principios Esenciales de Seguridad y Desempeño de los Dispositivos Médicos (GSPR)",
                articulos_clave={
                    "Principio 1 y 2": "Gestión del riesgo: Se exige implementar matrices de gestión de riesgos bajo ISO 14971:2019 (la versión 2012 está obsoleta).",
                    "Principio 10.4": "Sustancias químicas peligrosas y Ftalatos: Si el dispositivo contiene sustancias CMR o ftalatos (DEHP) en más de 0.1% p/p, debe justificarse técnicamente y declararse en rótulos e IFU.",
                    "Principio 11": "Control de infección y contaminación microbiana: Requisitos de esterilidad y acondicionamiento estéril."
                },
                temas=["principios esenciales", "gspr", "riesgo", "ftalatos", "iso 14971"],
                vigencia="VIGENTE",
                enlace_oficial="https://www.digemid.minsa.gob.pe"
            ),
            "DS_014_2011_SA": RegulatoryNorm(
                codigo="D.S. N° 014-2011-SA",
                nombre="Reglamento de Establecimientos Farmacéuticos (BPA y Dirección Técnica)",
                articulos_clave={
                    "Art. 22": "Dirección Técnica: La droguería debe contar con un Químico Farmacéutico Director Técnico con horario de permanencia acorde a las operaciones.",
                    "Art. 111": "Buenas Prácticas de Almacenamiento (BPA): Todo lote importado debe contar con certificado de análisis por lote y trazabilidad física en almacén."
                },
                temas=["bpa", "direccion tecnica", "almacenamiento", "drogueria"],
                vigencia="VIGENTE",
                enlace_oficial="https://www.digemid.minsa.gob.pe"
            ),
            "LEY_29459": RegulatoryNorm(
                codigo="Ley N° 29459",
                nombre="Ley de los Productos Farmacéuticos, Dispositivos Médicos y Productos Sanitarios",
                articulos_clave={
                    "Art. 8": "Obligatoriedad de Registro Sanitario: Prohibida la comercialización sin registro sanitario vigente.",
                    "Art. 10": "Responsabilidad Objetiva: El titular del registro sanitario responde por la calidad, seguridad, eficacia y veracidad de toda la documentación presentada."
                },
                temas=["ley 29459", "registro obligatorio", "responsabilidad"],
                vigencia="VIGENTE",
                enlace_oficial="https://www.digemid.minsa.gob.pe"
            ),
        }

    def _load_precedents(self):
        """Precedentes de dispositivos médicos similares registrados exitosamente ante DIGEMID."""
        self.precedentes_db: List[ApprovedPrecedent] = [
            ApprovedPrecedent(
                registro_sanitario="DM17365E (Histórico Aporte Perú)",
                titular="APORTE MÉDICO PERÚ S.A.C.",
                fabricante="ACE Medical Devices Pvt. Ltd. (India)",
                producto="Catéter Ureteral Doble J y Set",
                calibres_fr="3.0 a 8.0 Fr",
                longitudes_cm="6.0 a 32.0 cm",
                vida_util="36 meses (3 años)",
                tiempo_permanencia="≤ 30 días (temporal) / hasta 90 días (Long-Life)",
                material="Poliuretano Radiopaco de grado médico"
            ),
            ApprovedPrecedent(
                registro_sanitario="DM-20451-E (Referencia Mercado Perú)",
                titular="Droguería Médica Líder S.A.",
                fabricante="Fabricante Certificado CE / FDA",
                producto="Stent Ureteral Doble Cola de Cochino y Set de Colocación",
                calibres_fr="4.0 a 8.5 Fr",
                longitudes_cm="12.0 a 30.0 cm",
                vida_util="60 meses (5 años con estabilidad acelerada + tiempo real)",
                tiempo_permanencia="Hasta 90 días",
                material="Poliuretano hidrofílico"
            ),
        ]

    def search_regulations(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca artículos normativos y directivas de DIGEMID según palabras clave.
        """
        q_lower = query.lower().strip()
        results = []

        for code, norm in self.normativa_db.items():
            matches_tema = any(t in q_lower or q_lower in t for t in norm.temas)
            matching_articles = {}

            for art, content in norm.articulos_clave.items():
                if q_lower in art.lower() or q_lower in content.lower() or matches_tema:
                    matching_articles[art] = content

            if matching_articles or matches_tema:
                results.append({
                    "norma_codigo": norm.codigo,
                    "norma_nombre": norm.nombre,
                    "vigencia": norm.vigencia,
                    "articulos": matching_articles if matching_articles else norm.articulos_clave,
                    "enlace": norm.enlace_oficial
                })

        return results

    def get_precedents_for_product(self, product_type: str = "cateter") -> List[ApprovedPrecedent]:
        """Retorna precedentes aprobados ante DIGEMID para benchmark."""
        return self.precedentes_db

    def generate_solution_template(self, problem_key: str) -> Dict[str, str]:
        """
        Genera el redactado técnico-legal oficial para resolver las observaciones más críticas.
        """
        templates = {
            "CARTA_FABRICANTE_ART126": {
                "titulo": "Modelo Oficial: Carta de Autorización y Desglose de Modelos (Art. 126° D.S. 016)",
                "destinatario": "Dirección General de Medicamentos, Insumos y Drogas (DIGEMID) - Perú",
                "texto_espanol": (
                    "Por medio de la presente, ACE MEDICAL DEVICES PVT. LTD., con domicilio legal en 401A, Gera 77, "
                    "East Avenue, Kalyani Nagar, Pune 411006, India, como fabricante exclusivo de los dispositivos médicos, "
                    "CERTIFICA Y AUTORIZA a la empresa APORTE MÉDICO PERÚ S.A.C., con RUC N° 20610321268, con domicilio en Lima, Perú, "
                    "como nuestro TITULAR, IMPORTADOR Y DISTRIBUIDOR EXCLUSIVO en la República del Perú para el registro, importación "
                    "y comercialización del producto: CATÉTERES URETERALES (DOBLE J / STENT URETERAL Y SET).\n\n"
                    "Asimismo, se certifica que la matriz de calibres amparada corresponde unívocamente a los diámetros de 3.0 a 8.0 Fr "
                    "y longitudes de 06 a 32 cm. En las presentaciones comerciales en 'SET', el producto incluye: (1) Catéter Ureteral Doble J, "
                    "(2) Guía de colocación hidrofílica o PTFE, (3) Empujador/Pusher con banda radiopaca, (4) Clamp urológico y (5) Hilo de sujeción."
                ),
                "texto_ingles_ace": (
                    "To: DIGEMID (Peru) and APORTE MÉDICO PERÚ S.A.C. (RUC 20610321268).\n"
                    "We, ACE MEDICAL DEVICES PVT. LTD., located at 401A, Gera 77, East Avenue, Kalyani Nagar, Pune 411006, India, "
                    "hereby authorize APORTE MÉDICO PERÚ S.A.C. as our exclusive Distributor and Registration Holder in Peru for "
                    "URETERAL STENT (DOUBLE J) AND SET. Dimensions are strictly 3.0–8.0 Fr diameter and 06–32 cm length. "
                    "The SET presentation strictly contains: Ureteral Stent, Pusher, Guidewire (PTFE), Urological Clamp and Suture Thread."
                ),
                "instrucciones": "ACE Medical Devices debe imprimir este texto en papel membretado actual con firma de Vikas Sethi y sello húmedo nítido apostillado."
            },
            "FLUJOGRAMA_ART130": {
                "titulo": "Descripción Resumida Obligatoria del Flujograma de Fabricación (Art. 130° num. 5)",
                "texto_espanol": (
                    "1. Recepción y Control de Materia Prima: Inspección de poliuretano de grado médico radiopaco (con sulfato de bario) y componentes del empaque primario.\n"
                    "2. Extrusión de Tubo Ureteral: Extrusión termoplástica a temperatura controlada calibrando diámetro interno y externo según calibre Fr.\n"
                    "3. Termoformado de Pigtails (Doble J): Moldeo térmico de ambos extremos en forma de espiral/loop para anclaje en pelvis renal y vejiga.\n"
                    "4. Perforación y Marcado: Maquinado de orificios de drenaje laterales libres de rebabas y estampado de marcas radiopacas centimétricas.\n"
                    "5. Acondicionamiento del Set: Ensamble del catéter con empujador, guía PTFE, pinza y sutura en sala limpia Clase ISO 8 (ISO 14644-1).\n"
                    "6. Empaque Primario y Sellado: Envasado en pouch de Tyvek/Película plástica con sellado térmico validado bajo ISO 11607-1.\n"
                    "7. Esterilización Terminal por Óxido de Etileno: Ciclo de esterilización gaseosa EO validado bajo ISO 11135 asegurando SAL 10^-6 y desgasificación controlada de residuales según ISO 10993-7."
                ),
                "instrucciones": "Insertar este texto explicativo debajo del diagrama de cajas del Technical Report para subsanar la observación 1.8 de DIGEMID."
            },
            "ESTERILIZACION_SAL": {
                "titulo": "Corrección Científica de Nivel de Garantía de Esterilidad (SAL 10^-6)",
                "texto_espanol": (
                    "El proceso de esterilización por Óxido de Etileno (EO) ha sido validado bajo la norma internacional ISO 11135:2014, "
                    "alcanzando un Nivel de Garantía de Esterilidad (Sterility Assurance Level - SAL) de 10^-6 (uno en un millón). "
                    "Las muestras fueron inoculadas con Indicadores Biológicos de esporas de Bacillus atrophaeus (ATCC 9372) con población de 10^6 UFC."
                ),
                "instrucciones": "Sustituir toda mención errónea de 'SAL of 10^6' o '106' por 'SAL 10^-6' en la Sección 8.0 del informe ACE/SVR/DJ-02."
            },
            "INFILTRACION_LONGITUDES": {
                "titulo": "Sustento Técnico para Separar Ureteral Catheter (70-90 cm) del Stent Doble J (6-32 cm)",
                "texto_espanol": (
                    "Se aclara ante DIGEMID que el expediente ampara exclusivamente CATÉTERES URETERALES TIPO DOBLE J (Stents autorretenibles de 6 a 32 cm). "
                    "Las longitudes de 70 a 90 cm mencionadas accidentalmente en los reportes de exportación corresponden al producto 'Catéter Ureteral Simple' "
                    "(código no solicitado en este registro). Todos los documentos técnicos, rótulos e instrucciones de uso han sido depurados para amparar "
                    "únicamente el rango de 6 a 32 cm."
                ),
                "instrucciones": "Presentar este párrafo en el escrito de subsanación ante VUCE y eliminar tablas de 70-90 cm del paquete."
            }
        }

        return templates.get(problem_key, {
            "titulo": "Recomendación General DIGEMID",
            "texto_espanol": "Consultar la base normativa de D.S. 016-2011-SA Art. 130°.",
            "instrucciones": "Revisar la guía de subsanación oficial de DIGEMID."
        })
