"""
Orquestador Central de Auditoría Documental para DIGEMID.
Coordina la ingesta, inspección visual, aplicación de reglas por catálogo
y el motor de concordancia cruzada entre documentos.
"""

from pathlib import Path
from typing import List, Dict, Set, Optional, Callable

from core.models import (
    BatchAuditResult,
    DocumentReport,
    Finding,
    ExtractedParameters
)
from core.ingestion import DocumentIngestionEngine
from core.visual_inspector import VisualInspector
from core.rules.scientific_typos import ScientificTypoRules
from core.rules.structure import StructureIntegrityRules
from core.rules.cross_clash import CrossDocumentConsistencyEngine
from core.rules.digemid_legal import DigemidLegalRules


class DigemidDocumentAuditor:
    """
    Sistema integral de auditoría regulatoria para dispositivos médicos (Clase III / DIGEMID Perú).
    """

    def __init__(self, enable_ocr: bool = True, full_ocr: bool = False):
        self.ingestion_engine = DocumentIngestionEngine(enable_ocr=enable_ocr, full_ocr=full_ocr)
        self.visual_inspector = VisualInspector()
        self.scientific_rules = ScientificTypoRules()
        self.structure_rules = StructureIntegrityRules()
        self.cross_clash_engine = CrossDocumentConsistencyEngine()
        self.legal_rules = DigemidLegalRules()

    def audit_batch(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> BatchAuditResult:
        """
        Audita un lote completo de documentos técnicos y legales.
        """
        result = BatchAuditResult()
        total_files = len(file_paths)
        all_doc_names: Set[str] = {Path(p).name for p in file_paths}

        # Paso 1: Ingesta y auditoría individual de cada documento
        for idx, fpath in enumerate(file_paths):
            path_obj = Path(fpath)
            doc_name = path_obj.name

            if progress_callback:
                progress_callback(idx + 1, total_files, f"Procesando {doc_name}...")

            try:
                # 1.1 Ingesta documental (PyMuPDF + RapidOCR en escaneados + DOCX)
                meta, pages_text, tables = self.ingestion_engine.process_file(str(path_obj))

                # 1.2 Extracción de parámetros clave
                params = self.cross_clash_engine.extract_document_parameters(doc_name, pages_text)

                # 1.3 Ejecución de reglas por documento
                doc_findings: List[Finding] = []

                # A. Inspección visual y firmas
                doc_findings.extend(
                    self.visual_inspector.audit_visual_and_signatures(str(path_obj), meta, pages_text)
                )

                # B. Reglas científicas, tipográficas y traducción (Catálogo A)
                doc_findings.extend(
                    self.scientific_rules.analyze_document(doc_name, pages_text)
                )

                # C. Reglas estructurales, celdas vacías y anexos (Catálogo B)
                doc_findings.extend(
                    self.structure_rules.analyze_document(doc_name, pages_text, tables, all_doc_names)
                )

                # D. Contradicciones internas en el propio documento (Catálogo C.1)
                doc_findings.extend(
                    self.cross_clash_engine.check_internal_contradictions(doc_name, pages_text)
                )

                # E. Reglas legales específicas DIGEMID
                doc_findings.extend(
                    self.legal_rules.analyze_document(doc_name, pages_text)
                )

                # Crear reporte del documento
                doc_report = DocumentReport(
                    metadata=meta,
                    parameters=params,
                    findings=doc_findings,
                    extracted_text_by_page=pages_text,
                )
                result.documents[doc_name] = doc_report

            except Exception as e:
                print(f"[ERROR] Error al auditar {doc_name}: {e}")

        # Paso 2: Auditoría de concordancia cruzada entre todos los documentos (Catálogo C.2 - C.6)
        if progress_callback:
            progress_callback(total_files, total_files, "Ejecutando matriz de consistencia cruzada...")

        result.cross_findings = self.cross_clash_engine.check_batch_consistency(result.documents)

        return result
