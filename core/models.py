"""
Modelos de datos para el software Auditor Documental DIGEMID.
Define severidades, categorías, hallazgos y reportes estructurados.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class Severity(str, Enum):
    FATAL = "FATAL"         # 🔴 Causa directa de rechazo o nulidad (Art. 130 D.S. 016, inconsistencias mayores)
    CRITICAL = "CRITICAL"   # 🟡 Observación obligatoria segura de DIGEMID (Notificación oficial de subsanación)
    MINOR = "MINOR"         # 🔵 Error tipográfico, traducción deficiente o detalle menor de formato


class Category(str, Enum):
    TYPOGRAPHY_SCIENTIFIC = "Tipografía y Notación Científica"
    TRANSLATION_LEXICAL = "Traducción y Léxico Médico"
    VISUAL_STRUCTURE = "Estructura, Páginas e Integridad"
    SIGNATURES_SEALS = "Firmas, Sellos y Autorizaciones"
    CROSS_DOCUMENT = "Inconsistencias Cruzadas (Cross-Clash)"
    DIGEMID_NORMATIVE = "Contravenciones Normativas DIGEMID"


@dataclass
class Finding:
    id: str
    document_name: str
    page: Optional[int]
    severity: Severity
    category: Category
    title: str
    description: str
    detected_text: str
    expected_text: str
    digemid_norm_ref: str
    remediation_advice: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_name": self.document_name,
            "page": self.page,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "detected_text": self.detected_text,
            "expected_text": self.expected_text,
            "digemid_norm_ref": self.digemid_norm_ref,
            "remediation_advice": self.remediation_advice,
        }


@dataclass
class DocumentMetadata:
    filename: str
    filepath: str
    file_type: str
    total_pages: int
    author: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    modification_date: str = ""
    is_scanned: bool = False
    has_signatures: bool = False
    has_seals: bool = False
    file_size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "file_type": self.file_type,
            "total_pages": self.total_pages,
            "author": self.author,
            "creator": self.creator,
            "producer": self.producer,
            "creation_date": self.creation_date,
            "modification_date": self.modification_date,
            "is_scanned": self.is_scanned,
            "has_signatures": self.has_signatures,
            "has_seals": self.has_seals,
            "file_size_bytes": self.file_size_bytes,
        }


@dataclass
class ExtractedParameters:
    diameters_fr: List[float] = field(default_factory=list)
    diameters_fr_raw: str = ""
    lengths_cm: List[float] = field(default_factory=list)
    lengths_cm_raw: str = ""
    shelf_life_months: Optional[float] = None
    shelf_life_raw: str = ""
    indwelling_time_days: Optional[float] = None
    indwelling_time_raw: str = ""
    device_types: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    foreign_contaminations: List[str] = field(default_factory=list)
    iso_standards_cited: List[str] = field(default_factory=list)
    derogated_standards: List[str] = field(default_factory=list)
    half_cycles_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diameters_fr": self.diameters_fr,
            "diameters_fr_raw": self.diameters_fr_raw,
            "lengths_cm": self.lengths_cm,
            "lengths_cm_raw": self.lengths_cm_raw,
            "shelf_life_months": self.shelf_life_months,
            "shelf_life_raw": self.shelf_life_raw,
            "indwelling_time_days": self.indwelling_time_days,
            "indwelling_time_raw": self.indwelling_time_raw,
            "device_types": self.device_types,
            "components": self.components,
            "materials": self.materials,
            "foreign_contaminations": self.foreign_contaminations,
            "iso_standards_cited": self.iso_standards_cited,
            "derogated_standards": self.derogated_standards,
            "half_cycles_count": self.half_cycles_count,
        }


@dataclass
class DocumentReport:
    metadata: DocumentMetadata
    parameters: ExtractedParameters
    findings: List[Finding] = field(default_factory=list)
    extracted_text_by_page: Dict[int, str] = field(default_factory=dict)

    @property
    def fatal_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.FATAL)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def minor_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MINOR)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "parameters": self.parameters.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "counts": {
                "fatal": self.fatal_count,
                "critical": self.critical_count,
                "minor": self.minor_count,
                "total": len(self.findings),
            },
        }


@dataclass
class BatchAuditResult:
    documents: Dict[str, DocumentReport] = field(default_factory=dict)
    cross_findings: List[Finding] = field(default_factory=list)

    @property
    def all_findings(self) -> List[Finding]:
        findings = list(self.cross_findings)
        for doc in self.documents.values():
            findings.extend(doc.findings)
        return findings

    @property
    def total_fatal(self) -> int:
        return sum(1 for f in self.all_findings if f.severity == Severity.FATAL)

    @property
    def total_critical(self) -> int:
        return sum(1 for f in self.all_findings if f.severity == Severity.CRITICAL)

    @property
    def total_minor(self) -> int:
        return sum(1 for f in self.all_findings if f.severity == Severity.MINOR)

    @property
    def rejection_probability_pct(self) -> float:
        """
        Calcula la probabilidad objetiva de denegatoria ante DIGEMID:
        - Si hay al menos 1 hallazgo FATAL, la probabilidad es >= 95%.
        - Si hay hallazgos CRÍTICOS (observaciones de subsanación), cada uno añade peso.
        """
        if self.total_fatal > 0:
            prob = 90.0 + min(10.0, self.total_fatal * 2.0)
            return round(min(100.0, prob), 1)
        if self.total_critical > 0:
            prob = 50.0 + min(40.0, self.total_critical * 5.0)
            return round(min(90.0, prob), 1)
        if self.total_minor > 0:
            return round(min(40.0, self.total_minor * 2.5), 1)
        return 0.0

    @property
    def verdict(self) -> str:
        if self.total_fatal > 0:
            return "NO APTO PARA PRESENTACIÓN (DENEGATORIA INMINENTE)"
        if self.total_critical > 0:
            return "NO APTO - ALTO RIESGO DE OBSERVACIÓN Y RECHAZO"
        if self.total_minor > 0:
            return "APTO CON OBSERVACIONES MENORES DE FORMA"
        return "APTO PARA PRESENTACIÓN EN VUCE / DIGEMID"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_documents": len(self.documents),
                "total_findings": len(self.all_findings),
                "total_fatal": self.total_fatal,
                "total_critical": self.total_critical,
                "total_minor": self.total_minor,
                "rejection_probability_pct": self.rejection_probability_pct,
                "verdict": self.verdict,
            },
            "documents": {name: doc.to_dict() for name, doc in self.documents.items()},
            "cross_findings": [f.to_dict() for f in self.cross_findings],
        }
