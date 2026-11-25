"""
Motor de Ingesta y Normalización Documental (PDF, DOCX e Imágenes).
Extrae texto nativo, ejecuta OCR automático con RapidOCR en páginas escaneadas,
recupera metadatos, tablas y analiza la orientación física de las páginas.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import fitz  # PyMuPDF
from docx import Document as DocxDocument

from core.models import DocumentMetadata

# Inicialización diferida de OCR para optimizar arranque
_OCR_ENGINE = None

def _get_cache_dir() -> Path:
    """Usa el directorio temporal del sistema (seguro en nube/solo-lectura) para caché OCR."""
    base = Path(tempfile.gettempdir()) / "digemid_ocr_cache"
    try:
        base.mkdir(parents=True, exist_ok=True)
        return base
    except Exception:
        fallback = Path(__file__).resolve().parent.parent / ".ocr_cache"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

CACHE_DIR = _get_cache_dir()

def get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _OCR_ENGINE = RapidOCR()
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo inicializar RapidOCR: {e}")
            _OCR_ENGINE = None
    return _OCR_ENGINE


class DocumentIngestionEngine:
    """
    Motor centralizado de ingesta documental con caché en disco para OCR.
    Procesa PDFs digitales, escaneados híbridos y archivos DOCX.
    """

    def __init__(
        self,
        enable_ocr: bool = True,
        ocr_min_chars: int = 80,
        max_ocr_pages: int = 25,
        full_ocr: bool = False
    ):
        self.enable_ocr = enable_ocr
        self.ocr_min_chars = ocr_min_chars
        self.max_ocr_pages = max_ocr_pages
        self.full_ocr = full_ocr

    def _get_cache_path(self, file_path: Path, page_num: int) -> Path:
        stat = file_path.stat() if file_path.exists() else None
        mtime = int(stat.st_mtime) if stat else 0
        size = stat.st_size if stat else 0
        safe_name = re.sub(r'[^\w\-_\.]', '_', file_path.stem)[:60]
        return CACHE_DIR / f"{safe_name}_p{page_num}_{size}_{mtime}.txt"

    def process_file(self, filepath: str) -> Tuple[DocumentMetadata, Dict[int, str], List[Dict[str, Any]]]:
        """
        Procesa un archivo y retorna:
        (metadata, texto_por_pagina, tablas_extraidas)
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"El archivo '{path.name}' no existe o fue eliminado.")

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._process_pdf(path)
        elif suffix == ".docx":
            return self._process_docx(path)
        elif suffix == ".doc":
            raise ValueError(
                f"El archivo '{path.name}' usa el formato binario antiguo .doc (Word 97-2003). "
                "La plataforma VUCE / DIGEMID exige formato PDF o DOCX moderno. Convierta el archivo a PDF o .docx."
            )
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]:
            return self._process_image(path)
        else:
            raise ValueError(f"Formato no soportado: {suffix}. Use PDF, DOCX o imágenes (PNG/JPG).")

    def _process_pdf(self, path: Path) -> Tuple[DocumentMetadata, Dict[int, str], List[Dict[str, Any]]]:
        pages_text: Dict[int, str] = {}
        tables_data: List[Dict[str, Any]] = []
        is_scanned_overall = False
        has_signatures = False
        has_seals = False
        file_size = path.stat().st_size if path.exists() else 0

        if file_size == 0:
            raise ValueError(f"El archivo '{path.name}' está vacío (0 bytes) o corrupto.")

        with fitz.open(str(path)) as doc:
            if doc.needs_pass:
                raise ValueError(
                    f"El PDF '{path.name}' está protegido con contraseña o cifrado. "
                    "DIGEMID / VUCE rechaza archivos bloqueados; guarde una copia desbloqueada sin contraseña."
                )

            total_pages = len(doc)
            if total_pages == 0:
                raise ValueError(f"El archivo '{path.name}' no contiene páginas válidas.")

            # Extraer metadatos nativos
            meta = doc.metadata or {}
            author = meta.get("author", "") or ""
            creator = meta.get("creator", "") or ""
            producer = meta.get("producer", "") or ""
            creation_date = meta.get("creationDate", "") or ""
            mod_date = meta.get("modDate", "") or ""

            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]

                # 1. Extracción de texto nativo
                text = page.get_text("text").strip()
                image_list = page.get_images()

                # 2. Detección de página escaneada / sin texto suficiente
                if len(text) < self.ocr_min_chars and len(image_list) > 0 and self.enable_ocr:
                    is_scanned_overall = True
                    # Optimización: en documentos escaneados extensos (>25 pp), priorizar inicio, secciones clave y firmas
                    should_ocr = (
                        self.full_ocr
                        or total_pages <= self.max_ocr_pages
                        or page_idx < 15
                        or page_idx >= (total_pages - 10)
                    )
                    if should_ocr:
                        ocr_text = self._ocr_page(page, source_path=path)
                        if ocr_text:
                            text = f"{text}\n{ocr_text}".strip()

                pages_text[page_num] = text

                # 3. Detección preliminar de firmas / sellos en imágenes
                if len(image_list) > 0:
                    for img_info in image_list:
                        width, height = img_info[2], img_info[3]
                        if 50 <= width <= 600 and 30 <= height <= 400:
                            has_signatures = True

                # 4. Extracción de tablas estructuradas si están disponibles
                try:
                    tables = page.find_tables()
                    if tables and len(tables.tables) > 0:
                        for t in tables.tables:
                            df_rows = t.extract()
                            if df_rows:
                                tables_data.append({
                                    "page": page_num,
                                    "rows": df_rows,
                                    "header": df_rows[0] if len(df_rows) > 0 else [],
                                })
                except Exception:
                    pass

        doc_meta = DocumentMetadata(
            filename=path.name,
            filepath=str(path.resolve()),
            file_type="PDF",
            total_pages=total_pages,
            author=author,
            creator=creator,
            producer=producer,
            creation_date=creation_date,
            modification_date=mod_date,
            is_scanned=is_scanned_overall,
            has_signatures=has_signatures,
            has_seals=has_seals,
            file_size_bytes=file_size,
        )

        return doc_meta, pages_text, tables_data

    def _ocr_page(self, page: fitz.Page, source_path: Optional[Path] = None) -> str:
        """Aplica OCR sobre una página renderizada con almacenamiento en caché."""
        page_num = page.number + 1

        # 1. Verificar si existe en caché de disco
        if source_path:
            cache_file = self._get_cache_path(source_path, page_num)
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass

        ocr_engine = get_ocr_engine()
        if not ocr_engine:
            return ""

        try:
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            result, _ = ocr_engine(img_bytes)
            if result:
                lines = [item[1] for item in result]
                extracted = "\n".join(lines)
                # Guardar en caché
                if source_path:
                    cache_file = self._get_cache_path(source_path, page_num)
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            f.write(extracted)
                    except Exception:
                        pass
                return extracted
        except Exception as e:
            print(f"Error OCR en página {page.number}: {e}")
        return ""

    def _process_docx(self, path: Path) -> Tuple[DocumentMetadata, Dict[int, str], List[Dict[str, Any]]]:
        doc = DocxDocument(str(path))
        pages_text: Dict[int, str] = {}
        tables_data: List[Dict[str, Any]] = []

        all_text_lines = []
        for p in doc.paragraphs:
            if p.text.strip():
                all_text_lines.append(p.text.strip())

        # En DOCX no hay paginación fija exacta, agrupamos en bloques lógicos o página 1
        pages_text[1] = "\n".join(all_text_lines)

        # Tablas en DOCX
        for t_idx, table in enumerate(doc.tables):
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                table_rows.append(row_cells)
            if table_rows:
                tables_data.append({
                    "page": 1,
                    "table_index": t_idx,
                    "rows": table_rows,
                    "header": table_rows[0] if len(table_rows) > 0 else [],
                })

        # Metadatos del documento Word
        author = ""
        creation_date = ""
        mod_date = ""
        try:
            core_props = doc.core_properties
            author = core_props.author or ""
            creation_date = str(core_props.created) if core_props.created else ""
            mod_date = str(core_props.modified) if core_props.modified else ""
        except Exception:
            pass

        file_size = path.stat().st_size if path.exists() else 0

        doc_meta = DocumentMetadata(
            filename=path.name,
            filepath=str(path.resolve()),
            file_type="DOCX",
            total_pages=1,
            author=author,
            creator="Microsoft Word",
            producer="",
            creation_date=creation_date,
            modification_date=mod_date,
            is_scanned=False,
            has_signatures=False,
            has_seals=False,
            file_size_bytes=file_size,
        )

        return doc_meta, pages_text, tables_data

    def _process_image(self, path: Path) -> Tuple[DocumentMetadata, Dict[int, str], List[Dict[str, Any]]]:
        ocr_engine = get_ocr_engine()
        text = ""
        if ocr_engine:
            try:
                with open(path, "rb") as f:
                    img_bytes = f.read()
                result, _ = ocr_engine(img_bytes)
                if result:
                    text = "\n".join(item[1] for item in result)
            except Exception as e:
                print(f"Error procesando imagen {path.name}: {e}")

        file_size = path.stat().st_size if path.exists() else 0

        doc_meta = DocumentMetadata(
            filename=path.name,
            filepath=str(path.resolve()),
            file_type="IMAGE",
            total_pages=1,
            author="",
            creator="",
            producer="",
            creation_date="",
            modification_date="",
            is_scanned=True,
            has_signatures=False,
            has_seals=False,
            file_size_bytes=file_size,
        )

        return doc_meta, {1: text}, []
