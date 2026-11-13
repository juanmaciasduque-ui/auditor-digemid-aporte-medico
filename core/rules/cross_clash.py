"""
Motor de Concordancia Cruzada (Cross-Document Consistency Engine) y Contradicciones Internas.
Cubre el Catálogo C:
- Contradicción interna en el mismo archivo (2 vs 3 semiciclos de esterilización, fecha de expiración NO/YES).
- Descalce dimensional (Calibres Fr y Longitudes cm entre CLV, DVR, CER y rotulados).
- Descalce de vida útil (3 años vs 5 años vs 1 día).
- Descalce de tiempo de permanencia clínica (<25 días vs 30-90 días vs >30 días / implante vs 6 meses).
- Descalce de componentes del Set (CER 'no components' vs Carta/Rótulo 'Set con guía, pusher, clamp').
- Contaminación por copia clínica (Bottle/grenade type, Gastro-enterological, Umbilical cord clamp, Foley 8Fr-28Fr/balón 3-50ml).
"""

import re
from typing import List, Dict, Tuple, Optional
from core.models import Finding, Severity, Category, ExtractedParameters, DocumentReport
from config import MASTER_SPECIFICATIONS


class CrossDocumentConsistencyEngine:
    """Motor de análisis de concordancia cruzada y contaminación documental."""

    def extract_document_parameters(self, doc_name: str, pages_text: Dict[int, str]) -> ExtractedParameters:
        """Extrae parámetros numéricos y clínicos clave de un documento individual."""
        params = ExtractedParameters()
        full_text = " ".join(pages_text.values())

        # 1. Extracción de diámetros Fr
        # Patrones: '2-12 Fr', '3 - 8 Fr', '3 to 8 Fr', '3Fr to 8Fr', '3-10 Fr', '8Fr - 28Fr'
        fr_matches = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:[-–to]|a)\s*(\d+(?:\.\d+)?)\s*(?:Fr|FG|CH)\b', full_text, re.IGNORECASE)
        all_frs = []
        for low_s, high_s in fr_matches:
            try:
                low = float(low_s)
                high = float(high_s)
                all_frs.extend([low, high])
            except ValueError:
                pass
        if all_frs:
            params.diameters_fr = [min(all_frs), max(all_frs)]
            params.diameters_fr_raw = f"{min(all_frs)}–{max(all_frs)} Fr"

        # 2. Extracción de longitudes en cm
        # Patrones: '6-32 cm', '8 to 30 cm', '70-90 cm', '06 - 32 cm'
        cm_matches = re.findall(r'\b(\d+)\s*(?:[-–to]|a)\s*(\d+)\s*cm\b', full_text, re.IGNORECASE)
        all_cms = []
        for low_s, high_s in cm_matches:
            try:
                low = float(low_s)
                high = float(high_s)
                all_cms.extend([low, high])
            except ValueError:
                pass
        if all_cms:
            params.lengths_cm = [min(all_cms), max(all_cms)]
            params.lengths_cm_raw = f"{min(all_cms)}–{max(all_cms)} cm"

        # 3. Extracción de vida útil (shelf life)
        # Buscar: '3 years', '3 años', '5 years', '5 años', '60 months', '36 months', '1 day', '1 día'
        if re.search(r'\b(?:1\s*d[ií]a|1\s*day)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = round(1 / 30, 2)
            params.shelf_life_raw = "1 día"
        elif re.search(r'\b(?:3\s*years?|3\s*a[ñn]os?|36\s*months?|36\s*meses)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = 36
            params.shelf_life_raw = "3 años (36 meses)"
        elif re.search(r'\b(?:5\s*years?|5\s*a[ñn]os?|60\s*months?|60\s*meses)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = 60
            params.shelf_life_raw = "5 años (60 meses)"

        # 4. Extracción de tiempo de permanencia clínica (indwelling time)
        # '25 days', '30-90 days', '> 30 days', 'permanent implant', '6 months'
        if re.search(r'\b(?:not\s+to\s+be\s+kept\s+indwelling\s+for\s+more\s+than\s+25\s+days|menos\s+de\s+25\s+d[ií]as|25\s*d[ií]as?)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 25
            params.indwelling_time_raw = "< 25 días"
        elif re.search(r'\b(?:30\s*[-–to]\s*90\s*days?|30\s*[-–a]\s*90\s*d[ií]as?)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 90
            params.indwelling_time_raw = "30–90 días"
        elif re.search(r'\b(?:6\s*months?|6\s*meses)\b[^\.\n]{0,40}\b(?:indwelling|permanencia)\b', full_text, re.IGNORECASE) or \
             re.search(r'\b(?:indwelling|permanencia)\b[^\.\n]{0,40}\b(?:6\s*months?|6\s*meses)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 180
            params.indwelling_time_raw = "6 meses"
        elif re.search(r'\b(?:Permanent\s+Exposure|\>\s*30\s*days|Implant\s+Device)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 365
            params.indwelling_time_raw = "> 30 días / Implante Permanente"

        # 5. Detección de componentes del Set
        if re.search(r'\b(?:doesn\'?t\s+contain\s+any\s+components?|no\s+contains?\s+any\s+components?|sin\s+componentes)\b', full_text, re.IGNORECASE):
            params.components.append("NO_COMPONENTS_DECLARED")
        if re.search(r'\b(?:guidewire|gu[ií]a\s+hidrof[ií]lica|PTFE\s+guidewire)\b', full_text, re.IGNORECASE):
            params.components.append("Guía")
        if re.search(r'\b(?:pusher|posicionador|empujador)\b', full_text, re.IGNORECASE):
            params.components.append("Empujador")
        if re.search(r'\b(?:clamp|pinza)\b', full_text, re.IGNORECASE):
            params.components.append("Clamp")
        if re.search(r'\b(?:suture|thread|hilo\s+de\s+sujeci[oó]n)\b', full_text, re.IGNORECASE):
            params.components.append("Sutura")

        # 6. Detección de Contaminaciones Clínicas (Copy-Paste de otros productos)
        if re.search(r'\b(?:Bottle/grenade\s+type|botella/granada|grenade\s+type)\b', full_text, re.IGNORECASE):
            params.foreign_contaminations.append("Bottle/grenade type (Drenaje quirúrgico)")
        if re.search(r'\b(?:Gastro-enterological|gastroenterolog[ií]a|endoscopic\s+gastro)\b', full_text, re.IGNORECASE):
            params.foreign_contaminations.append("Gastro-enterological procedures (Gastroenterología)")
        if re.search(r'\b(?:Umbilical\s+cord\s+clamp|clamp\s+de\s+cord[oó]n\s+umbilical)\b', full_text, re.IGNORECASE):
            params.foreign_contaminations.append("Umbilical cord clamp (Abrazadera de cordón umbilical)")
        if re.search(r'\b(?:balloon\s*3\s*[-–to]\s*50\s*ml|bal[oó]n\s*3\s*[-–a]\s*50\s*ml|Foley\s+balloon)\b', full_text, re.IGNORECASE):
            params.foreign_contaminations.append("Foley Balloon Catheter (Catéter con balón)")

        return params

    def check_internal_contradictions(self, doc_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        """Detecta contradicciones dentro del mismo documento."""
        findings: List[Finding] = []

        # 1. Contradicción numérica de semiciclos de esterilización (ej: pág 2 dice 2 semiciclos, pág 3 dice 3 semiciclos)
        two_half = []
        three_half = []
        for p_num, text in pages_text.items():
            if re.search(r'\b2\s+half\s+cycles?\b|\bdos\s+semiciclos?\b', text, re.IGNORECASE):
                two_half.append(p_num)
            if re.search(r'\b3\s+half\s+cycles?\b|\bthree\s+half\s+cycles?\b|\btres\s+semiciclos?\b', text, re.IGNORECASE):
                three_half.append(p_num)

        if two_half and three_half:
            findings.append(Finding(
                id=f"INT_HALF_CYCLES_{doc_name}",
                document_name=doc_name,
                page=three_half[0],
                severity=Severity.FATAL,
                category=Category.CROSS_DOCUMENT,
                title="Contradicción Interna de Semiciclos de Esterilización en el Mismo Informe",
                description=(
                    f"El documento declara en la página {two_half[0]} haber ejecutado '2 half cycles' (2 semiciclos), "
                    f"mientras que en la página {three_half[0]} (y Tabla 1) afirma 'Three half cycles' (3 semiciclos). "
                    "DIGEMID considera que esta discrepancia invalida la reproducibilidad del protocolo de esterilización."
                ),
                detected_text=f"Pág {two_half[0]}: 2 semiciclos vs Pág {three_half[0]}: 3 semiciclos",
                expected_text="Cifra única y consistente de semiciclos validados (ej: 2 o 3 en todo el protocolo)",
                digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ISO 11135",
                remediation_advice="Uniformar el número exacto de semiciclos ejecutados en todas las secciones y tablas.",
            ))

        # 2. Contradicción de fecha de expiración en rótulo en GSPR (NO vs YES)
        gspr_no_exp = []
        gspr_yes_exp = []
        for p_num, text in pages_text.items():
            if re.search(r'expiration\s+date[^\.\n]{0,50}\bNO\b', text, re.IGNORECASE):
                gspr_no_exp.append(p_num)
            if re.search(r'expiration\s+date[^\.\n]{0,50}\bYES\b', text, re.IGNORECASE):
                gspr_yes_exp.append(p_num)

        if gspr_no_exp and gspr_yes_exp:
            findings.append(Finding(
                id=f"INT_GSPR_EXP_{doc_name}",
                document_name=doc_name,
                page=gspr_no_exp[0],
                severity=Severity.CRITICAL,
                category=Category.CROSS_DOCUMENT,
                title="Contradicción Interna en Checklist GSPR (Fecha de Expiración en Rótulo)",
                description=(
                    f"En la página {gspr_no_exp[0]} se marcó 'NO' a la inclusión de fecha de expiración en rótulo, "
                    f"mientras que en la página {gspr_yes_exp[0]} se indica 'YES'. "
                    "Para productos estériles de un solo uso la fecha de caducidad es obligatoria."
                ),
                detected_text=f"Pág {gspr_no_exp[0]}: NO vs Pág {gspr_yes_exp[0]}: YES",
                expected_text="Marcar 'YES' con justificación de rotulado conforme a D.S. 016-2011-SA Art. 137°",
                digemid_norm_ref="D.S. 003-2020-SA / D.S. 016-2011-SA Art. 137°",
                remediation_advice="Corregir a 'YES' indicando que el envase primario y secundario portan fecha de caducidad.",
            ))

        # 3. Contaminación por copia clínica dentro del documento
        for p_num, text in pages_text.items():
            if "bottle/grenade" in text.lower():
                findings.append(Finding(
                    id=f"CONTAM_GRENADE_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.FATAL,
                    category=Category.CROSS_DOCUMENT,
                    title="Contaminación por Copia Clínica: 'Bottle/grenade type' (Drenaje Quirúrgico)",
                    description=(
                        f"En la página {p_num} el documento afirma que el dispositivo es de tipo 'Bottle/grenade' "
                        "(tipo granada o botella de fuelle), correspondiente a un sistema de drenaje quirúrgico cerrado "
                        "y no a un catéter/stent endoureteral Doble J. Esto evidencia copia y edición indebida de otro archivo."
                    ),
                    detected_text="Similar device design: Bottle/grenade type",
                    expected_text="Double J / Double Pigtail Ureteral Stent",
                    digemid_norm_ref="Ley N° 29459 / Principio de Veracidad Documental",
                    remediation_advice="Eliminar toda referencia a 'Bottle/grenade' y describir exclusivamente el stent ureteral.",
                ))

            if "gastro-enterological" in text.lower():
                findings.append(Finding(
                    id=f"CONTAM_GASTRO_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.FATAL,
                    category=Category.CROSS_DOCUMENT,
                    title="Contaminación por Copia Clínica: Procedimientos Gastroenterológicos en Dispositivo Urológico",
                    description=(
                        f"En la página {p_num} se indica que el dispositivo está indicado para 'Gastro-enterological "
                        "Endoscopic procedures'. Un stent ureteral es estrictamente urológico (riñón/uréter/vejiga). "
                        "DIGEMID deniega expedientes que mezclan especialidades clínicas incompatibles."
                    ),
                    detected_text="Gastro-enterological Endoscopic procedures",
                    expected_text="Urological endoscopic procedures (Ureteroscopy / Cystoscopy)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                    remediation_advice="Corregir a indicaciones estrictamente urológicas en el GSPR.",
                ))

            if "umbilical cord clamp" in text.lower():
                findings.append(Finding(
                    id=f"CONTAM_UMBILICAL_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.FATAL,
                    category=Category.CROSS_DOCUMENT,
                    title="Contaminación de Componentes: 'Umbilical cord clamp' en Kit de Stent Ureteral",
                    description=(
                        f"En la página {p_num} se declara que el Set incluye 'Umbilical cord clamp' "
                        "(abrazadera de cordón umbilical). Es un despropósito médico y técnico en un catéter urológico adulto."
                    ),
                    detected_text="Kit Contain: ... Umbilical cord clamp",
                    expected_text="Urological clamp / Guidewire clamp (o eliminar si no corresponde)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                    remediation_advice="Reemplazar por pinza de guía urológica y justificar su función en el Set.",
                ))

            if re.search(r'\b(?:Foley\s+balloon|bal[oó]n\s*3\s*[-–a]\s*50\s*ml)\b', text, re.IGNORECASE):
                findings.append(Finding(
                    id=f"CONTAM_FOLEY_{doc_name}_{p_num}",
                    document_name=doc_name,
                    page=p_num,
                    severity=Severity.FATAL,
                    category=Category.CROSS_DOCUMENT,
                    title="Infiltración de Otro Dispositivo: Tablas de Catéter Balón Foley (8Fr–28Fr)",
                    description=(
                        f"En la página {p_num} se insertaron especificaciones de Catéter Foley con balón de 3–50 ml "
                        "y calibres de hasta 28 Fr. Esto contamina el expediente de Catéteres Ureterales Doble J."
                    ),
                    detected_text="Catéter balón Foley / Balón 3-50 ml / 8Fr-28Fr",
                    expected_text="Catéter Ureteral Doble J (3-8 Fr, sin balón de retención)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                    remediation_advice="Eliminar por completo las páginas y tablas correspondientes al catéter Foley.",
                ))

        return findings

    def check_batch_consistency(self, doc_reports: Dict[str, DocumentReport]) -> List[Finding]:
        """
        Ejecuta la auditoría cruzada global entre todos los documentos del lote.
        Compara medidas Fr, longitudes cm, vida útil, permanencia clínica y componentes del Set.
        """
        cross_findings: List[Finding] = []

        # 1. Comparación de Diámetros Fr entre Documentos
        fr_by_doc: Dict[str, Tuple[float, float, str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.diameters_fr:
                fr_by_doc[name] = (
                    rep.parameters.diameters_fr[0],
                    rep.parameters.diameters_fr[-1],
                    rep.parameters.diameters_fr_raw
                )

        if len(fr_by_doc) >= 2:
            items = list(fr_by_doc.items())
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    doc1, (min1, max1, raw1) = items[i]
                    doc2, (min2, max2, raw2) = items[j]
                    # Si difieren significativamente (ej: 2-12 Fr vs 3-8 Fr)
                    if abs(min1 - min2) >= 0.5 or abs(max1 - max2) >= 1.0:
                        cross_findings.append(Finding(
                            id=f"CROSS_FR_CLASH_{i}_{j}",
                            document_name=f"{doc1} vs {doc2}",
                            page=None,
                            severity=Severity.FATAL,
                            category=Category.CROSS_DOCUMENT,
                            title="Descalce Dimensional en Calibres Fr entre Documentos del Expediente",
                            description=(
                                f"Existe discrepancia en el rango de calibres declarado: "
                                f"'{doc1}' declara {raw1}, mientras que '{doc2}' declara {raw2}. "
                                "DIGEMID exige que el Certificado de Libre Venta (CLV), la Verificación de Diseño (DVR), "
                                "la Evaluación Clínica (CER), el rotulado y la solicitud DISMED coincidan exactamente."
                            ),
                            detected_text=f"{doc1}: {raw1} | {doc2}: {raw2}",
                            expected_text="Rango dimensional único aprobado y respaldado en todos los documentos",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 126° y 130°",
                            remediation_advice="Definir con el fabricante una matriz de calibres Fr idéntica en el 100% de documentos.",
                        ))

        # 2. Infiltración de Longitud de Catéter Ureteral (70–90 cm)
        for name, rep in doc_reports.items():
            if rep.parameters.lengths_cm:
                min_l, max_l = rep.parameters.lengths_cm[0], rep.parameters.lengths_cm[-1]
                if max_l >= 60.0: # Longitudes de 70 a 90 cm
                    cross_findings.append(Finding(
                        id=f"CROSS_LENGTH_INFILTRATION_{name}",
                        document_name=name,
                        page=None,
                        severity=Severity.FATAL,
                        category=Category.CROSS_DOCUMENT,
                        title="Infiltración de Producto Distinto: Longitud de 70–90 cm (Ureteral Catheter)",
                        description=(
                            f"En '{name}' se reportan longitudes de {rep.parameters.lengths_cm_raw}. "
                            "Los catéteres Doble J para implantación ureteral miden típicamente entre 6 y 32 cm. "
                            "Las longitudes de 70 a 90 cm corresponden a 'Ureteral Catheters' simples de drenaje externo. "
                            "Esta mezcla motivó la observación directa en la Notificación N° 2026068505 (Ítems 4.1 - 4.4)."
                        ),
                        detected_text=f"Longitud: {rep.parameters.lengths_cm_raw}",
                        expected_text="6 a 32 cm (rango propio de Catéter Doble J)",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                        remediation_advice="Eliminar las especificaciones de 70-90 cm del expediente de Stents Doble J.",
                    ))

        # 3. Descalce de Vida Útil (Shelf Life)
        shelf_by_doc: Dict[str, Tuple[float, str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.shelf_life_months is not None:
                shelf_by_doc[name] = (rep.parameters.shelf_life_months, rep.parameters.shelf_life_raw)

        if len(shelf_by_doc) >= 2:
            items_s = list(shelf_by_doc.items())
            for i in range(len(items_s)):
                for j in range(i + 1, len(items_s)):
                    doc1, (m1, raw1) = items_s[i]
                    doc2, (m2, raw2) = items_s[j]
                    if abs(m1 - m2) >= 1.0:
                        cross_findings.append(Finding(
                            id=f"CROSS_SHELF_LIFE_CLASH_{i}_{j}",
                            document_name=f"{doc1} vs {doc2}",
                            page=None,
                            severity=Severity.FATAL,
                            category=Category.CROSS_DOCUMENT,
                            title="Descalce Severo de Vida Útil entre Documentos (Shelf Life Mismatch)",
                            description=(
                                f"Inconsistencia crítica en la vida útil: '{doc1}' declara {raw1}, "
                                f"mientras que '{doc2}' indica {raw2}. "
                                "Declarar vidas útiles dispares (ej. 3 años en DVR vs 5 años en lotes analizados vs 1 día en borrador) "
                                "es causal inmediata de denegatoria por no sustentar la estabilidad del producto estéril."
                            ),
                            detected_text=f"{doc1}: {raw1} | {doc2}: {raw2}",
                            expected_text="Vida útil única y sustentada (ej: 36 meses o 60 meses con reporte de estabilidad)",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ASTM F1980 / ISO 11607",
                            remediation_advice="Alinear la vida útil en DVR, Ficha Técnica, Rótulos e Informe Técnico según el estudio real.",
                        ))

        # 4. Descalce de Tiempo de Permanencia Clínica (Indwelling Time)
        indw_by_doc: Dict[str, Tuple[float, str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.indwelling_time_days is not None:
                indw_by_doc[name] = (rep.parameters.indwelling_time_days, rep.parameters.indwelling_time_raw)

        if len(indw_by_doc) >= 2:
            items_ind = list(indw_by_doc.items())
            for i in range(len(items_ind)):
                for j in range(i + 1, len(items_ind)):
                    doc1, (d1, raw1) = items_ind[i]
                    doc2, (d2, raw2) = items_ind[j]
                    if abs(d1 - d2) >= 20.0:
                        cross_findings.append(Finding(
                            id=f"CROSS_INDWELLING_CLASH_{i}_{j}",
                            document_name=f"{doc1} vs {doc2}",
                            page=None,
                            severity=Severity.FATAL,
                            category=Category.CROSS_DOCUMENT,
                            title="Discrepancia en Tiempo de Permanencia Clínica (Indwelling Time)",
                            description=(
                                f"Conflicto clínico mayor: '{doc1}' declara {raw1}, mientras que '{doc2}' declara {raw2}. "
                                "Declarar tiempos de permanencia contradictorios (<25 días, 30–90 días, >30 días / implante permanente o 6 meses) "
                                "modifica la regla de clasificación de riesgo y la batería requerida de ensayos de biocompatibilidad ISO 10993."
                            ),
                            detected_text=f"{doc1}: {raw1} | {doc2}: {raw2}",
                            expected_text="Definición clínica unívoca del tiempo de permanencia según material",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ISO 10993-1",
                            remediation_advice="Definir si el registro ampara uso temporal (≤30 días) o prolongado (30-90 días) con sus estudios respectivos.",
                        ))

        # 5. Descalce de Componentes del Set (Set vs "No Components")
        has_set_declaration = any(
            any(comp in ["Guía", "Empujador", "Clamp", "Sutura"] for comp in rep.parameters.components) or "set" in name.lower()
            for name, rep in doc_reports.items()
        )
        has_no_components = any(
            "NO_COMPONENTS_DECLARED" in rep.parameters.components
            for name, rep in doc_reports.items()
        )

        if has_set_declaration and has_no_components:
            cer_docs = [n for n, r in doc_reports.items() if "NO_COMPONENTS_DECLARED" in r.parameters.components]
            cross_findings.append(Finding(
                id="CROSS_SET_COMPONENTS_CONTRADICTION",
                document_name=", ".join(cer_docs),
                page=None,
                severity=Severity.FATAL,
                category=Category.CROSS_DOCUMENT,
                title="Descalce Crítico de Componentes del Set: CER Niega Componentes",
                description=(
                    "El expediente tramita la denominación 'SET' (catéter, guía hidrofílica, empujador, clamp, hilo), "
                    f"pero en el documento {', '.join(cer_docs)} se declara literalmente que el producto "
                    "'doesn't contain any components'. Esta contradicción directa fue observada en el Exp. 25157794."
                ),
                detected_text="CER declara: 'doesn't contain any components' vs Título/Carta: 'SET con 5 componentes'",
                expected_text="Evaluación clínica (CER) que cubra el Set completo y cada uno de sus accesorios",
                digemid_norm_ref="D.S. 016-2011-SA Art. 126° y 130°",
                remediation_advice="Actualizar el CER para que evalúe y liste explícitamente todos los componentes del Set.",
            ))

        return cross_findings
