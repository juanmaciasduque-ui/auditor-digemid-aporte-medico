"""
Generador del Paquete Instalador Autónomo para Distribución.
Crea un archivo ZIP limpio listo para enviar por WhatsApp o correo.
"""

import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
DESKTOP_DIR = Path.home() / "OneDrive" / "Escritorio"
if not DESKTOP_DIR.exists():
    DESKTOP_DIR = Path.home() / "Desktop"

OUTPUT_ZIP = DESKTOP_DIR / "Auditor_DIGEMID_Instalador_AporteMedico.zip"

INCLUDE_EXTENSIONS = {".py", ".bat", ".vbs", ".ico", ".png", ".txt", ".toml", ".md"}
EXCLUDE_DIRS = {".git", ".ocr_cache", "reports", ".pytest_cache", "__pycache__", "tests", ".venv"}


def build_distribution_zip():
    print(f"Empaquetando instalador en: {OUTPUT_ZIP}")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                filepath = Path(root) / file
                rel_path = filepath.relative_to(ROOT_DIR)
                
                # Excluir archivos innecesarios o pesados
                if any(part in EXCLUDE_DIRS for part in rel_path.parts):
                    continue
                if file.endswith(".pyc") or file.endswith(".zip"):
                    continue

                zf.write(filepath, arcname=str(rel_path))

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Paquete creado con éxito: {OUTPUT_ZIP} ({size_mb:.2f} MB)")
    return OUTPUT_ZIP, size_mb


if __name__ == "__main__":
    build_distribution_zip()
