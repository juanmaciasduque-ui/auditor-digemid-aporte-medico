"""
Validador de Estructura, Celdas en Blanco, Anexos Prometidos y Numeración.
Cubre el Catálogo B:
- Celdas y secciones en blanco en checklists (GSPR) y manuales IFU ('Artwork code with Rev. No.').
- Tablas que rellenan variables únicamente con la palabra 'Complies' sin corridas, lotes ni equipos reales.
- Anexos prometidos en el texto pero ausentes en el documento o paquete ('Annexure 3 CV is attached', 'PMS Report attached').
- Numeración desordenada de secciones (saltos erráticos como 1.1, 1.2, 1.3, 1.4, 3, 4, 5).
"""

import re
from typing import List, Dict, Any, Set
from core.models import Finding, Severity, Category


class StructureIntegrityRules:
    """Reglas de validación estructural y consistencia interna de formatos."""

    def analyze_document(
        self,
        document_name: str,
        pages_text: Dict[int, str],
        tables_data: List[Dict[str, Any]],
        all_document_names: Set[str] = None,
        total_pages: int = None
    ) -> List[Finding]:
        findings: List[Finding] = []
        all_docs = all_document_names or set()

        full_doc_text = "\n".join(pages_text.values())

        # 1. Celdas en blanco críticas y campos vacíos en IFU
        findings.extend(self._check_blank_fields_and_ifu(document_name, pages_text))

        # 2. Tablas que solo dicen "Complies" sin datos cuantitativos de corrida
        findings.extend(self._check_complies_only_tables(document_name, tables_data, pages_text))

        # 3. Anexos prometidos en el texto pero ausentes
        findings.extend(self._check_promised_annexes(document_name, pages_text, full_doc_text, all_docs))

        # 4. Numeración desordenada de secciones
        findings.extend(self._check_section_numbering(document_name, pages_text))

        # 5. Foliación declarada vs páginas reales del archivo (Páginas faltantes)
        findings.extend(self._check_page_count_discrepancy(document_name, pages_text, total_pages))

        return findings

    def _check_blank_fields_and_ifu(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        # Búsqueda de Artwork code en blanco
        for page_num, text in pages_text.items():
            # Patrón para 'Artwork code with Rev. No.' seguido de dos puntos o vacío/espacios
            artwork_match = re.search(
                r'Artwork\s+code\s+with\s+Rev\.?\s*(?:No\.?|Number)?\s*[:\-_]?\s*(?:\r?\n|$|[ \t]+(?=\r?\n))',
                text,
                re.IGNORECASE
            )
            if artwork_match:
                findings.append(Finding(
                    id=f"STR_ARTWORK_BLANK_{doc_name}_{page_num}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity.MINOR,
                    category=Category.VISUAL_STRUCTURE,
                    title="Campo Crítico en Blanco en Manual IFU (Artwork code with Rev. No.)",
                    description=(
                        f"En la página {page_num} se detectó el campo 'Artwork code with Rev. No.' dejado en blanco. "
                        "El rotulado e IFU de DIGEMID exige código unívoco de arte y versión controlada."
                    ),
                    detected_text=artwork_match.group(0).strip(),
                    expected_text="Código de arte y revisión asignado (ej: AW-ACE-DJ-01 Rev. 02)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 137°",
                    remediation_advice="Asignar el código de diseño gráfico y revisión en la plantilla del IFU.",
                ))

            # Búsqueda de "Falta agregar breve descripción" o texto placeholder de borradores
            draft_placeholder = re.search(r'\b(?:Falta\s+agregar|Pendiente\s+de\s+completar|TO\s+BE\s+ADDED|TBD|PLACEHOLDER)\b', text, re.IGNORECASE)
            if draft_placeholder:
                findings.append(Finding(
                    id=f"STR_PLACEHOLDER_{doc_name}_{page_num}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity.CRITICAL,
                    category=Category.VISUAL_STRUCTURE,
                    title="Texto de Borrador / Marcador Pendiente Detectado",
                    description=(
                        f"Se encontró el marcador de texto provisional '{draft_placeholder.group(0)}' en la página {page_num}. "
                        "Esto evidencia que el documento se presentó incompleto sin revisión final."
                    ),
                    detected_text=draft_placeholder.group(0),
                    expected_text="Contenido técnico formal y definitivo redactado",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                    remediation_advice="Eliminar los comentarios de borrador y redactar el contenido técnico faltante.",
                ))

            # Búsqueda de campos de encabezado críticos dejados con guiones bajos en blanco (ej: Fecha: ____, Rev. No.: ____)
            blank_header = re.search(
                r'\b(?:Date|Fecha|Rev\.?\s*No\.?|Lot\s*No\.?|Batch\s*No\.?|Effective\s+Date|Approved\s+by)\s*[:\-]?\s*_{3,}',
                text,
                re.IGNORECASE
            )
            if blank_header:
                findings.append(Finding(
                    id=f"STR_BLANK_HEADER_{doc_name}_{page_num}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity.CRITICAL,
                    category=Category.VISUAL_STRUCTURE,
                    title="Campo de Control Documental en Blanco (Guiones Bajos '___')",
                    description=(
                        f"En la página {page_num} se detectó un campo de control o trazabilidad sin llenar: "
                        f"'{blank_header.group(0).strip()}'. DIGEMID exige documentos controlados con fecha, versión y aprobación vigentes."
                    ),
                    detected_text=blank_header.group(0).strip(),
                    expected_text="Valor real diligenciado (fecha, revisión o número de lote)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ISO 13485:2016",
                    remediation_advice="Completar el campo vacío en la plantilla controlada antes de exportar a PDF.",
                ))

        return findings

    def _check_complies_only_tables(
        self,
        doc_name: str,
        tables_data: List[Dict[str, Any]],
        pages_text: Dict[int, str]
    ) -> List[Finding]:
        findings = []

        # Analizar si es un reporte de validación, ensayo, COA, GSPR o biocompatibilidad
        doc_lower = doc_name.lower()
        if not any(k in doc_lower for k in [
            "sterilization", "esterilizacion", "esterilización", "validation", "validacion",
            "dvr", "verification", "verificacion", "coa", "analysis", "analisis", "análisis",
            "gspr", "biocompat", "stability", "estabilidad"
        ]):
            return findings

        for t_info in tables_data:
            page_num = t_info.get("page", 1)
            rows = t_info.get("rows", [])
            if len(rows) < 3:
                continue

            complies_count = 0
            total_data_cells = 0

            for r in rows[1:]:  # Omitir cabecera
                for cell in r:
                    val = str(cell).strip().lower()
                    if val in ["complies", "cumple", "pass", "ok"]:
                        complies_count += 1
                    if len(val) > 0:
                        total_data_cells += 1

            # Si más del 70% de las celdas de datos son simplemente "Complies" sin valores numéricos ni evidencias
            if total_data_cells >= 4 and (complies_count / total_data_cells) >= 0.70:
                findings.append(Finding(
                    id=f"STR_COMPLIES_ONLY_{doc_name}_{page_num}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity.CRITICAL,
                    category=Category.VISUAL_STRUCTURE,
                    title="Tabla Técnica con Relleno Exclusivo 'Complies' Sin Datos Cuantitativos ni Evidencia",
                    description=(
                        f"En la página {page_num}, la tabla técnica contiene {complies_count} celdas marcadas "
                        "únicamente como 'Complies/Cumple', sin reportar valores reales medidos, fechas de corrida, "
                        "números de lote ni código de documento de respaldo. "
                        "DIGEMID observa protocolos y checklists GSPR que no demuestran trazabilidad cuantitativa real."
                    ),
                    detected_text=f"{complies_count} de {total_data_cells} celdas dicen solo 'Complies'",
                    expected_text="Parámetros reales: Lote, fecha, valor numérico medido y referencia exacta de informe",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130° / D.S. 003-2020-SA",
                    remediation_advice="Reemplazar 'Complies' por datos cuantitativos específicos y trazables a los reportes de laboratorio.",
                ))
                break  # Una alerta por tabla/documento es suficiente

        return findings

    def _check_promised_annexes(
        self,
        doc_name: str,
        pages_text: Dict[int, str],
        full_doc_text: str,
        all_document_names: Set[str]
    ) -> List[Finding]:
        findings = []

        # Expresiones regulares para promesas de anexos
        annex_patterns = [
            (
                r'Annexure\s+(\d+|[A-Z0-9]+)\s+(?:CV\s+)?(?:is\s+)?attached',
                "Hoja de vida / Anexo prometido ({matched}) no adjunto"
            ),
            (
                r'PMS\s+Report\s+attached',
                "Reporte de Vigilancia Post-Comercialización (PMS) citado como adjunto pero no incorporado"
            ),
            (
                r'(?:approved\s+)?NABL(?:\s+accredited)?\s+laboratory\b[^\.\n]{0,80}\bISO\s*10993-7',
                "Reporte NABL de residuales de Óxido de Etileno (ISO 10993-7) prometido pero no adjunto"
            ),
            (
                r'Anexo\s+IN-DM-\d+',
                "Referencia a Anexo IN-DM no adjunto o inexistente"
            ),
        ]

        full_lower = full_doc_text.lower()
        all_docs_lower = [d.lower() for d in all_document_names]

        for page_num, text in pages_text.items():
            for pat, desc_template in annex_patterns:
                for match in re.finditer(pat, text, re.IGNORECASE):
                    matched_str = match.group(0)

                    # Verificar si existe como encabezado dentro del propio PDF o como archivo independiente
                    is_found = False

                    # Si es NABL ISO 10993-7
                    if "10993-7" in matched_str:
                        if not any("nabl" in d or "residual" in d or "10993-7" in d for d in all_docs_lower):
                            if not re.search(r'\b(?:mg/device|µg/device|ug/device|mg/dispositivo)\b', full_lower):
                                findings.append(Finding(
                                    id=f"ANNEX_MISSING_NABL_{doc_name}_{page_num}",
                                    document_name=doc_name,
                                    page=page_num,
                                    severity=Severity.FATAL,
                                    category=Category.VISUAL_STRUCTURE,
                                    title="Reporte de Ensayos Residuales de EO (ISO 10993-7) Prometido pero Ausente",
                                    description=(
                                        f"En la página {page_num} se afirma haber enviado muestras a un laboratorio NABL "
                                        "para ensayos de residuales bajo ISO 10993-7, pero no se adjunta el informe analítico "
                                        "ni se reportan los valores cuantitativos de óxido de etileno (EO) y etilenclorhidrina (ECH). "
                                        "Esto es motivo de rechazo directo por DIGEMID."
                                    ),
                                    detected_text=matched_str,
                                    expected_text="Informe analítico completo del laboratorio NABL con límites según ISO 10993-7",
                                    digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ISO 10993-7",
                                    remediation_advice="Adjuntar el informe de ensayo de residuales emitido por el laboratorio NABL acreditado.",
                                ))

                    elif "annexure" in matched_str.lower():
                        m_id = re.search(r'Annexure\s+(\d+|[A-Z0-9]+)', matched_str, re.IGNORECASE)
                        annex_id = m_id.group(1) if m_id else ""
                        if f"annexure {annex_id.lower()}" not in full_lower.replace(matched_str.lower(), ""):
                            findings.append(Finding(
                                id=f"ANNEX_MISSING_{annex_id}_{doc_name}_{page_num}",
                                document_name=doc_name,
                                page=page_num,
                                severity=Severity.CRITICAL,
                                category=Category.VISUAL_STRUCTURE,
                                title=f"Anexo Citado como Adjunto Ausente (Annexure {annex_id})",
                                description=(
                                    f"En la página {page_num} el texto declara '{matched_str}', "
                                    f"pero dicho anexo no se encuentra al final del documento ni como archivo adjunto."
                                ),
                                detected_text=matched_str,
                                expected_text=f"Anexo {annex_id} completo incorporado al final del documento",
                                digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                                remediation_advice=f"Incorporar físicamente el Annexure {annex_id} prometido en el índice y anexo.",
                            ))

                    elif "pms report" in matched_str.lower():
                        has_pms_doc = any("pms" in d or "post-market" in d or "vigilancia" in d for d in all_docs_lower)
                        has_pms_section = bool(re.search(r'\b(?:post[- ]market\s+surveillance|pms\s+data|vigilancia\s+post)\b', full_lower.replace(matched_str.lower(), "")))
                        if not has_pms_doc and not has_pms_section:
                            findings.append(Finding(
                                id=f"ANNEX_MISSING_PMS_{doc_name}_{page_num}",
                                document_name=doc_name,
                                page=page_num,
                                severity=Severity.CRITICAL,
                                category=Category.VISUAL_STRUCTURE,
                                title="Reporte PMS (Post-Market Surveillance) Prometido pero Ausente",
                                description=(
                                    f"En la página {page_num} se cita '{matched_str}', pero el reporte de vigilancia "
                                    "post-comercialización (PMS) no fue incorporado ni cargado en el paquete."
                                ),
                                detected_text=matched_str,
                                expected_text="Reporte PMS / PSUR completo firmado adjunto al expediente",
                                digemid_norm_ref="D.S. 016-2011-SA Art. 130° / MEDDEV 2.7/1",
                                remediation_advice="Adjuntar el Reporte PMS completo o retirar la mención de anexo si no aplica.",
                            ))

                    elif "in-dm-" in matched_str.lower():
                        anx_clean = matched_str.lower()
                        if anx_clean not in full_lower.replace(anx_clean, "") and not any(anx_clean in d for d in all_docs_lower):
                            findings.append(Finding(
                                id=f"ANNEX_MISSING_INDM_{doc_name}_{page_num}",
                                document_name=doc_name,
                                page=page_num,
                                severity=Severity.CRITICAL,
                                category=Category.VISUAL_STRUCTURE,
                                title=f"Anexo Citado No Encontrado ({matched_str})",
                                description=(
                                    f"En la página {page_num} se referencia '{matched_str}', "
                                    "sin que exista dicho anexo dentro del archivo ni en los documentos cargados."
                                ),
                                detected_text=matched_str,
                                expected_text=f"Documento o sección '{matched_str}' debidamente incorporada",
                                digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                                remediation_advice=f"Adjuntar o armonizar el código del {matched_str}.",
                            ))

        return findings

    def _check_section_numbering(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings = []

        # Extraer numerales tipo 1.1, 1.2, 1.3... o 1.0, 2.0... o 1, 2, 3
        sections = []
        for page_num, text in pages_text.items():
            lines = text.split("\n")
            for line in lines:
                m = re.match(r'^(?:Sec(?:tion)?\.?\s*)?(\d+(?:\.\d+)*)\s+[A-Z]', line.strip())
                if m:
                    sec_str = m.group(1)
                    sections.append((page_num, sec_str))

        if len(sections) >= 2:
            prev_main = None
            for p_num, s_str in sections:
                parts = s_str.split(".")
                if parts[0].isdigit():
                    curr_main = int(parts[0])
                    if prev_main is not None:
                        if curr_main > prev_main + 1 and curr_main <= prev_main + 5:
                            findings.append(Finding(
                                id=f"STR_SEC_JUMP_{doc_name}_{p_num}_{prev_main}_{curr_main}",
                                document_name=doc_name,
                                page=p_num,
                                severity=Severity.MINOR,
                                category=Category.VISUAL_STRUCTURE,
                                title=f"Salto Errático en Numeración de Secciones ({prev_main} a {curr_main})",
                                description=(
                                    f"En la página {p_num} la numeración pasa bruscamente de la sección {prev_main} "
                                    f"a la sección {curr_main}, omitiendo el numeral correlativo intermedio."
                                ),
                                detected_text=f"Salto de sección: {prev_main} -> {curr_main}",
                                expected_text=f"Sección correlativa {prev_main + 1}",
                                digemid_norm_ref="Formato y consistencia documental",
                                remediation_advice="Renumerar los títulos de sección correlativamente.",
                            ))
                            break
                    prev_main = curr_main

        return findings

    def _check_page_count_discrepancy(
        self,
        doc_name: str,
        pages_text: Dict[int, str],
        total_pages: int = None
    ) -> List[Finding]:
        """Detecta discrepancias entre la foliación declarada en el pie de página y las páginas reales del archivo."""
        findings = []
        actual_pages = total_pages if total_pages is not None else len(pages_text)
        if actual_pages == 0:
            return findings

        declared_totals = set()
        samples = []
        for p_num, text in pages_text.items():
            matches = re.finditer(
                r'\b(?:P[aá]gina|P[aá]g\.?|Page)\s*[:\-_]?\s*(\d+)\s*(?:de|of|\/)\s*(\d+)\b',
                text,
                re.IGNORECASE
            )
            for m in matches:
                curr_p = int(m.group(1))
                dec_total = int(m.group(2))
                declared_totals.add(dec_total)
                samples.append((p_num, m.group(0), curr_p, dec_total))

        for dec_total in declared_totals:
            if dec_total > actual_pages and abs(dec_total - actual_pages) >= 1:
                # Faltan páginas físicas en el documento digital
                first_sample = next(s for s in samples if s[3] == dec_total)
                findings.append(Finding(
                    id=f"STR_MISSING_PAGES_{doc_name}",
                    document_name=doc_name,
                    page=first_sample[0],
                    severity=Severity.FATAL,
                    category=Category.VISUAL_STRUCTURE,
                    title="Foliación Incompleta: Páginas Faltantes en el Documento Digital",
                    description=(
                        f"El pie de página declara '{first_sample[1]}' indicando un total de {dec_total} páginas, "
                        f"pero el archivo digital únicamente contiene {actual_pages} páginas. "
                        f"Se han omitido físicamente {dec_total - actual_pages} página(s). DIGEMID rechaza de plano "
                        "cualquier expediente presentado con documentos incompletos o truncados (Art. 130 D.S. 016-2011-SA)."
                    ),
                    detected_text=f"Declarado: {first_sample[1]} vs Páginas Reales del Archivo: {actual_pages}",
                    expected_text=f"Archivo íntegro con las {dec_total} páginas completas",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130° / Ley N° 29459",
                    remediation_advice="Solicitar al fabricante o escanear el documento íntegro con todas sus páginas correlativas.",
                ))
            elif actual_pages > dec_total and (actual_pages - dec_total) >= 2:
                # Hay más páginas que las declaradas en el pie de página
                first_sample = next(s for s in samples if s[3] == dec_total)
                findings.append(Finding(
                    id=f"STR_PAGE_COUNT_MISMATCH_{doc_name}",
                    document_name=doc_name,
                    page=first_sample[0],
                    severity=Severity.CRITICAL,
                    category=Category.VISUAL_STRUCTURE,
                    title="Descalce en Foliación Declarada vs Páginas Reales del Archivo",
                    description=(
                        f"El pie de página declara '{first_sample[1]}' ({dec_total} páginas), "
                        f"mientras que el archivo contiene {actual_pages} páginas. La foliación está desfasada "
                        "o se incorporaron anexos/hojas adicionales sin actualizar el pie de página."
                    ),
                    detected_text=f"Pie de página: {first_sample[1]} vs Total de páginas en PDF: {actual_pages}",
                    expected_text=f"Pie de página actualizado a 'Página X de {actual_pages}'",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                    remediation_advice="Revisar y armonizar la foliación del documento para que coincida con el total de páginas.",
                ))

        return findings
