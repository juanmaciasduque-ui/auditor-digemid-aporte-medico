"""
Reglas Regulatorias Específicas de DIGEMID (Perú).
Cubre:
- Pertinencia documental regulatoria (rechazo de CVs, facturas, cuentas de cobro, archivos en blanco o ajenos).
- D.S. 016-2011-SA Art. 130°: Flujograma con descripción resumida de cada fase.
- D.S. 016-2011-SA Art. 126°: Carta de Autorización y sustento de modelos/códigos.
- D.S. 016-2011-SA Art. 137°: Obligatoriedad de idioma español en rótulos e IFU.
- D.S. 003-2020-SA: Principios Esenciales (GSPR) y justificación de ftalatos/sustancias CMR.
- Detección de normativa extranjera (INVIMA / Decreto 4725 Colombia) o titularidad colombiana infiltrada.
- Reglas específicas por familia de productos de Aporte Médico / urotienda.com (IEC 60601, ISO 17664).
- TUO Ley N° 27444 / Ley N° 29459: Doble fecha contradictoria y vigencia legal.
"""

import re
from typing import List, Dict
from core.models import Finding, Severity, Category


class DigemidLegalRules:
    """Reglas de verificación normativa y legal ante DIGEMID para todo el catálogo de dispositivos."""

    def analyze_document(
        self,
        document_name: str,
        pages_text: Dict[int, str],
        product_family: str = "UNIVERSAL"
    ) -> List[Finding]:
        findings: List[Finding] = []

        full_text = " ".join(pages_text.values())

        # 0. Verificación de Pertinencia Documental Regulatoria (D.S. 016-2011-SA / TUPA DIGEMID)
        findings.extend(self._check_document_relevance(document_name, pages_text, full_text))

        # 1. Autorización dirigida a Colombia / Aporte Médico S.A.S. / normativa INVIMA en vez de DIGEMID Perú
        findings.extend(self._check_colombia_sas_in_peru_filing(document_name, pages_text))

        # 2. Rótulos con Importador Antiguo (Consorcio Teleandes S.A.C.)
        findings.extend(self._check_historical_importer(document_name, pages_text))

        # 3. Flujograma básico sin descripción resumida de etapas (Art. 130° num. 5)
        findings.extend(self._check_flowchart_description(document_name, pages_text))

        # 4. Inconsistencia de Ftalatos / CMR en Clase III
        findings.extend(self._check_phthalates_cmr(document_name, pages_text))

        # 5. Doble fecha contradictoria en cartas oficiales
        findings.extend(self._check_double_contradictory_dates(document_name, pages_text))

        # 6. Dirección de fabricante desactualizada (Neptune Society vs 401A Gera 77)
        findings.extend(self._check_manufacturer_address(document_name, pages_text))

        # 7. Obligatoriedad de idioma español en Rótulos e IFU (Art. 137° D.S. 016-2011-SA)
        findings.extend(self._check_spanish_labeling_art137(document_name, full_text))

        # 8. Reglas específicas por familia del catálogo Aporte Médico / Urotienda
        findings.extend(self._check_family_specific_regulations(document_name, full_text, product_family))

        return findings

    def _check_document_relevance(self, doc_name: str, pages_text: Dict[int, str], full_text: str) -> List[Finding]:
        """
        Valida que el archivo subido sea pertinente para un trámite de registro sanitario ante DIGEMID.
        Detecta e invalida archivos en blanco/ilegibles o ajenos como:
        - Hojas de Vida / Currículum Vitae (CV)
        - Cuentas de Cobro / Facturas / Cotizaciones / Comprobantes contables
        - Documentos administrativos ajenos o textos genéricos sin contenido médico-sanitario
        """
        findings = []
        clean_text = full_text.strip()

        # 0. Archivo completamente vacío o ilegible (escaneo fallido / hoja en blanco)
        if len(clean_text) == 0:
            findings.append(Finding(
                id=f"LEG_EMPTY_DOC_{doc_name}",
                document_name=doc_name,
                page=1,
                severity=Severity.FATAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Documento Ilegible o en Blanco (0 Caracteres Extraídos)",
                description=(
                    f"El archivo '{doc_name}' no contiene texto legible ni capas OCR reconocibles. "
                    "Puede tratarse de un documento escaneado a muy baja resolución, una imagen en blanco o un PDF corrupto. "
                    "Presentar documentos ilegibles en VUCE provoca rechazo inmediato."
                ),
                detected_text="0 caracteres legibles extraídos",
                expected_text="Documento PDF/DOCX nítido con texto legible y resolución mínima de 300 DPI",
                digemid_norm_ref="D.S. 016-2011-SA / Directiva VUCE",
                remediation_advice="Verificar el archivo original y volver a digitalizarlo en alta resolución con OCR habilitado.",
            ))
            return findings

        # 1. Detección específica de Hoja de Vida / Currículum Vitae
        cv_match = re.search(
            r'\b(?:hoja\s+de\s+vida|curriculum\s+vitae|curr[ií]culum|experiencia\s+laboral|'
            r'formaci[oó]n\s+acad[eé]mica|perfil\s+profesional|referencias\s+(?:laborales|personales|familiares)|'
            r'certificado\s+laboral|contrato\s+de\s+trabajo|c[eé]dula\s+de\s+ciudadan[ií]a)\b',
            clean_text,
            re.IGNORECASE
        )
        if cv_match:
            findings.append(Finding(
                id=f"LEG_IRRELEVANT_CV_{doc_name}",
                document_name=doc_name,
                page=1,
                severity=Severity.FATAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Documento No Pertinente: Infiltración de Hoja de Vida / Currículum Vitae",
                description=(
                    f"El archivo '{doc_name}' corresponde a una Hoja de Vida o documento laboral personal "
                    f"('{cv_match.group(0)}') y no a documentación técnica, analítica, clínica ni legal exigible "
                    "para el registro sanitario de un dispositivo médico bajo el D.S. 016-2011-SA. "
                    "La radicación de hojas de vida sueltas o documentos de recursos humanos en la plataforma VUCE "
                    "constituye causal de observación y entorpece la calificación del expediente ante DIGEMID."
                ),
                detected_text=f"Contenido detectado: {cv_match.group(0)} (Hoja de Vida / Datos Personales / Laborales)",
                expected_text="Documento reglamentario de dispositivo médico (Informe Técnico, Ficha Técnica, IFU, Rotulado, etc.)",
                digemid_norm_ref="D.S. 016-2011-SA Art. 126° y 130° / TUPA DIGEMID",
                remediation_advice="Eliminar este archivo del paquete documental. Solo deben incluirse documentos técnicos y legales del dispositivo.",
            ))
            return findings

        # 2. Detección específica de Cuentas de Cobro / Facturas Comerciales / Comprobantes de Pago
        bill_match = re.search(
            r'\b(?:cuenta\s+de\s+cobro|factura\s+(?:de\s+venta|electr[oó]nica)|recibo\s+(?:por\s+honorarios|de\s+caja)|'
            r'comprobante\s+de\s+(?:pago|egreso)|orden\s+de\s+compra|valor\s+a\s+pagar|por\s+concepto\s+de|'
            r'cuenta\s+de\s+ahorros|cuenta\s+corriente\s+no\.?|consignar\s+a|honorarios\s+profesionales|'
            r'cotizaci[oó]n\s+n[°o]?|nota\s+cr[eé]dito|extracto\s+bancario|rut\s+dian|declaraci[oó]n\s+de\s+renta)\b',
            clean_text,
            re.IGNORECASE
        )
        if bill_match:
            findings.append(Finding(
                id=f"LEG_IRRELEVANT_BILL_{doc_name}",
                document_name=doc_name,
                page=1,
                severity=Severity.FATAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Documento No Pertinente: Factura / Cuenta de Cobro Comercial Infiltrada",
                description=(
                    f"El archivo '{doc_name}' corresponde a un comprobante contable o comercial "
                    f"('{bill_match.group(0)}') y no forma parte de los requisitos sanitarios exigidos por DIGEMID. "
                    "Los comprobantes de pago comerciales y cuentas de cobro no deben incorporarse en el expediente "
                    "técnico de registro de dispositivos médicos ante VUCE."
                ),
                detected_text=f"Contenido detectado: {bill_match.group(0)} (Comprobante contable / Factura / Cuenta de cobro)",
                expected_text="Documentación técnica y analítica del dispositivo médico bajo D.S. 016-2011-SA",
                digemid_norm_ref="D.S. 016-2011-SA Art. 130° / TUPA DIGEMID",
                remediation_advice="Retirar los comprobantes contables o comerciales del expediente regulatorio.",
            ))
            return findings

        # 3. Detección de texto genérico o ajeno sin ninguna relevancia médica / regulatoria
        medical_matches = re.findall(
            r'\b(?:dispositiv[oa]s?|m[eé]dic[oa]s?|sanitari[oa]s?|farmac[eé]utic[oa]s?|cl[ií]nic[oa]s?|'
            r'quir[uú]rgic[oa]s?|pacientes?|terap[eé]utic[oa]s?|cat[eé]teres?|stents?|mallas?|cintas?|'
            r'suturas?|jeringas?|agujas?|implantes?|digemid|vuce|tupa|d\.s\.?\s*016|iso\s*\d+|iec\s*\d+|astm|usp|bpm|gmp|'
            r'ce\s*mark|esteril(?:izaci[oó]n|idad|izado)?|sterile|sterilized|biocompatib\w+|citotox\w+|lotes?|batch|'
            r'shelf\s*life|vida\s*[uú]til|rotulad[oa]|r[oó]tulo|etiqueta|empaque|bl[ií]ster|fabricante|manufacturer|'
            r'indwelling|ensayos?|laboratorio|calibre|gauges?|in\s*vitro|importad[oa]s?|distribuid[oa]s?|'
            r'titular|ruc\b|dismed|teleandes|aporte\s+m[eé]dico|registro\s+sanitario|clv|coa|cer|dvr|gspr|ifu|'
            r'uroclamp|uicop|cunningham|canastilla|nitinol|camisa\s+ureteral|access\s+sheath|asa\s+de\s+corte|'
            r'monopolar|bipolar|resectoscop\w+|storz|wolf|olympus|tungsteno|tungsten|pesa\s+vaginal|pesas?\s+[ií]ntimas?|'
            r'pesario|suelo\s+p[eé]lvico|piso\s+p[eé]lvico|rehabilitador|km\s*526|electroestimul\w+|biofeedback|'
            r'incontinencia|prolapso|tot\b|tvt\b|sling|conductor\s+uretral|sonda|estilete|ficha\s+t[eé]cnica|'
            r'informe\s+t[eé]cnico|libre\s+venta|free\s+sale|conformidad|autoclave|vapor|reutilizable|reusable|'
            r'desechable|disposable|un\s+solo\s+uso|single\s+use|orion|ace\s+medical|direcci[oó]n\s+t[eé]cnica|'
            r'droguer[ií]a|invima)\b',
            clean_text,
            re.IGNORECASE
        )
        if len(medical_matches) == 0 and len(clean_text) > 15:
            snippet = clean_text[:120].replace('\n', ' ')
            findings.append(Finding(
                id=f"LEG_NO_MEDICAL_RELEVANCE_{doc_name}",
                document_name=doc_name,
                page=1,
                severity=Severity.FATAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Documento Sin Pertinencia Regulatoria para Registro Sanitario DIGEMID",
                description=(
                    f"El archivo '{doc_name}' no contiene información técnica, clínica, analítica "
                    "ni legal relacionada con un dispositivo médico. Carece de especificaciones, materias primas, "
                    "datos de fabricante, lote o sustento regulatorio bajo el D.S. 016-2011-SA. "
                    "Presentar archivos genéricos o ajenos en la ventanilla VUCE motiva la observación o denegatoria del trámite."
                ),
                detected_text=f"Muestra de texto: \"{snippet}...\" (0 términos médicos/regulatorios)",
                expected_text="Documento reglamentario válido de dispositivo médico (Art. 128°, 129° o 130° D.S. 016-2011-SA)",
                digemid_norm_ref="D.S. 016-2011-SA Arts. 128°, 129°, 130° / Ley N° 29459",
                remediation_advice="Verificar si se cargó el archivo equivocado y sustituirlo por el documento técnico o analítico correspondiente.",
            ))

        return findings

    def _check_colombia_sas_in_peru_filing(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        for p_num, text in pages_text.items():
            # Buscar mención de Aporte Medico S.A.S. o Manizales o Colombia en cartas de nombramiento/autorización
            if re.search(r'\bAPORTE\s+MEDICO\s+S\.?A\.?S\.?\b', text, re.IGNORECASE) or \
               re.search(r'\b(?:Manizales\s*[-–]\s*Colombia|TITULAR\s+DE\s+LOS\s+REGISTROS\s+SANITARIOS\s+en\s+Colombia)\b', text, re.IGNORECASE):
                # Excepción inteligente: si es un CLV colombiano legítimo donde el exportador es Aporte Médico SAS hacia Perú
                is_clv_colombia = bool(re.search(r'\b(?:Certificado\s+de\s+Libre\s+Venta|Free\s+Sale\s+Certificate)\b', text, re.IGNORECASE)) and \
                                  bool(re.search(r'\bAPORTE\s+M[EÉ]DICO\s+PER[UÚ]\b', text, re.IGNORECASE))
                if not is_clv_colombia:
                    findings.append(Finding(
                        id=f"LEG_COLOMBIA_SAS_{doc_name}_{p_num}",
                        document_name=doc_name,
                        page=p_num,
                        severity=Severity.FATAL,
                        category=Category.DIGEMID_NORMATIVE,
                        title="Documento Legal Autorizado para Colombia Presentado ante DIGEMID (Perú)",
                        description=(
                            f"En la página {p_num} se detectó un documento que nombra o cita a 'APORTE MEDICO S.A.S.' "
                            "(Colombia, Manizales) o titularidad colombiana. "
                            "El expediente ante DIGEMID debe contener documentación exclusiva para "
                            "'APORTE MÉDICO PERÚ S.A.C.' (RUC 20610321268). Presentar cartas o rótulos de otra razón social "
                            "y país acarrea rechazo de plano."
                        ),
                        detected_text="APORTE MEDICO S.A.S. - Manizales - Colombia / Titular en Colombia",
                        expected_text="APORTE MÉDICO PERÚ S.A.C. (RUC 20610321268) en Perú",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 126° y Art. 130°",
                        remediation_advice="Emitir el documento o rotulado exclusivamente a nombre de APORTE MÉDICO PERÚ S.A.C. (RUC 20610321268).",
                    ))

            # Detectar normativa colombiana (Decreto 4725 / INVIMA) infiltrada en documentos técnicos de DIGEMID
            is_official_clv = any(k in doc_name.lower() for k in ["clv", "libre venta", "free sale"]) or \
                              bool(re.search(r'\b(?:Certificado\s+de\s+Libre\s+Venta|Free\s+Sale\s+Certificate)\b', text, re.IGNORECASE))
            if not is_official_clv:
                invima_match = re.search(
                    r'\b(?:Decreto\s*4725\s*(?:de\s*2005)?|Resoluci[oó]n\s*4816\s*(?:de\s*2008)?|Registro\s+Sanitario\s+INVIMA)\b',
                    text,
                    re.IGNORECASE
                )
                if invima_match:
                    findings.append(Finding(
                        id=f"LEG_INVIMA_IN_PERU_{doc_name}_{p_num}",
                        document_name=doc_name,
                        page=p_num,
                        severity=Severity.CRITICAL,
                        category=Category.DIGEMID_NORMATIVE,
                        title="Normativa Colombiana (INVIMA / Decreto 4725) Infiltrada en Trámite DIGEMID (Perú)",
                        description=(
                            f"En la página {p_num} se cita '{invima_match.group(0)}' perteneciente a la legislación de Colombia. "
                            "Para trámites en Perú debe adecuarse íntegramente al marco legal peruano (Ley N° 29459 y D.S. 016-2011-SA)."
                        ),
                        detected_text=invima_match.group(0),
                        expected_text="D.S. 016-2011-SA / Ley N° 29459 / DIGEMID Perú",
                        digemid_norm_ref="D.S. 016-2011-SA / Ley N° 29459",
                        remediation_advice="Sustituir toda referencia a INVIMA o Decreto 4725 por la normativa DIGEMID vigente.",
                    ))

        return findings

    def _check_historical_importer(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        for p_num, text in pages_text.items():
            if re.search(r'\b(?:Consorcio\s+Teleandes|20537638631)\b', text, re.IGNORECASE):
                findings.append(Finding(
                    id=f"LEG_HIST_IMPORTER_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.FATAL,
                    category=Category.DIGEMID_NORMATIVE,
                    title="Rotulado con Datos de Importador Histórico Extinto (Consorcio Teleandes)",
                    description=(
                        f"En la página {p_num} el rotulado sigue declarando a 'Consorcio Teleandes S.A.C.' (RUC 20537638631) "
                        "como importador/distribuidor. Los proyectos de rotulado mediato e inmediato deben declarar "
                        "exclusivamente a APORTE MÉDICO PERÚ S.A.C. como titular e importador autorizado."
                    ),
                    detected_text="Consorcio Teleandes S.A.C. (RUC 20537638631)",
                    expected_text="APORTE MÉDICO PERÚ S.A.C. (RUC 20610321268)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 137°",
                    remediation_advice="Reemplazar el nombre y RUC del importador en todos los proyectos de rotulado.",
                ))

        return findings

    def _check_flowchart_description(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        for p_num, text in pages_text.items():
            if re.search(r'\b(?:Flow\s*chart|Flujograma|Diagrama\s+de\s+flujo)\b', text, re.IGNORECASE):
                if re.search(r'Falta\s+agregar\s+breve\s+descripci[oó]n', text, re.IGNORECASE) or \
                   (len(text) < 200 and not re.search(r'\b(?:etapa|fase|proceso|inspecci[oó]n|ensamble|extrusión|extrusion)\b', text, re.IGNORECASE)):
                    findings.append(Finding(
                        id=f"LEG_FLOWCHART_NODESC_{doc_name}_{p_num}",
                        document_name=doc_name,
                        page=p_num,
                        severity=Severity.CRITICAL,
                        category=Category.DIGEMID_NORMATIVE,
                        title="Flujograma de Fabricación Sin Breve Descripción de Cada Etapa",
                        description=(
                            f"En la página {p_num} se detectó el diagrama de flujo sin una descripción narrativa "
                            "resumida de cada etapa del proceso de manufactura. "
                            "El D.S. 016-2011-SA Art. 130° num. 5 exige expresamente dicha descripción técnica."
                        ),
                        detected_text="Flujograma gráfico sin texto descriptivo por etapa",
                        expected_text="Diagrama con descripción narrativa explicativa de cada etapa productiva",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 130° numeral 5",
                        remediation_advice="Añadir una sección con 2 o 3 líneas explicativas por cada caja o bloque del diagrama.",
                    ))

        return findings

    def _check_phthalates_cmr(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        for p_num, text in pages_text.items():
            if re.search(r'\b(?:phthalates?|ftalatos?|DEHP)\b', text, re.IGNORECASE):
                if re.search(r'\b(?:contains?\s+phthalates?|contiene\s+ftalatos?)\b', text, re.IGNORECASE) and \
                   re.search(r'\b(?:does\s+not\s+contain|libre\s+de\s+ftalatos?|phthalate\s*free)\b', text, re.IGNORECASE):
                    findings.append(Finding(
                        id=f"LEG_PHTHALATES_CONTRADICTION_{doc_name}_{p_num}",
                        document_name=doc_name,
                        page=p_num,
                        severity=Severity.FATAL,
                        category=Category.DIGEMID_NORMATIVE,
                        title="Contradicción sobre Presencia de Ftalatos (DEHP) en Dispositivo Clase III",
                        description=(
                            f"En la página {p_num} existen declaraciones contradictorias sobre ftalatos "
                            "(un párrafo afirma contenerlos o advierte precauciones, mientras otro afirma que es phthalate-free). "
                            "Para dispositivos Clase III, DIGEMID exige conocer el porcentaje exacto y cómo se minimiza el riesgo."
                        ),
                        detected_text="Contradicción contiene / libre de ftalatos en el mismo documento",
                        expected_text="Certificación analítica de sustancias SVHC / REACH / Libre de ftalatos",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 130° / D.S. 003-2020-SA",
                        remediation_advice="Adjuntar reporte químico analítico SVHC/REACH que demuestre ausencia de ftalatos.",
                    ))

        return findings

    def _check_double_contradictory_dates(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        for p_num, text in pages_text.items():
            has_sep = bool(re.search(r'26\s*(?:de\s+)?(?:septiembre|sep|09)\s*(?:de\s+)?2019', text, re.IGNORECASE))
            has_nov = bool(re.search(r'26\s*(?:de\s+)?(?:noviembre|nov|11)\s*(?:de\s+)?2019', text, re.IGNORECASE))

            if has_sep and has_nov:
                findings.append(Finding(
                    id=f"LEG_DOUBLE_DATE_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.CRITICAL,
                    category=Category.DIGEMID_NORMATIVE,
                    title="Doble Fecha Contradictoria en Carta Oficial (26/09/2019 vs 26/11/2019)",
                    description=(
                        f"En la página {p_num} el encabezado cita '26 de Septiembre de 2019' y el pie de firma cita '26/11/2019'. "
                        "Esta discordancia temporal pone en duda la autenticidad del documento ante DIGEMID."
                    ),
                    detected_text="Encabezado: 26/09/2019 vs Firma: 26/11/2019",
                    expected_text="Fecha de emisión y firma idéntica y concordante",
                    digemid_norm_ref="TUO Ley N° 27444 Art. 34°",
                    remediation_advice="Emitir una carta nueva con fecha única concordante en membrete y firma.",
                ))

        return findings

    def _check_manufacturer_address(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        for p_num, text in pages_text.items():
            if re.search(r'\bNeptune\s+Society\b', text, re.IGNORECASE):
                findings.append(Finding(
                    id=f"LEG_OLD_ADDRESS_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.CRITICAL,
                    category=Category.DIGEMID_NORMATIVE,
                    title="Dirección Desactualizada de Planta del Fabricante (Neptune Society)",
                    description=(
                        f"En la página {p_num} se indica la dirección antigua 'E-1/7 Neptune Society'. "
                        "La planta actual certificada en ISO 13485:2016 y CDSCO de ACE Medical es '401A, Gera 77, "
                        "East Avenue, Kalyani Nagar, Pune 411006, India'. La discrepancia de plantas anula el registro."
                    ),
                    detected_text="E-1/7 Neptune Society, Pune",
                    expected_text="401A, Gera 77, East Avenue, Kalyani Nagar, Pune 411006, India",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 126° y Art. 130°",
                    remediation_advice="Actualizar la dirección de manufactura en rótulos y fichas técnicas a 401A Gera 77.",
                ))

        return findings

    def _check_spanish_labeling_art137(self, doc_name: str, full_text: str) -> List[Finding]:
        """Art. 137° D.S. 016-2011-SA exige que rótulos, etiquetas e IFU estén en idioma español."""
        findings = []
        doc_lower = doc_name.lower()
        is_label_or_ifu = any(k in doc_lower for k in ["rotulo", "rótulo", "etiqueta", "label", "ifu", "manual", "instrucciones"])
        if not is_label_or_ifu or len(full_text.strip()) < 150:
            return findings

        spanish_hits = len(re.findall(
            r'\b(?:para|uso|advertencia|precauci[oó]n|instrucciones|producto|dispositivo|fabricado|importado|registro\s+sanitario|esteril|est[eé]ril|lote)\b',
            full_text,
            re.IGNORECASE
        ))
        english_hits = len(re.findall(
            r'\b(?:the|and|for|with|sterile|warning|caution|instructions|device|manufactured|single\s+use)\b',
            full_text,
            re.IGNORECASE
        ))

        if english_hits >= 5 and spanish_hits == 0:
            findings.append(Finding(
                id=f"LEG_NO_SPANISH_ART137_{doc_name}",
                document_name=doc_name,
                page=1,
                severity=Severity.CRITICAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Proyecto de Rotulado o IFU Únicamente en Inglés (Incumple Art. 137°)",
                description=(
                    f"El documento '{doc_name}' corresponde a un rótulo o manual de instrucciones (IFU), "
                    "pero está redactado íntegramente en idioma inglés sin traducción oficial al español. "
                    "DIGEMID exige por norma imperativa (Art. 137°) que la información al usuario y rótulos figuren en español."
                ),
                detected_text=f"Idioma inglés detectado ({english_hits} términos) / 0 palabras técnicas en español",
                expected_text="Rotulado e IFU redactados o traducidos integralmente al idioma español",
                digemid_norm_ref="D.S. 016-2011-SA Art. 137°",
                remediation_advice="Incorporar la traducción oficial al español en rótulos mediato/inmediato y manual IFU.",
            ))

        return findings

    def _check_family_specific_regulations(self, doc_name: str, full_text: str, product_family: str) -> List[Finding]:
        """Aplica controles normativos específicos por línea de producto de Aporte Médico / urotienda.com."""
        findings = []
        doc_lower = doc_name.lower()
        text_lower = full_text.lower()
        is_ifu_or_manual = any(k in doc_lower for k in ["ifu", "manual", "instrucciones", "rotulo", "rótulo"])
        is_tech_report = any(k in doc_lower for k in ["informe", "technical", "ficha", "dvr", "gspr"])

        # 1. Equipos Biomédicos Activos / Electrocirugía (KM 526, Asas Monopolares/Bipolares)
        is_active = product_family in ("PELVIC_REHAB_ACTIVE", "ELECTROSURGICAL_LOOPS") or \
                    bool(re.search(r'\b(?:km\s*526|electroestimulador|biofeedback|asa\s+(?:monopolar|bipolar)|resectoscop)\b', text_lower))
        if is_active:
            if is_ifu_or_manual and len(full_text) > 100:
                if "km 526" in text_lower or "electroestimul" in text_lower:
                    if not re.search(r'\b(?:marcapasos|pacemaker|embarazo|pregnancy|contraindicaci)\b', text_lower):
                        findings.append(Finding(
                            id=f"LEG_ACTIVE_CONTRA_{doc_name}",
                            document_name=doc_name,
                            page=1,
                            severity=Severity.CRITICAL,
                            category=Category.DIGEMID_NORMATIVE,
                            title="Manual de Equipo Activo (Electroestimulador) Sin Contraindicaciones Clínicas Obligatorias",
                            description=(
                                f"En '{doc_name}' no se detectan las contraindicaciones críticas exigidas por DIGEMID "
                                "para equipos de electroestimulación de piso pélvico (uso en pacientes con marcapasos, "
                                "embarazo, implantes metálicos pélvicos o infecciones agudas)."
                            ),
                            detected_text="Ausencia de advertencias de marcapasos/embarazo en manual/IFU",
                            expected_text="Sección explícita de contraindicaciones (Marcapasos, Embarazo, DIU metálico)",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 129° y 137° / IEC 60601-1",
                            remediation_advice="Agregar la sección completa de contraindicaciones y precauciones de seguridad eléctrica en español.",
                        ))
                elif "asa" in text_lower or "monopolar" in text_lower or "bipolar" in text_lower:
                    if not re.search(r'\b(?:alta\s+frecuencia|high\s+frequency|quemadura|burn|aislamiento|insulation|iec\s*60601)\b', text_lower):
                        findings.append(Finding(
                            id=f"LEG_ELECTRO_WARN_{doc_name}",
                            document_name=doc_name,
                            page=1,
                            severity=Severity.CRITICAL,
                            category=Category.DIGEMID_NORMATIVE,
                            title="IFU de Asa Electroquirúrgica Sin Advertencias de Alta Frecuencia / Aislamiento",
                            description=(
                                f"El manual '{doc_name}' de asa de corte monopolar/bipolar omite advertencias sobre "
                                "riesgos de quemaduras por corriente de alta frecuencia e inspección previa del aislamiento."
                            ),
                            detected_text="Sin advertencias de alta frecuencia ni integridad de aislamiento",
                            expected_text="Advertencias de electrocirugía e inspección de aislamiento según IEC 60601-2-2",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 129°/130° / IEC 60601-2-2",
                            remediation_advice="Incluir advertencias de potencia máxima admitida, placa neutra (monopolar) y revisión de aislamiento.",
                        ))

            if is_tech_report and len(full_text) > 100 and not re.search(r'\b(?:iec\s*60601|seguridad\s+el[eé]ctrica|compatibilidad\s+electromagn[eé]tica|diel[eé]ctric)\b', text_lower):
                findings.append(Finding(
                    id=f"LEG_ACTIVE_IEC60601_{doc_name}",
                    document_name=doc_name,
                    page=1,
                    severity=Severity.CRITICAL,
                    category=Category.DIGEMID_NORMATIVE,
                    title="Documento Técnico de Dispositivo Activo Sin Referencia a Seguridad Eléctrica (IEC 60601)",
                    description=(
                        f"El informe '{doc_name}' corresponde a un dispositivo médico activo (electroestimulador o electrodo), "
                        "pero no declara el cumplimiento de normas de seguridad eléctrica / aislamiento IEC 60601-1."
                    ),
                    detected_text="Sin mención a IEC 60601-1 / IEC 60601-1-2 / ensayo dieléctrico",
                    expected_text="Cumplimiento de IEC 60601-1 (y IEC 60601-1-2 EMC / IEC 60601-2-2)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 129° / D.S. 003-2020-SA",
                    remediation_advice="Citar y adjuntar los reportes de ensayo IEC 60601 vigentes en el expediente técnico.",
                ))

        # 2. Dispositivos Reutilizables (Uroclamp, Conductores Uretrales Metálicos, Pesas Íntimas)
        is_reusable = product_family in ("REUSABLE_INSTRUMENTS", "NON_INVASIVE_INCONTINENCE", "PELVIC_REHAB_WEIGHTS") or \
                      bool(re.search(r'\b(?:uroclamp|conductor\s+uretral|pesas?\s+(?:[íi]ntimas?|vaginales?)|pesario|reutilizable)\b', text_lower))
        if is_reusable and is_ifu_or_manual and len(full_text) > 100:
            if "reutilizable" in text_lower or "reusable" in text_lower:
                if not re.search(r'\b(?:limpieza|lavado|desinfecci[oó]n|esterilizaci[oó]n|autoclave|wash|clean|disinfect|reprocesamiento)\b', text_lower):
                    findings.append(Finding(
                        id=f"LEG_REUSABLE_ISO17664_{doc_name}",
                        document_name=doc_name,
                        page=1,
                        severity=Severity.CRITICAL,
                        category=Category.DIGEMID_NORMATIVE,
                        title="Dispositivo Reutilizable Sin Instrucciones de Limpieza / Reprocesamiento (ISO 17664)",
                        description=(
                            f"En '{doc_name}' se declara un dispositivo reutilizable, pero el IFU carece de "
                            "instrucciones validadas de lavado, desinfección o esterilización entre usos."
                        ),
                        detected_text="Dispositivo reutilizable sin protocolo de limpieza/desinfección",
                        expected_text="Instrucciones validadas de limpieza, desinfección o reesterilización según ISO 17664-1",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 137° / D.S. 003-2020-SA / ISO 17664-1",
                        remediation_advice="Detallar temperatura, agente limpiador/desinfectante y método de secado o autoclave permitido.",
                    ))

        return findings
