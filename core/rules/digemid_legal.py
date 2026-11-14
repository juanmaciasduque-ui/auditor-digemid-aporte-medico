"""
Reglas Regulatorias Específicas de DIGEMID (Perú).
Cubre:
- D.S. 016-2011-SA Art. 130°: Flujograma con descripción resumida de cada fase.
- D.S. 016-2011-SA Art. 126°: Carta de Autorización y sustento de modelos/códigos.
- D.S. 003-2020-SA: Principios Esenciales (GSPR) y justificación de ftalatos/sustancias CMR.
- Rótulos y manuales: Detección de importadores históricos (Consorcio Teleandes) o países erróneos (Colombia/Aporte SAS).
- TUO Ley N° 27444 / Ley N° 29459: Doble fecha contradictoria y vigencia legal.
"""

import re
from typing import List, Dict
from core.models import Finding, Severity, Category


class DigemidLegalRules:
    """Reglas de verificación normativa y legal ante DIGEMID."""

    def analyze_document(self, document_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings: List[Finding] = []

        full_text = " ".join(pages_text.values())

        # 0. Verificación de Pertinencia Documental Regulatoria (D.S. 016-2011-SA / TUPA DIGEMID)
        findings.extend(self._check_document_relevance(document_name, pages_text, full_text))

        # 1. Autorización dirigida a Colombia / Aporte Médico S.A.S. en vez de Perú
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

        return findings

    def _check_document_relevance(self, doc_name: str, pages_text: Dict[int, str], full_text: str) -> List[Finding]:
        """
        Valida que el archivo subido sea pertinente para un trámite de registro sanitario ante DIGEMID.
        Detecta e invalida archivos ajenos como:
        - Hojas de Vida / Currículum Vitae (CV)
        - Cuentas de Cobro / Facturas / Comprobantes de pago contables
        - Documentos administrativos ajenos o textos genéricos sin contenido médico-sanitario
        """
        findings = []
        clean_text = full_text.strip()

        # 1. Detección específica de Hoja de Vida / Currículum Vitae
        cv_match = re.search(
            r'\b(?:hoja\s+de\s+vida|curriculum\s+vitae|curr[ií]culum|experiencia\s+laboral|'
            r'formaci[oó]n\s+acad[eé]mica|perfil\s+profesional|referencias\s+(?:laborales|personales|familiares))\b',
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
                    f"El archivo '{doc_name}' corresponde a una Hoja de Vida o Currículum Vitae personal "
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
            r'\b(?:cuenta\s+de\s+cobro|factura\s+(?:de\s+venta|electr[oó]nica)|recibo\s+por\s+honorarios|'
            r'comprobante\s+de\s+pago|orden\s+de\s+compra|valor\s+a\s+pagar|por\s+concepto\s+de|'
            r'cuenta\s+de\s+ahorros|cuenta\s+corriente\s+no\.?|consignar\s+a|honorarios\s+profesionales)\b',
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
                remediation_advice="Retirar los comprobantes contables del expediente regulatorio.",
            ))
            return findings

        # 3. Detección de texto genérico o ajeno sin ninguna relevancia médica / regulatoria
        if len(clean_text) > 40:
            medical_matches = re.findall(
                r'\b(?:dispositiv[oa]s?|m[eé]dic[oa]s?|sanitari[oa]s?|farmac[eé]utic[oa]s?|cl[ií]nic[oa]s?|'
                r'quir[uú]rgic[oa]s?|pacientes?|terap[eé]utic[oa]s?|cat[eé]teres?|stents?|mallas?|cintas?|'
                r'suturas?|jeringas?|agujas?|implantes?|digemid|vuce|tupa|d\.s\.?\s*016|iso\s*\d+|bpm|gmp|'
                r'ce\s*mark|esteril(?:izaci[oó]n|idad)?|sterile|biocompatib\w+|citotox\w+|lotes?|batch|'
                r'shelf\s*life|vida\s*[uú]til|rotulad[oa]|r[oó]tulo|etiqueta|empaque|bl[ií]ster|fabricante|manufacturer|'
                r'indwelling|ensayos?|laboratorio|calibre|gauges?|in\s*vitro|importad[oa]s?|distribuid[oa]s?|'
                r'titular|ruc\b|dismed|teleandes|aporte\s+m[eé]dico|registro\s+sanitario)\b',
                clean_text,
                re.IGNORECASE
            )
            if len(medical_matches) == 0:
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
                findings.append(Finding(
                    id=f"LEG_COLOMBIA_SAS_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.FATAL,
                    category=Category.DIGEMID_NORMATIVE,
                    title="Documento Legal Autorizado para Colombia Presentado ante DIGEMID (Perú)",
                    description=(
                        f"En la página {p_num} se detectó una carta u hoja técnica que nombra a 'APORTE MEDICO S.A.S.' "
                        "(Colombia, Manizales) como titular en Colombia. "
                        "El expediente ante DIGEMID debe contener una Carta de Autorización y Nombramiento exclusiva "
                        "para 'APORTE MÉDICO PERÚ S.A.C.' (RUC 20610321268). Presentar documentos de otra razón social "
                        "y país acarrea rechazo de plano."
                    ),
                    detected_text="APORTE MEDICO S.A.S. - Manizales - Colombia / Titular en Colombia",
                    expected_text="Carta de Exclusividad/Autorización para APORTE MÉDICO PERÚ S.A.C. (RUC 20610321268) en Perú",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 126° y Art. 130°",
                    remediation_advice="Solicitar a ACE Medical una Carta de Nombramiento dirigida a DIGEMID y APORTE MÉDICO PERÚ S.A.C.",
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

        # Buscar si es un informe técnico o flujograma
        for p_num, text in pages_text.items():
            if re.search(r'\b(?:Flow\s*chart|Flujograma|Diagrama\s+de\s+flujo)\b', text, re.IGNORECASE):
                # Verificar si contiene la frase observada en la Notificación oficial:
                # "Falta agregar breve descripción" o si solo son cajas sin texto explicativo
                if re.search(r'Falta\s+agregar\s+breve\s+descripci[oó]n', text, re.IGNORECASE) or \
                   (len(text) < 200 and not re.search(r'\b(?:etapa|fase|proceso|inspecci[oó]n|ensamble|extrusión)\b', text, re.IGNORECASE)):
                    findings.append(Finding(
                        id=f"LEG_FLOWCHART_NODESC_{doc_name}_{p_num}",
                        document_name=doc_name,
                        page=p_num,
                        severity=Severity.CRITICAL,
                        category=Category.DIGEMID_NORMATIVE,
                        title="Flujograma de Fabricación Sin Breve Descripción de Cada Etapa",
                        description=(
                            f"En la página {p_num} se detectó el diagrama de flujo sin una descripción narrativa "
                            "resumida de cada etapa del proceso de manufactura (extrusión, termoformado de pigtail, "
                            "perforación de orificios, empaque primario y esterilización EO). "
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
            # Buscar contradicción de ftalatos (GSPR 10.4.3 niega ftalatos pero IFU advierte presencia)
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
            # Detectar fechas contradictorias como 26 de septiembre de 2019 arriba y 26 de noviembre en firma
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
            # Detectar dirección antigua de la planta (E-1/7 Neptune Society vs 401A Gera 77)
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
