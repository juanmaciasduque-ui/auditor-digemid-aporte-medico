"""
Detector de Errores Tipográficos, Ortográficos, Notación Científica y Traducción Absurda.
Cubre el Catálogo A:
- Exponentes y notación microbiológica (SAL 10^6 vs 10^-6, indicador biológico 106).
- Normas ISO mal digitadas (ISO 111737) y derogadas (ISO 14971:2012, MDD 93/42/EEC, EN 980:2008).
- Errores de OCR y lectura corrupta (ZSO 9001, 'ifi', 'taction').
- Traducción automática absurda o no médica ('no debe mantenerse mora', 'El doble coleta', 'el gato No.', 'de la vegiga').
- Mezcla de idiomas e inconsistencias léxicas ('blíster' en inglés, 'Silicon stents', 'Columbia').
"""

import re
from typing import List, Dict
from core.models import Finding, Severity, Category
from config import STANDARDS_COMPLIANCE_MAP, ABSURD_TRANSLATIONS


class ScientificTypoRules:
    """Reglas de detección de errores científicos, tipográficos y de traducción."""

    def analyze_document(self, document_name: str, pages_text: Dict[int, str]) -> List[Finding]:
        findings: List[Finding] = []

        for page_num, text in pages_text.items():
            if not text:
                continue

            findings.extend(self._check_sal_and_microbiology(document_name, page_num, text))
            findings.extend(self._check_iso_and_standards(document_name, page_num, text))
            findings.extend(self._check_absurd_translations(document_name, page_num, text))
            findings.extend(self._check_lexical_and_language_mix(document_name, page_num, text))

        return findings

    def _check_sal_and_microbiology(self, doc_name: str, page_num: int, text: str) -> List[Finding]:
        findings = []

        # 1. SAL of 10^6 o SAL 106 (exponente positivo = un millón de probabilidad de NO esterilidad)
        # Buscar: SAL de 10^6, SAL of 10^6, SAL of 106, SAL 106
        # Distinguir de 10^-6 o 10-6
        sal_pos_pattern = re.compile(
            r'\b(?:SAL|Sterility\s+Assurance\s+Level|Nivel\s+de\s+Garant[ií]a\s+de\s+Esterilidad)\s*(?:of|de|:)?\s*(?:10\^?\+?6\b|106\b)(?!\s*[\-–]\s*6)',
            re.IGNORECASE
        )
        for match in sal_pos_pattern.finditer(text):
            matched_str = match.group(0)
            # Asegurarse de que no sea 10^-6 o 10-6
            snippet_after = text[match.end():match.end() + 15]
            if not re.match(r'^\s*[\-–]\s*6', snippet_after):
                findings.append(Finding(
                    id=f"TYPO_SAL_POS_{doc_name}_{page_num}_{match.start()}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity.FATAL,
                    category=Category.TYPOGRAPHY_SCIENTIFIC,
                    title="Error Científico Fatal en Nivel de Esterilidad (SAL con Exponente Positivo)",
                    description=(
                        f"Se detectó la expresión '{matched_str}' en la página {page_num}. "
                        "Un SAL de 10^6 o 106 representa 1 millón de unidades contaminadas (exponente positivo), "
                        "en lugar de 10^-6 (una probabilidad en un millón de no esterilidad). "
                        "DIGEMID deniega de oficio validaciones de esterilización con esta formulación errónea."
                    ),
                    detected_text=matched_str,
                    expected_text="SAL 10^-6 (10 a la menos 6 / 1 x 10^-6)",
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130° / ISO 11135",
                    remediation_advice="Corregir inmediatamente el superíndice a 10^-6 en el informe de validación de EO.",
                ))

        # 2. Indicador biológico: 106 sin superíndice
        bi_pattern = re.compile(
            r'\b(?:Bacillus|Bacilus|atrophaeus|subtilis|biological\s+indicator|indicador\s+biol[oó]gico)\b[^\n\.\,]{0,40}\b106\b(?!\s*[\-–]\s*6)',
            re.IGNORECASE
        )
        for match in bi_pattern.finditer(text):
            matched_str = match.group(0)
            findings.append(Finding(
                id=f"TYPO_BI_EXP_{doc_name}_{page_num}_{match.start()}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.CRITICAL,
                category=Category.TYPOGRAPHY_SCIENTIFIC,
                title="Población de Indicador Biológico Mal Digitada (106 sin Superíndice)",
                description=(
                    f"Se digitó '{matched_str}' sin superíndice. La población requerida para el indicador "
                    "biológico de Bacillus atrophaeus es 10^6 esporas (un millón), no el número plano 106."
                ),
                detected_text=matched_str,
                expected_text="10^6 esporas (con superíndice)",
                digemid_norm_ref="ISO 11135:2014 / ISO 11138-1",
                remediation_advice="Formatear como 10^6 en el texto y tablas del protocolo.",
            ))

        # 3. Bacilus con una sola 'l'
        bacillus_typo = re.compile(r'\bBacilus\s+atrophaeus\b', re.IGNORECASE)
        for match in bacillus_typo.finditer(text):
            findings.append(Finding(
                id=f"TYPO_BACILLUS_{doc_name}_{page_num}_{match.start()}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.MINOR,
                category=Category.TYPOGRAPHY_SCIENTIFIC,
                title="Nombre Científico Mal Escrito (Bacilus con una sola 'l')",
                description=f"Se escribió '{match.group(0)}' en lugar de 'Bacillus atrophaeus'.",
                detected_text=match.group(0),
                expected_text="Bacillus atrophaeus",
                digemid_norm_ref="Farmacopea / ISO 11138-2",
                remediation_advice="Corregir a 'Bacillus atrophaeus' con doble 'l'.",
            ))

        return findings

    def _check_iso_and_standards(self, doc_name: str, page_num: int, text: str) -> List[Finding]:
        findings = []

        # 1. ISO 111737 (Typo común por ISO 11737-1)
        if re.search(r'\bISO\s*111737\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"STD_ISO_111737_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.CRITICAL,
                category=Category.TYPOGRAPHY_SCIENTIFIC,
                title="Cita de Norma ISO Inexistente (Error Tipográfico: ISO 111737)",
                description=(
                    "Se cita la norma 'ISO 111737', la cual no existe. El estándar internacional aplicable "
                    "para bioburden y control microbiológico de esterilización es ISO 11737-1 e ISO 11737-2."
                ),
                detected_text="ISO 111737",
                expected_text="ISO 11737-1 (Bioburden) / ISO 11737-2 (Esterilidad)",
                digemid_norm_ref="D.S. 016-2011-SA Art. 130°",
                remediation_advice="Corregir a ISO 11737-1 en todo el informe de esterilización.",
            ))

        # 2. ZSO 9001 (Error de OCR)
        if re.search(r'\bZSO\s*9001\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"STD_ZSO_9001_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.MINOR,
                category=Category.TYPOGRAPHY_SCIENTIFIC,
                title="Error de Lectura OCR / Digitalización Corrupta (ZSO 9001)",
                description="Se detectó 'ZSO 9001:2015' generado por reconocimiento óptico corrupto de 'ISO 9001'.",
                detected_text="ZSO 9001",
                expected_text="ISO 9001:2015",
                digemid_norm_ref="D.S. 016-2011-SA",
                remediation_advice="Revisar el PDF para que el texto vectorial sea nítido y diga ISO 9001:2015.",
            ))

        # 3. Normas Derogadas
        # ISO 14971:2012
        if re.search(r'\bISO\s*14971\s*:\s*2012\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"STD_DEROG_14971_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.CRITICAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Uso de Norma Derogada en Gestión de Riesgos (ISO 14971:2012)",
                description=(
                    "El archivo cita ISO 14971:2012. Dicha versión fue derogada y sustituida por "
                    "ISO 14971:2019 (+ Enmienda A11:2021). Presentar expedientes basados en normas "
                    "desactualizadas motiva observaciones de DIGEMID bajo el D.S. 003-2020-SA."
                ),
                detected_text="ISO 14971:2012",
                expected_text="ISO 14971:2019 / A11:2021",
                digemid_norm_ref="D.S. 003-2020-SA / Principio Esencial 1 y 2",
                remediation_advice="Actualizar la matriz de gestión del riesgo a ISO 14971:2019.",
            ))

        # MDD 93/42/EEC
        if re.search(r'\b(?:MDD\s*93/42/EEC|93/42/CEE|Council\s+Directive\s+93/42)\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"STD_DEROG_MDD_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.CRITICAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Invocación de Directiva Europea Derogada (MDD 93/42/EEC)",
                description=(
                    "Se cita la Directiva MDD 93/42/EEC, la cual quedó derogada y reemplazada por el "
                    "Reglamento de Dispositivos Médicos de la Unión Europea (UE) 2017/745 (EU MDR)."
                ),
                detected_text="MDD 93/42/EEC",
                expected_text="Reglamento (UE) 2017/745 (EU MDR)",
                digemid_norm_ref="D.S. 016-2011-SA / D.S. 003-2020-SA",
                remediation_advice="Reemplazar referencias a MDD 93/42/EEC por EU MDR 2017/745.",
            ))

        # EN 980:2008
        if re.search(r'\bEN\s*980(?:\s*:\s*2008)?\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"STD_DEROG_EN980_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.CRITICAL,
                category=Category.DIGEMID_NORMATIVE,
                title="Cita de Norma Derogada de Símbolos de Rotulado (EN 980:2008)",
                description=(
                    "La norma EN 980 fue derogada y sustituida globalmente por ISO 15223-1 "
                    "(Símbolos a utilizar en las etiquetas de los productos sanitarios)."
                ),
                detected_text="EN 980:2008",
                expected_text="ISO 15223-1:2021",
                digemid_norm_ref="D.S. 016-2011-SA Art. 137°",
                remediation_advice="Actualizar la referencia en rótulos y manual IFU a ISO 15223-1:2021.",
            ))

        return findings

    def _check_absurd_translations(self, doc_name: str, page_num: int, text: str) -> List[Finding]:
        findings = []
        text_lower = text.lower()

        for pattern_str, info in ABSURD_TRANSLATIONS.items():
            if pattern_str in text_lower:
                # Obtener fragmento contextual
                idx = text_lower.find(pattern_str)
                snippet = text[max(0, idx - 25):min(len(text), idx + len(pattern_str) + 25)].strip()
                snippet = snippet.replace("\n", " ")

                findings.append(Finding(
                    id=f"TRAD_ABSURD_{doc_name}_{page_num}_{idx}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity(info["gravedad"]),
                    category=Category.TRANSLATION_LEXICAL,
                    title=f"Traducción Inadecuada / No Médica: '{pattern_str}'",
                    description=(
                        f"En la página {page_num} se detectó: \"...{snippet}...\". "
                        f"Proviene de una traducción automática literal del inglés ('{info['origen']}'). "
                        f"Esto genera observaciones severas de evaluadores DIGEMID por falta de rigor técnico."
                    ),
                    detected_text=pattern_str,
                    expected_text=info["correccion"],
                    digemid_norm_ref="D.S. 016-2011-SA Art. 130° y 137°",
                    remediation_advice=f"Reemplazar por '{info['correccion']}' en la traducción oficial colegiada.",
                ))

        return findings

    def _check_lexical_and_language_mix(self, doc_name: str, page_num: int, text: str) -> List[Finding]:
        findings = []

        # 1. Tildes en párrafos en inglés (ej: "blíster" en inglés, "identificactión", "Instruciones")
        # Detectar "blíster" dentro de oraciones con palabras en inglés como "pack", "sterile", "device", "seal"
        blister_pattern = re.compile(r'\bbl[ií]ster\b[^\.\n]{0,50}\b(?:pack|sterile|pouch|box|sealed)\b', re.IGNORECASE)
        for match in blister_pattern.finditer(text):
            if "blíster" in match.group(0).lower():
                findings.append(Finding(
                    id=f"LEX_BLISTER_{doc_name}_{page_num}_{match.start()}",
                    document_name=doc_name,
                    page=page_num,
                    severity=Severity.MINOR,
                    category=Category.TRANSLATION_LEXICAL,
                    title="Inconsistencia Léxica: Tilde en Idioma Inglés ('blíster')",
                    description="Se insertó la palabra en español con tilde 'blíster' dentro de una oración en inglés.",
                    detected_text=match.group(0),
                    expected_text="blister (sin tilde en inglés)",
                    digemid_norm_ref="Criterio de coherencia documental",
                    remediation_advice="Eliminar la tilde en los textos redactados en idioma inglés.",
                ))

        # 2. "identificactión" en inglés
        if re.search(r'\bidentificacti[oó]n\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"LEX_IDENTIFICACTION_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.MINOR,
                category=Category.TRANSLATION_LEXICAL,
                title="Error Tipográfico / Mezcla Lingüística ('identificactión')",
                description="Se detectó 'identificactión' (combinación errónea de 'identification' con acento español).",
                detected_text="identificactión",
                expected_text="identification (inglés) o identificación (español)",
                digemid_norm_ref="Calidad formal del expediente",
                remediation_advice="Corregir a 'identification' en los encabezados y carátulas.",
            ))

        # 3. "Instruciones" (falta de 'c' en español)
        if re.search(r'\bInstruciones\b', text, re.IGNORECASE):
            findings.append(Finding(
                id=f"LEX_INSTRUCIONES_{doc_name}_{page_num}",
                document_name=doc_name,
                page=page_num,
                severity=Severity.MINOR,
                category=Category.TRANSLATION_LEXICAL,
                title="Falta Ortográfica en Portada o Rótulo ('Instruciones')",
                description="Se escribió 'Instruciones' con una sola 'c' en lugar de 'Instrucciones'.",
                detected_text="Instruciones",
                expected_text="Instrucciones de uso",
                digemid_norm_ref="D.S. 016-2011-SA Art. 137°",
                remediation_advice="Corregir a 'Instrucciones' con doble 'c'.",
            ))

        return findings
