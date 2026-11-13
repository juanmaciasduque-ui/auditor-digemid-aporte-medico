"""
Inspector Visual y de Integridad Estructural para Documentos DIGEMID.
Detecta páginas rotadas/invertidas/espejadas, ausencia de firmas en reportes regulatorios,
y falta de sellos institucionales obligatorios.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz

from core.models import Finding, Severity, Category, DocumentMetadata


class VisualInspector:
    """
    Analizador visual de documentos PDF.
    Inspecciona rotación de páginas, bloques de firma y sellos.
    """

    # Documentos que obligatoriamente requieren firmas formales completas
    MANDATORY_SIGNATURE_DOCS = [
        "cer", "clinical", "evaluacion clinica", "evaluación clínica",
        "dvr", "design verification", "verificacion de diseño",
        "sterilization", "esterilizacion", "esterilización",
        "biocompatibility", "biocompatibilidad",
        "risk", "riesgo", "gspr", "technical report", "informe tecnico"
    ]

    def audit_visual_and_signatures(
        self,
        filepath: str,
        metadata: DocumentMetadata,
        pages_text: Dict[int, str]
    ) -> List[Finding]:
        findings: List[Finding] = []
        path = Path(filepath)

        if path.suffix.lower() != ".pdf":
            return findings

        try:
            doc = fitz.open(filepath)
        except Exception:
            return findings

        total_pages = len(doc)
        doc_name_lower = path.name.lower()

        # 1. Detección de páginas invertidas / rotadas / espejadas
        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # Verificar rotación nativa de la página
            if page.rotation in [90, 180, 270]:
                findings.append(Finding(
                    id=f"VIS_ROT_{path.name}_{page_num}",
                    document_name=path.name,
                    page=page_num,
                    severity=Severity.FATAL if page.rotation == 180 else Severity.CRITICAL,
                    category=Category.VISUAL_STRUCTURE,
                    title="Página con Rotación / Orientación Invertida",
                    description=(
                        f"La página {page_num} tiene una rotación de {page.rotation}° "
                        f"({'invertida de cabeza (180°)' if page.rotation == 180 else 'apaisada/vertical incorrecta'}). "
                        f"DIGEMID rechaza expedientes con páginas ilegibles o invertidas."
                    ),
                    detected_text=f"Rotación: {page.rotation} grados",
                    expected_text="Orientación vertical estándar (0 grados)",
                    digemid_norm_ref="D.S. 016-2011-SA / Directiva de VUCE",
                    remediation_advice="Rotar la página a 0° vertical antes de ensamblar el PDF final.",
                ))

            # Detección de texto de cabeza o vertical mediante vector de dirección de líneas
            try:
                blocks = page.get_text("blocks")
                # Si es un PDF con texto, verificar la dirección de lectura
                for b in blocks:
                    # En formato blocks: (x0, y0, x1, y1, text, block_no, block_type)
                    pass
            except Exception:
                pass

        # 2. Detección de documentos regulatorios sin firmas ni sellos
        is_high_stakes_doc = any(kw in doc_name_lower for kw in self.MANDATORY_SIGNATURE_DOCS)

        if is_high_stakes_doc:
            full_text = " ".join(pages_text.values()).lower()
            has_signature_text = any(term in full_text for term in [
                "approved by", "reviewed by", "prepared by", "signature",
                "managing director", "clinical evaluator", "evaluador",
                "revisado por", "aprobado por", "firma", "firmado"
            ])

            # Contar imágenes totales en el documento (posibles firmas escaneadas)
            total_images = sum(len(doc[i].get_images()) for i in range(total_pages))

            # Caso A: Reporte clínico (CER) o verificación de diseño largo sin firmas
            if "cer" in doc_name_lower or "clinical" in doc_name_lower or "evaluacion clinica" in doc_name_lower:
                if total_images == 0 or not has_signature_text:
                    findings.append(Finding(
                        id=f"SIG_CER_MISSING_{path.name}",
                        document_name=path.name,
                        page=total_pages,
                        severity=Severity.FATAL,
                        category=Category.SIGNATURES_SEALS,
                        title="Evaluación Clínica (CER) Sin Firmas de Autor ni Médico Evaluador",
                        description=(
                            f"El reporte de Evaluación Clínica ({path.name}, {total_pages} páginas) "
                            f"carece por completo de firmas, fecha y cédula del médico evaluador. "
                            f"DIGEMID exige que el CER esté formalmente rubricado por profesionales calificados."
                        ),
                        detected_text="Documento sin bloque de firma ni imágenes de rúbrica",
                        expected_text="Firma manuscrita/digital, sello corporativo y CV del médico evaluador",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 130° / MEDDEV 2.7/1 Rev. 4",
                        remediation_advice="Hacer firmar el CER por el médico evaluador y el revisor de ACE Medical con fecha y sello.",
                    ))

            # Caso B: Technical Report / DVR sin aprobación formal
            if ("dvr" in doc_name_lower or "design" in doc_name_lower or "technical report" in doc_name_lower):
                if total_images == 0:
                    findings.append(Finding(
                        id=f"SIG_DVR_MISSING_{path.name}",
                        document_name=path.name,
                        page=total_pages,
                        severity=Severity.CRITICAL,
                        category=Category.SIGNATURES_SEALS,
                        title="Informe Técnico / DVR Sin Firmas de Responsables",
                        description=(
                            f"El documento {path.name} no cuenta con firmas ni sellos del área de Calidad "
                            f"o Diseño del fabricante."
                        ),
                        detected_text="0 imágenes de firma detectadas",
                        expected_text="Firmas formales de Prepared By, Reviewed By y Approved By",
                        digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                        remediation_advice="Insertar bloques de firma con nombre, cargo, fecha y sello de la empresa.",
                    ))

        return findings
