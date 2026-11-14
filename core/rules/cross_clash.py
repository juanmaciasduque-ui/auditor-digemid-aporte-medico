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
        """Extrae parámetros universales numéricos y clínicos de cualquier tipo de dispositivo médico."""
        params = ExtractedParameters()
        full_text = " ".join(pages_text.values())

        # 0. Identificación automática del producto
        if re.search(r'\b(?:cinta\s+vaginal|sling|malla|mesh|incontinencia)\b', full_text, re.IGNORECASE):
            params.detected_product_name = "Cinta Vaginal / Malla Quirúrgica"
            params.detected_risk_class = "Clase III (Implante Quirúrgico)"
        elif re.search(r'\b(?:cat[eé]ter\s+ureteral|stent\s+ureteral|doble\s*j|pigtail)\b', full_text, re.IGNORECASE):
            params.detected_product_name = "Catéter / Stent Ureteral Doble J"
            params.detected_risk_class = "Clase III (Invasivo Quirúrgico)"
        elif re.search(r'\b(?:asa\s+de\s+resecci[oó]n|resection\s+loop|electrodo)\b', full_text, re.IGNORECASE):
            params.detected_product_name = "Asa de Resección Endoscópica"
            params.detected_risk_class = "Clase IIb / III"
        elif re.search(r'\b(?:sutura|suture|poliglactina|polidioxanona)\b', full_text, re.IGNORECASE):
            params.detected_product_name = "Sutura Quirúrgica"
            params.detected_risk_class = "Clase IIb / III"
        elif re.search(r'\b(?:jeringa|syringe|aguja|needle|venoclisis)\b', full_text, re.IGNORECASE):
            params.detected_product_name = "Equipo de Infusión / Jeringa"
            params.detected_risk_class = "Clase IIa"
        else:
            params.detected_product_name = "Dispositivo Médico General"
            params.detected_risk_class = "Clase I / II / III / IV"

        # 1. Extracción de diámetros Fr
        fr_matches = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:[-–to]|a)\s*(\d+(?:\.\d+)?)\s*(?:Fr|FG|CH)\b', full_text, re.IGNORECASE)
        all_frs = []
        for low_s, high_s in fr_matches:
            try:
                all_frs.extend([float(low_s), float(high_s)])
            except ValueError:
                pass
        if all_frs:
            params.diameters_fr = [min(all_frs), max(all_frs)]
            params.diameters_fr_raw = f"{min(all_frs)}–{max(all_frs)} Fr"

        # 2. Extracción de calibres Gauge (G)
        g_matches = re.findall(r'\b(\d+)\s*(?:G|Gauge)\b', full_text, re.IGNORECASE)
        if g_matches:
            params.gauges = [int(g) for g in g_matches]
            params.gauges_raw = ", ".join(set(g_matches)) + " G"

        # 3. Extracción de dimensiones de mallas/cintas (ej: 1.1 x 50 cm, 1 x 36 cm, 10 x 15 cm)
        mesh_m = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:x|×|de\s+ancho\s+por)\s*(\d+(?:\.\d+)?)\s*(?:cm|mm)\b', full_text, re.IGNORECASE)
        if mesh_m:
            for w, l in mesh_m:
                params.mesh_dimensions.append(f"{w} x {l} cm")
        # Patrón inverso: 36 cm de largo por un/1 cm de ancho
        mesh_inv = re.findall(r'\b(\d+(?:\.\d+)?)\s*cm\s+de\s+largo\s+por\s+(?:un|1|\d+(?:\.\d+)?)\s*cm\s+de\s+ancho\b', full_text, re.IGNORECASE)
        for l in mesh_inv:
            params.mesh_dimensions.append(f"1 x {l} cm")
        # Dimensiones en reportes en inglés (Length in cm: 11 cm)
        mesh_eng = re.findall(r'Length\s*(?:in\s*cm)?\s*[:\-_]?\s*(\d+(?:\.\d+)?)\s*cms?', full_text, re.IGNORECASE)
        for l in mesh_eng:
            params.mesh_dimensions.append(f"Longitud {l} cm")

        # 4. Extracción de longitudes en cm
        cm_matches = re.findall(r'\b(\d+)\s*(?:[-–to]|a)\s*(\d+)\s*cm\b', full_text, re.IGNORECASE)
        all_cms = []
        for low_s, high_s in cm_matches:
            try:
                all_cms.extend([float(low_s), float(high_s)])
            except ValueError:
                pass
        if all_cms:
            params.lengths_cm = [min(all_cms), max(all_cms)]
            params.lengths_cm_raw = f"{min(all_cms)}–{max(all_cms)} cm"

        # 5. Extracción de vida útil (shelf life)
        if re.search(r'\b(?:1\s*d[ií]a|1\s*day)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = round(1 / 30, 2)
            params.shelf_life_raw = "1 día"
        elif re.search(r'\b(?:2\s*years?|2\s*a[ñn]os?|24\s*months?|24\s*meses)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = 24
            params.shelf_life_raw = "2 años (24 meses)"
        elif re.search(r'\b(?:3\s*years?|3\s*a[ñn]os?|36\s*months?|36\s*meses)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = 36
            params.shelf_life_raw = "3 años (36 meses)"
        elif re.search(r'\b(?:5\s*years?|5\s*a[ñn]os?|60\s*months?|60\s*meses)\b', full_text, re.IGNORECASE):
            params.shelf_life_months = 60
            params.shelf_life_raw = "5 años (60 meses)"

        # 6. Extracción de tiempo de permanencia clínica (indwelling time)
        if re.search(r'\b(?:menos\s+de\s+24\s+horas|<24\s*h|uso\s+transitorio)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 1
            params.indwelling_time_raw = "< 24 horas (Transitorio)"
        elif re.search(r'\b(?:not\s+to\s+be\s+kept\s+indwelling\s+for\s+more\s+than\s+25\s+days|menos\s+de\s+25\s+d[ií]as|25\s*d[ií]as?)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 25
            params.indwelling_time_raw = "< 25 días (Corto plazo)"
        elif re.search(r'\b(?:30\s*[-–to]\s*90\s*days?|30\s*[-–a]\s*90\s*d[ií]as?)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 90
            params.indwelling_time_raw = "30–90 días (Prolongado)"
        elif re.search(r'\b(?:6\s*months?|6\s*meses)\b[^\.\n]{0,40}\b(?:indwelling|permanencia)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 180
            params.indwelling_time_raw = "6 meses"
        elif re.search(r'\b(?:Permanent\s+Exposure|\>\s*30\s*days|Implant\s+Device|implante\s+definitivo|permanente)\b', full_text, re.IGNORECASE):
            params.indwelling_time_days = 365
            params.indwelling_time_raw = "> 30 días / Implante Permanente"

        # 7. Materiales declarados
        if re.search(r'\b(?:polyurethane|poliuretano)\b', full_text, re.IGNORECASE):
            params.materials.append("Poliuretano")
        if re.search(r'\b(?:polypropylene|polipropileno)\b', full_text, re.IGNORECASE):
            params.materials.append("Polipropileno")
        if re.search(r'\b(?:silicone|silicona)\b', full_text, re.IGNORECASE):
            params.materials.append("Silicona")
        if re.search(r'\b(?:stainless\s+steel|acero\s+inoxidable)\b', full_text, re.IGNORECASE):
            params.materials.append("Acero Inoxidable")

        # 8. Métodos de esterilización
        # Priorizar declaración explícita en encabezado o campo 'MÉTODO DE ESTERILIZACIÓN'
        explicit_steril = re.search(
            r'(?:M[EÉ]TODO\s+DE\s+ESTERILIZACI[OÓ]N|STERILIZATION\s+METHOD|ESTERILIZACION\s+A)\s*[:\-_]?\s*([^\.\n\r]+)',
            full_text,
            re.IGNORECASE
        )
        if explicit_steril:
            val_s = explicit_steril.group(1).strip()
            if re.search(r'per[oó]xido|plasma|sterrad', val_s, re.IGNORECASE):
                params.sterilization_methods.append("Peróxido de Hidrógeno (Plasma)")
            elif re.search(r'[oó]xido\s+de\s+etileno|EO|ETO', val_s, re.IGNORECASE):
                params.sterilization_methods.append("Óxido de Etileno (EO)")
            elif re.search(r'gamma|radiaci[oó]n', val_s, re.IGNORECASE):
                params.sterilization_methods.append("Radiación Gamma")
            elif re.search(r'vapor|autoclave', val_s, re.IGNORECASE):
                params.sterilization_methods.append("Vapor / Autoclave")

        if not params.sterilization_methods:
            if re.search(r'\b(?:ethylene\s+oxide|[oó]xido\s+de\s+etileno|EO\s+sterilization|ETO)\b', full_text, re.IGNORECASE):
                params.sterilization_methods.append("Óxido de Etileno (EO)")
            if re.search(r'\b(?:gamma\s+radiation|radiaci[oó]n\s+gamma|cobalt\s*60)\b', full_text, re.IGNORECASE):
                params.sterilization_methods.append("Radiación Gamma")
            if re.search(r'\b(?:steam|vapor|autoclave)\b', full_text, re.IGNORECASE):
                params.sterilization_methods.append("Vapor / Autoclave")
            if re.search(r'\b(?:per[oó]xido\s+de\s+hidr[oó]geno|hydrogen\s+peroxide|plasma|sterrad)\b', full_text, re.IGNORECASE):
                params.sterilization_methods.append("Peróxido de Hidrógeno (Plasma)")

        # 9. Componentes del Set / Kit
        if re.search(r'\b(?:doesn\'?t\s+contain\s+any\s+components?|no\s+contains?\s+any\s+components?|sin\s+componentes)\b', full_text, re.IGNORECASE):
            params.components.append("NO_COMPONENTS_DECLARED")
        if re.search(r'\b(?:guidewire|gu[ií]a\s+hidrof[ií]lica|PTFE\s+guidewire)\b', full_text, re.IGNORECASE):
            params.components.append("Guía")
        if re.search(r'\b(?:pusher|posicionador|empujador)\b', full_text, re.IGNORECASE):
            params.components.append("Empujador")
        if re.search(r'\b(?:clamp|pinza)\b', full_text, re.IGNORECASE):
            params.components.append("Clamp / Pinza")
        if re.search(r'\b(?:varilla|aguja\s+pasadora|trocar|pasador)\b', full_text, re.IGNORECASE):
            params.components.append("Varilla / Pasador")

        # 10. Contaminaciones Clínicas (Copy-Paste de otros dispositivos)
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

        # 6. Descalce de Dimensiones de Malla / Cinta Quirúrgica (Cintas Vaginales / Mallas)
        mesh_by_doc: Dict[str, Set[str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.mesh_dimensions:
                mesh_by_doc[name] = set(rep.parameters.mesh_dimensions)

        if len(mesh_by_doc) >= 2:
            m_items = list(mesh_by_doc.items())
            for i in range(len(m_items)):
                for j in range(i + 1, len(m_items)):
                    doc1, dims1 = m_items[i]
                    doc2, dims2 = m_items[j]
                    if dims1 != dims2 and not (dims1.issubset(dims2) or dims2.issubset(dims1)):
                        cross_findings.append(Finding(
                            id=f"CROSS_MESH_DIM_CLASH_{i}_{j}",
                            document_name=f"{doc1} vs {doc2}",
                            page=None,
                            severity=Severity.FATAL,
                            category=Category.CROSS_DOCUMENT,
                            title="Descalce en Dimensiones de Malla/Cinta Quirúrgica entre Documentos",
                            description=(
                                f"Inconsistencia dimensional en implante de malla/cinta: '{doc1}' declara {', '.join(sorted(dims1))}, "
                                f"mientras que '{doc2}' declara {', '.join(sorted(dims2))}. "
                                "DIGEMID exige que las medidas de la malla en el Certificado de Análisis, Ficha Técnica, "
                                "Manual IFU y Rotulado coincidan exactamente."
                            ),
                            detected_text=f"{doc1}: {', '.join(sorted(dims1))} | {doc2}: {', '.join(sorted(dims2))}",
                            expected_text="Dimensiones de malla idénticas en todos los documentos del expediente",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                            remediation_advice="Armonizar las medidas (ancho x largo en cm o mm) en toda la documentación técnica y rótulos.",
                        ))

        # 7. Descalce en Método de Esterilización
        steril_by_doc: Dict[str, Set[str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.sterilization_methods:
                steril_by_doc[name] = set(rep.parameters.sterilization_methods)

        if len(steril_by_doc) >= 2:
            st_items = list(steril_by_doc.items())
            for i in range(len(st_items)):
                for j in range(i + 1, len(st_items)):
                    doc1, m1 = st_items[i]
                    doc2, m2 = st_items[j]
                    if m1 != m2 and not (m1.issubset(m2) or m2.issubset(m1)):
                        cross_findings.append(Finding(
                            id=f"CROSS_STERILIZATION_CLASH_{i}_{j}",
                            document_name=f"{doc1} vs {doc2}",
                            page=None,
                            severity=Severity.FATAL,
                            category=Category.CROSS_DOCUMENT,
                            title="Contradicción Crítica en Método de Esterilización entre Documentos",
                            description=(
                                f"Conflicto grave en el proceso de esterilización declarado: '{doc1}' declara {', '.join(sorted(m1))}, "
                                f"mientras que '{doc2}' declara {', '.join(sorted(m2))}. "
                                "Una contradicción en el método de esterilización invalida las validaciones microbiológicas "
                                "(ISO 11135 para EO vs ISO 11137 para Radiación Gamma) y los ensayos de citotoxicidad y residuales."
                            ),
                            detected_text=f"{doc1}: {', '.join(sorted(m1))} vs {doc2}: {', '.join(sorted(m2))}",
                            expected_text="Método de esterilización único y congruente en todos los documentos",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ISO 11135 / ISO 11137",
                            remediation_advice="Confirmar con el fabricante el método validado y corregir los documentos discordantes.",
                        ))

        # 8. Descalce en Materia Prima / Composición Polimérica
        mat_by_doc: Dict[str, Set[str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.materials:
                mat_by_doc[name] = set(rep.parameters.materials)

        if len(mat_by_doc) >= 2:
            mat_items = list(mat_by_doc.items())
            for i in range(len(mat_items)):
                for j in range(i + 1, len(mat_items)):
                    doc1, mats1 = mat_items[i]
                    doc2, mats2 = mat_items[j]
                    incompatible_pairs = [
                        ({"Poliuretano"}, {"Polipropileno"}),
                        ({"Silicona"}, {"Poliuretano"}),
                    ]
                    for s1, s2 in incompatible_pairs:
                        if (s1.issubset(mats1) and s2.issubset(mats2)) or (s2.issubset(mats1) and s1.issubset(mats2)):
                            cross_findings.append(Finding(
                                id=f"CROSS_MATERIAL_CLASH_{i}_{j}",
                                document_name=f"{doc1} vs {doc2}",
                                page=None,
                                severity=Severity.FATAL,
                                category=Category.CROSS_DOCUMENT,
                                title="Inconsistencia Crítica en la Materia Prima / Composición del Dispositivo",
                                description=(
                                    f"Contradicción grave en la composición del polímero: '{doc1}' declara {', '.join(sorted(mats1))}, "
                                    f"mientras que '{doc2}' declara {', '.join(sorted(mats2))}. "
                                    "La naturaleza química de la materia prima determina la biocompatibilidad (ISO 10993) "
                                    "y la vida útil. Mezclar polímeros distintos causa el rechazo inmediato del expediente."
                                ),
                                detected_text=f"{doc1}: {', '.join(sorted(mats1))} vs {doc2}: {', '.join(sorted(mats2))}",
                                expected_text="Especificación unívoca del material en Ficha Técnica, DVR, CER y Rótulos",
                                digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                                remediation_advice="Verificar la resina o polímero grado médico exacto y estandarizar la especificación.",
                            ))
                            break

        # 9. Discrepancia en Calibres Gauge (G)
        g_by_doc: Dict[str, Tuple[Set[int], str]] = {}
        for name, rep in doc_reports.items():
            if rep.parameters.gauges:
                g_by_doc[name] = (set(rep.parameters.gauges), rep.parameters.gauges_raw)

        if len(g_by_doc) >= 2:
            g_items = list(g_by_doc.items())
            for i in range(len(g_items)):
                for j in range(i + 1, len(g_items)):
                    doc1, (s_g1, raw_g1) = g_items[i]
                    doc2, (s_g2, raw_g2) = g_items[j]
                    if s_g1 != s_g2 and not (s_g1.issubset(s_g2) or s_g2.issubset(s_g1)):
                        cross_findings.append(Finding(
                            id=f"CROSS_GAUGE_CLASH_{i}_{j}",
                            document_name=f"{doc1} vs {doc2}",
                            page=None,
                            severity=Severity.CRITICAL,
                            category=Category.CROSS_DOCUMENT,
                            title="Discrepancia en Calibre de Aguja/Trocar (Gauge) entre Documentos",
                            description=(
                                f"Discrepancia en calibre de agujas o accesorios: '{doc1}' declara {raw_g1}, "
                                f"mientras que '{doc2}' declara {raw_g2}."
                            ),
                            detected_text=f"{doc1}: {raw_g1} vs {doc2}: {raw_g2}",
                            expected_text="Calibre Gauge uniforme y justificado clínicamente",
                            digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                            remediation_advice="Uniformar el calibre de aguja/trocar en la ficha técnica y manual.",
                        ))

        # 10. Validación de Integridad Mínima del Lote Regulatorio
        if doc_reports:
            has_valid_medical_doc = any(
                not any("Documento No Pertinente" in f.title or "Sin Pertinencia Regulatoria" in f.title for f in r.findings)
                for r in doc_reports.values()
            )
            if not has_valid_medical_doc:
                cross_findings.append(Finding(
                    id="CROSS_BATCH_NO_REGULATORY_DOCS",
                    document_name="Lote Completo de Documentos",
                    page=None,
                    severity=Severity.FATAL,
                    category=Category.CROSS_DOCUMENT,
                    title="Lote Documental Inválido: Ningún Documento Pertenece a un Trámite DIGEMID",
                    description=(
                        "Ninguno de los archivos cargados en este lote corresponde a documentación técnica, "
                        "clínica, analítica ni legal de un dispositivo médico bajo el D.S. 016-2011-SA. "
                        "El lote está compuesto exclusivamente por documentos ajenos (hojas de vida, facturas, "
                        "cuentas de cobro o textos no médicos). La presentación de este lote ante DIGEMID / VUCE "
                        "resultará en rechazo de plano o inadmisibilidad."
                    ),
                    detected_text="0 documentos regulatorios válidos en el lote evaluado",
                    expected_text="Expediente técnico con Informe Técnico, Ficha Técnica, Rótulos, IFU y validaciones según D.S. 016-2011-SA",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 128°, 129° y 130° / TUPA DIGEMID",
                    remediation_advice="Cargar los archivos oficiales del expediente técnico del dispositivo médico a registrar.",
                ))

        return cross_findings
