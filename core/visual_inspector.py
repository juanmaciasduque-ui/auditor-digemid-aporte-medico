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
            with fitz.open(filepath) as doc:
                total_pages = len(doc)
                doc_name_lower = path.name.lower()

                # 1. Detección de páginas invertidas / rotadas / en blanco
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

                    # Detección de páginas en blanco accidentales
                    extracted_p_text = (pages_text.get(page_num) or "").strip()
                    if len(extracted_p_text) == 0 and len(page.get_images()) == 0:
                        findings.append(Finding(
                            id=f"VIS_BLANK_{path.name}_{page_num}",
                            document_name=path.name,
                            page=page_num,
                            severity=Severity.MINOR,
                            category=Category.VISUAL_STRUCTURE,
                            title="Página Totalmente en Blanco Detectada",
                            description=(
                                f"La página {page_num} de '{path.name}' está completamente vacía (sin texto ni imágenes). "
                                "Suele ocurrir por escaneo a doble cara sin contenido."
                            ),
                            detected_text=f"Página {page_num}: 0 caracteres y 0 imágenes",
                            expected_text="Eliminar páginas en blanco sobrantes antes de cargar a VUCE",
                            digemid_norm_ref="Directiva técnica de digitalización VUCE / DIGEMID",
                            remediation_advice=f"Suprimir la página {page_num} en blanco del PDF para mantener foliación limpia.",
                        ))

                    # Detección de texto orientado al revés (-1, 0) cuando el PDF tiene rotación=0°
                    if page.rotation == 0:
                        try:
                            text_dict = page.get_text("dict")
                            inverted_lines = 0
                            total_lines = 0
                            for block in text_dict.get("blocks", []):
                                for line in block.get("lines", []):
                                    total_lines += 1
                                    d = line.get("dir", (1.0, 0.0))
                                    if d[0] < -0.5:  # Texto de cabeza (180° en vector)
                                        inverted_lines += 1
                            if total_lines >= 3 and inverted_lines / total_lines > 0.5:
                                findings.append(Finding(
                                    id=f"VIS_VEC_INV_{path.name}_{page_num}",
                                    document_name=path.name,
                                    page=page_num,
                                    severity=Severity.FATAL,
                                    category=Category.VISUAL_STRUCTURE,
                                    title="Página Invertida de Cabeza Detectada por Vector de Texto",
                                    description=(
                                        f"En la página {page_num}, la mayoría de líneas de texto ({inverted_lines}/{total_lines}) "
                                        "tienen orientación invertida (180°)."
                                    ),
                                    detected_text="Orientación vectorial invertida (-180°)",
                                    expected_text="Orientación de lectura normal (0°)",
                                    digemid_norm_ref="D.S. 016-2011-SA / Directiva de VUCE",
                                    remediation_advice="Rotar físicamente la página 180° en el editor de PDF.",
                                ))
                        except Exception:
                            pass

                # 2. Detección de documentos regulatorios sin firmas ni sellos
                is_high_stakes_doc = any(kw in doc_name_lower for kw in self.MANDATORY_SIGNATURE_DOCS)

                if is_high_stakes_doc:
                    full_text = " ".join(pages_text.values()).lower()
                    has_signature_text = any(term in full_text for term in [
                        "approved by", "reviewed by", "prepared by", "signature",
                        "managing director", "clinical evaluator", "evaluador",
                        "revisado por", "aprobado por", "firma", "firmado",
                        "director tecnico", "director técnico", "autorizado por"
                    ])

                    total_images = sum(len(doc[i].get_images()) for i in range(total_pages))

                    # Caso A: Reporte clínico (CER) sin firmas
                    if "cer" in doc_name_lower or "clinical" in doc_name_lower or "evaluacion clinica" in doc_name_lower or "evaluación clínica" in doc_name_lower:
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
                                    f"carece de firmas, fecha y cédula del médico evaluador. "
                                    f"DIGEMID exige que el CER esté formalmente rubricado por profesionales calificados."
                                ),
                                detected_text="Documento sin bloque de firma ni imágenes de rúbrica",
                                expected_text="Firma manuscrita/digital, sello corporativo y CV del médico evaluador",
                                digemid_norm_ref="D.S. 016-2011-SA Art. 130° / MEDDEV 2.7/1 Rev. 4",
                                remediation_advice="Hacer firmar el CER por el médico evaluador y el revisor técnico con fecha y sello.",
                            ))

                    # Caso B: Technical Report / DVR / COA / Declaración de Conformidad / Estabilidad sin aprobación formal
                    if any(k in doc_name_lower for k in ["dvr", "design", "technical report", "informe tecnico", "informe técnico", "coa", "analysis", "analisis", "análisis", "stability", "estabilidad", "risk", "riesgo"]):
                        if total_images == 0 and not has_signature_text:
                            findings.append(Finding(
                                id=f"SIG_DVR_MISSING_{path.name}",
                                document_name=path.name,
                                page=total_pages,
                                severity=Severity.CRITICAL,
                                category=Category.SIGNATURES_SEALS,
                                title="Documento Técnico / Calidad Sin Firmas de Responsables",
                                description=(
                                    f"El documento {path.name} no cuenta con bloques de firma ni sellos del área de Calidad "
                                    f"o Diseño del fabricante."
                                ),
                                detected_text="0 firmas ni bloques de aprobación detectados",
                                expected_text="Firmas formales de Prepared By, Reviewed By y Approved By con fecha y sello",
                                digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                                remediation_advice="Insertar bloques de firma con nombre, cargo, fecha y sello de la empresa fabricante.",
                            ))
        except Exception:
            return findings
