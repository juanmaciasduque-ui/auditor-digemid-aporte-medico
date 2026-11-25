"""
Suite de Pruebas Automatizadas para el Auditor Documental DIGEMID.
Valida unitaria e integralmente cada regla de los Catálogos A, B y C.
"""

import pytest
from core.models import Severity, Category, DocumentMetadata, DocumentReport
from core.rules.scientific_typos import ScientificTypoRules
from core.rules.structure import StructureIntegrityRules
from core.rules.cross_clash import CrossDocumentConsistencyEngine
from core.rules.digemid_legal import DigemidLegalRules
from core.visual_inspector import VisualInspector
from core.auditor import DigemidDocumentAuditor


# ==============================================================================
# PRUEBAS DEL CATÁLOGO A: ERRORES TIPOGRÁFICOS, CIENTÍFICOS Y TRADUCCIÓN
# ==============================================================================

def test_sal_positive_exponent_detected():
    rules = ScientificTypoRules()
    text = "The sterilization process achieved a Sterility Assurance level (SAL of 10^6) under EO gas."
    findings = rules.analyze_document("sterilization_test.pdf", {1: text})
    
    assert any(f.severity == Severity.FATAL and "SAL" in f.title for f in findings)
    assert any("10^6" in f.detected_text or "SAL" in f.detected_text for f in findings)


def test_sal_negative_exponent_not_flagged():
    rules = ScientificTypoRules()
    text = "The cycle achieved a validated Sterility Assurance Level (SAL 10^-6) compliant with ISO 11135."
    findings = rules.analyze_document("clean_sterilization.pdf", {1: text})
    
    sal_fatals = [f for f in findings if f.severity == Severity.FATAL and "SAL" in f.title]
    assert len(sal_fatals) == 0


def test_iso_typos_and_derogations():
    rules = ScientificTypoRules()
    text = (
        "Bioburden tests were performed following ISO 111737. "
        "Risk management was structured under ISO 14971:2012 and MDD 93/42/EEC. "
        "Labeling graphics comply with EN 980:2008 and quality meets ZSO 9001."
    )
    findings = rules.analyze_document("tech_report.pdf", {1: text})
    
    assert any("ISO 111737" in f.title for f in findings)
    assert any("ISO 14971:2012" in f.title for f in findings)
    assert any("MDD 93/42/EEC" in f.title for f in findings)
    assert any("EN 980:2008" in f.title for f in findings)
    assert any("ZSO 9001" in f.title for f in findings)


def test_absurd_translations():
    rules = ScientificTypoRules()
    text = (
        "Advertencia: el dispositivo no debe mantenerse mora. "
        "El doble coleta permite el anclaje seguro de la vegiga al riñón. "
        "Consulte el gato No. 405 para ordenar repuestos por el tubo."
    )
    findings = rules.analyze_document("ifu_espanol.pdf", {1: text})
    
    titles = [f.title for f in findings]
    assert any("no debe mantenerse mora" in t for t in titles)
    assert any("el doble coleta" in t for t in titles)
    assert any("de la vegiga" in t for t in titles)
    assert any("el gato no." in t for t in titles)


def test_lexical_english_accent_and_columbia():
    rules = ScientificTypoRules()
    text = (
        "Each sterile blíster pack is labeled for single use. "
        "Products were exported to Peru and Columbia."
    )
    findings = rules.analyze_document("export_details.pdf", {1: text})
    
    assert any("blíster" in f.title for f in findings)
    assert any("columbia" in f.title for f in findings)


# ==============================================================================
# PRUEBAS DEL CATÁLOGO B: ESTRUCTURA, ANEXOS, CAMPOS EN BLANCO Y SALTOS
# ==============================================================================

def test_blank_artwork_code_and_placeholder():
    rules = StructureIntegrityRules()
    text = (
        "IFU STENT URETERAL\n"
        "Artwork code with Rev. No.: \n"
        "Falta agregar breve descripción del proceso de esterilización."
    )
    findings = rules.analyze_document("ifu.pdf", {1: text}, tables_data=[])
    
    assert any("Artwork code with Rev. No." in f.title for f in findings)
    assert any("Borrador" in f.title or "Falta agregar" in f.description for f in findings)


def test_promised_annex_missing():
    rules = StructureIntegrityRules()
    text = (
        "Section 5.0 Clinical Team:\n"
        "Annexure 3 CV is attached for the principal clinical reviewer. "
        "Samples were analyzed at an approved NABL accredited laboratory for ISO 10993-7."
    )
    findings = rules.analyze_document("cer.pdf", {1: text}, tables_data=[], all_document_names={"cer.pdf"})
    
    assert any("Annexure 3" in f.title for f in findings)
    assert any("ISO 10993-7" in f.title or "NABL" in f.title for f in findings)


def test_section_numbering_jump():
    rules = StructureIntegrityRules()
    pages_text = {
        1: "1.0 Introduction\nSome text\n2.0 Scope\nSome text\n",
        2: "5.0 Clinical Data\nJumped from 2 to 5 directly."
    }
    findings = rules.analyze_document("report.pdf", pages_text, tables_data=[])
    assert any("Salto Errático en Numeración" in f.title for f in findings)


# ==============================================================================
# PRUEBAS DEL CATÁLOGO C: CONTRADICCIONES INTERNAS Y DESCALCES CRUZADOS
# ==============================================================================

def test_internal_half_cycles_contradiction():
    engine = CrossDocumentConsistencyEngine()
    pages_text = {
        2: "Section 1.0: In this study 2 half cycles were carried out.",
        3: "Section 4.0: Three half cycles were performed in the EO chamber."
    }
    findings = engine.check_internal_contradictions("sterilization_val.pdf", pages_text)
    assert any("Contradicción Interna de Semiciclos" in f.title for f in findings)


def test_clinical_copy_paste_contaminations():
    engine = CrossDocumentConsistencyEngine()
    pages_text = {
        1: "Similar device design: Bottle/grenade type for urological drain.",
        2: "Indicated for Gastro-enterological Endoscopic procedures.",
        3: "Kit Contain: Stent, Umbilical cord clamp, guidewire.",
        4: "Foley balloon catheter 8Fr-28Fr with balloon 3-50 ml."
    }
    findings = engine.check_internal_contradictions("cer_contaminated.pdf", pages_text)
    
    titles = [f.title for f in findings]
    assert any("Bottle/grenade" in t for t in titles)
    assert any("Gastroenterológicos" in t for t in titles)
    assert any("Umbilical cord clamp" in t for t in titles)
    assert any("Foley" in t for t in titles)


def test_cross_batch_fr_and_length_clash():
    engine = CrossDocumentConsistencyEngine()
    
    # Doc 1: CLV declara 2-12 Fr y 6-32 cm
    p1 = engine.extract_document_parameters("CLV.pdf", {1: "Catéter Ureteral Doble J 2-12 Fr, longitud 6-32 cm."})
    rep1 = DocumentReport(metadata=DocumentMetadata("CLV.pdf", "", "PDF", 1), parameters=p1)

    # Doc 2: DVR declara 3-8 Fr y 70-90 cm (infiltración)
    p2 = engine.extract_document_parameters("DVR.pdf", {1: "Diameter 3-8 Fr & length 70-90 cm."})
    rep2 = DocumentReport(metadata=DocumentMetadata("DVR.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"CLV.pdf": rep1, "DVR.pdf": rep2})
    
    assert any("Descalce Dimensional en Calibres Fr" in f.title for f in cross_findings)
    assert any("Infiltración de Producto Distinto: Longitud de 70–90 cm" in f.title for f in cross_findings)


def test_cross_batch_shelf_life_clash():
    engine = CrossDocumentConsistencyEngine()
    
    # Doc 1: DVR dice 3 años
    p1 = engine.extract_document_parameters("DVR.pdf", {1: "Shelf life: 3 years (36 months)."})
    rep1 = DocumentReport(metadata=DocumentMetadata("DVR.pdf", "", "PDF", 1), parameters=p1)

    # Doc 2: Lotes Accuprec dicen 5 años
    p2 = engine.extract_document_parameters("Lab.pdf", {1: "Tested shelf life: 5 years (60 months)."})
    rep2 = DocumentReport(metadata=DocumentMetadata("Lab.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"DVR.pdf": rep1, "Lab.pdf": rep2})
    assert any("Descalce Severo de Vida Útil" in f.title for f in cross_findings)


def test_cross_batch_set_components_contradiction():
    engine = CrossDocumentConsistencyEngine()
    
    # Doc 1: Carta fabricante declara SET con accesorios
    p1 = engine.extract_document_parameters("Carta.pdf", {1: "Ureteral Stent Set with pusher, guidewire and clamp."})
    rep1 = DocumentReport(metadata=DocumentMetadata("Carta.pdf", "", "PDF", 1), parameters=p1)

    # Doc 2: CER declara que no contiene componentes
    p2 = engine.extract_document_parameters("CER.pdf", {1: "The device doesn't contain any components."})
    rep2 = DocumentReport(metadata=DocumentMetadata("CER.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"Carta.pdf": rep1, "CER.pdf": rep2})
    assert any("CER Niega Componentes" in f.title for f in cross_findings)


# ==============================================================================
# PRUEBAS DE REGLAS LEGALES DIGEMID
# ==============================================================================

def test_digemid_colombia_sas_detected():
    rules = DigemidLegalRules()
    text = (
        "Nosotros, ACE MEDICAL DEVICES PVT. LTD. confirmamos a APORTE MEDICO S.A.S. "
        "Manizales - Colombia como TITULAR DE LOS REGISTROS SANITARIOS en Colombia."
    )
    findings = rules.analyze_document("carta_colombia.pdf", {1: text})
    assert any("Documento Legal Autorizado para Colombia" in f.title for f in findings)


def test_digemid_historical_importer_teleandes():
    rules = DigemidLegalRules()
    text = "Importado y distribuido por Consorcio Teleandes S.A.C. RUC 20537638631."
    findings = rules.analyze_document("rotulo.pdf", {1: text})
    assert any("Consorcio Teleandes" in f.title for f in findings)


# ==============================================================================
# PRUEBAS UNIVERSALES: MALLAS, ESTERILIZACIÓN, MATERIA PRIMA Y FOLIACIÓN
# ==============================================================================

def test_page_count_discrepancy_missing_pages():
    rules = StructureIntegrityRules()
    # Archivo que solo tiene 3 páginas pero en el pie de página declara "Página 1 de 5"
    pages = {
        1: "Manual de Uso. Página 1 de 5",
        2: "Descripción técnica. Página 2 de 5",
        3: "Advertencias clínicas. Página 3 de 5",
    }
    findings = rules.analyze_document("Manual_Cinta.pdf", pages, tables_data=[], total_pages=3)
    assert any("Foliación Incompleta: Páginas Faltantes" in f.title for f in findings)
    assert any(f.severity.value == "FATAL" for f in findings)


def test_cross_batch_mesh_dimension_clash():
    engine = CrossDocumentConsistencyEngine()
    # Doc 1: Ficha técnica declara 1.1 x 50 cm
    p1 = engine.extract_document_parameters("Ficha.pdf", {1: "Dimensiones de la cinta de polipropileno: 1.1 x 50 cm"})
    rep1 = DocumentReport(metadata=DocumentMetadata("Ficha.pdf", "", "PDF", 1), parameters=p1)

    # Doc 2: Manual declara 1.5 x 45 cm
    p2 = engine.extract_document_parameters("Manual.pdf", {1: "Dimensiones del implante: 1.5 x 45 cm"})
    rep2 = DocumentReport(metadata=DocumentMetadata("Manual.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"Ficha.pdf": rep1, "Manual.pdf": rep2})
    assert any("Descalce en Dimensiones de Malla/Cinta Quirúrgica" in f.title for f in cross_findings)


def test_cross_batch_sterilization_method_clash():
    engine = CrossDocumentConsistencyEngine()
    # Doc 1: Validación declara Óxido de Etileno
    p1 = engine.extract_document_parameters("Val_EO.pdf", {1: "Esterilización validada mediante óxido de etileno (EO)."})
    rep1 = DocumentReport(metadata=DocumentMetadata("Val_EO.pdf", "", "PDF", 1), parameters=p1)

    # Doc 2: Rótulo declara Radiación Gamma
    p2 = engine.extract_document_parameters("Rotulo.pdf", {1: "Sterilized using Gamma radiation."})
    rep2 = DocumentReport(metadata=DocumentMetadata("Rotulo.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"Val_EO.pdf": rep1, "Rotulo.pdf": rep2})
    assert any("Contradicción Crítica en Método de Esterilización" in f.title for f in cross_findings)


def test_cross_batch_material_clash():
    engine = CrossDocumentConsistencyEngine()
    # Doc 1: Ficha declara Poliuretano
    p1 = engine.extract_document_parameters("Ficha.pdf", {1: "Materia prima principal: Poliuretano grado médico."})
    rep1 = DocumentReport(metadata=DocumentMetadata("Ficha.pdf", "", "PDF", 1), parameters=p1)

    # Doc 2: CER declara Polipropileno
    p2 = engine.extract_document_parameters("CER.pdf", {1: "Device body manufactured from polypropylene."})
    rep2 = DocumentReport(metadata=DocumentMetadata("CER.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"Ficha.pdf": rep1, "CER.pdf": rep2})
    assert any("Inconsistencia Crítica en la Materia Prima" in f.title for f in cross_findings)


# ==============================================================================
# PRUEBAS DE PERTINENCIA DOCUMENTAL (HOJA DE VIDA, FACTURAS, TEXTOS AJENOS)
# ==============================================================================

def test_cv_resume_detected_as_fatal():
    rules = DigemidLegalRules()
    cv_text = """
    CURRICULUM VITAE
    Carlos Alberto Gómez - Ingeniero Biomédico
    Perfil Profesional: Especialista con 8 años de experiencia laboral en mantenimiento hospitalario.
    Formación Académica: Universidad de los Andes.
    Referencias Laborales: Disponibles a solicitud.
    """
    findings = rules.analyze_document("Hoja_de_Vida_Carlos.pdf", {1: cv_text})
    assert any("Infiltración de Hoja de Vida / Currículum Vitae" in f.title for f in findings)
    assert any(f.severity.value == "FATAL" for f in findings)


def test_invoice_bill_detected_as_fatal():
    rules = DigemidLegalRules()
    bill_text = """
    CUENTA DE COBRO N° 102
    Aporte Médico Perú S.A.C.
    DEBE A: Juan Fernando Pérez
    LA SUMA DE: $ 4.500.000 COP
    POR CONCEPTO DE: Honorarios profesionales por asesoría contable mes de marzo.
    Consignar a la Cuenta de Ahorros Bancolombia N° 987654321.
    """
    findings = rules.analyze_document("Cuenta_de_Cobro_Marzo.pdf", {1: bill_text})
    assert any("Factura / Cuenta de Cobro Comercial Infiltrada" in f.title for f in findings)
    assert any(f.severity.value == "FATAL" for f in findings)


def test_irrelevant_generic_text_detected_as_fatal():
    rules = DigemidLegalRules()
    random_text = """
    El informe meteorológico indica que las lluvias continuarán en la región norte durante el fin de semana.
    Las autoridades recomiendan tomar precauciones viales y mantener limpios los canales de drenaje.
    """
    findings = rules.analyze_document("Informe_Clima.pdf", {1: random_text})
    assert any("Documento Sin Pertinencia Regulatoria" in f.title for f in findings)
    assert any(f.severity.value == "FATAL" for f in findings)


def test_batch_all_irrelevant_documents_verdict():
    from core.models import BatchAuditResult
    rules = DigemidLegalRules()
    engine = CrossDocumentConsistencyEngine()

    doc1_text = "Hoja de Vida. Experiencia laboral en marketing y ventas. Formación académica."
    doc2_text = "Cuenta de cobro por concepto de diseño gráfico. Valor a pagar $500."

    f1 = rules.analyze_document("CV.pdf", {1: doc1_text})
    p1 = engine.extract_document_parameters("CV.pdf", {1: doc1_text})
    rep1 = DocumentReport(metadata=DocumentMetadata("CV.pdf", "", "PDF", 1), parameters=p1, findings=f1)

    f2 = rules.analyze_document("Cobro.pdf", {1: doc2_text})
    p2 = engine.extract_document_parameters("Cobro.pdf", {1: doc2_text})
    rep2 = DocumentReport(metadata=DocumentMetadata("Cobro.pdf", "", "PDF", 1), parameters=p2, findings=f2)

    batch_findings = engine.check_batch_consistency({"CV.pdf": rep1, "Cobro.pdf": rep2})
    batch_result = BatchAuditResult(documents={"CV.pdf": rep1, "Cobro.pdf": rep2}, cross_findings=batch_findings)

    assert batch_result.total_fatal >= 2
    assert batch_result.rejection_probability_pct == 100.0
    assert "NO APTO: EXPEDIENTE INVÁLIDO" in batch_result.verdict


# ==============================================================================
# PRUEBAS DE CATÁLOGO COMPLETO APORTE MÉDICO / UROTIENDA Y CORRECCIÓN DE BUGS
# ==============================================================================

def test_ifi_word_boundary_no_false_positive_in_certificado():
    rules = ScientificTypoRules()
    text = "Certificado de Libre Venta. Especificaciones técnicas e identificación de calidad verificada."
    findings = rules.analyze_document("clv.pdf", {1: text})
    assert not any("ifi" in f.detected_text.lower() for f in findings)


def test_mesh_mm_to_cm_normalization_no_false_positive():
    engine = CrossDocumentConsistencyEngine()
    p1 = engine.extract_document_parameters("Ficha.pdf", {1: "Cinta vaginal de polipropileno 1.1 x 50 cm."})
    rep1 = DocumentReport(metadata=DocumentMetadata("Ficha.pdf", "", "PDF", 1), parameters=p1)
    p2 = engine.extract_document_parameters("Manual.pdf", {1: "Cinta vaginal de polipropileno 11 x 500 mm."})
    rep2 = DocumentReport(metadata=DocumentMetadata("Manual.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency({"Ficha.pdf": rep1, "Manual.pdf": rep2}, product_family="VAGINAL_SLINGS_MESHES")
    assert not any("Descalce en Dimensiones de Malla" in f.title for f in cross_findings)


def test_nitinol_basket_length_70_120_not_flagged_as_double_j_infiltration():
    engine = CrossDocumentConsistencyEngine()
    p1 = engine.extract_document_parameters("Ficha_Canastilla.pdf", {1: "Canastilla extractora de Nitinol 3 hilos, calibre 2.2 Fr, longitud 70-120 cm."})
    rep1 = DocumentReport(metadata=DocumentMetadata("Ficha_Canastilla.pdf", "", "PDF", 1), parameters=p1)
    p2 = engine.extract_document_parameters("IFU_Canastilla.pdf", {1: "Canastilla de Nitinol 2.2 Fr, longitud 70-120 cm para ureteroscopia."})
    rep2 = DocumentReport(metadata=DocumentMetadata("IFU_Canastilla.pdf", "", "PDF", 1), parameters=p2)

    cross_findings = engine.check_batch_consistency(
        {"Ficha_Canastilla.pdf": rep1, "IFU_Canastilla.pdf": rep2},
        product_family="NITINOL_BASKETS_ACCESS"
    )
    assert not any("Ureteral Catheter" in f.title for f in cross_findings)


def test_uroclamp_reusable_without_cleaning_and_reusable_clash():
    rules = DigemidLegalRules()
    ifu_text = (
        "MANUAL DE USUARIO UROCLAMP. Pinza anatómica externa reutilizable para control de incontinencia masculina. "
        "Fabricado en silicona médica libre de látex. Uso externo diario por el paciente. Mantener en lugar fresco y seco."
    )
    findings = rules.analyze_document("IFU_Uroclamp.pdf", {1: ifu_text}, product_family="NON_INVASIVE_INCONTINENCE")
    assert any("ISO 17664" in f.title for f in findings)

    engine = CrossDocumentConsistencyEngine()
    p1 = engine.extract_document_parameters("IFU_Uroclamp.pdf", {1: "Uroclamp dispositivo reutilizable para incontinencia."})
    rep1 = DocumentReport(metadata=DocumentMetadata("IFU_Uroclamp.pdf", "", "PDF", 1), parameters=p1)
    p2 = engine.extract_document_parameters("Rotulo_Uroclamp.pdf", {1: "Uroclamp pinza externa. Un solo uso / Do not reuse."})
    rep2 = DocumentReport(metadata=DocumentMetadata("Rotulo_Uroclamp.pdf", "", "PDF", 1), parameters=p2)
    cross_findings = engine.check_batch_consistency({"IFU_Uroclamp.pdf": rep1, "Rotulo_Uroclamp.pdf": rep2})
    assert any("Un Solo Uso" in f.title and "Reutilizable" in f.title for f in cross_findings)


def test_active_device_km526_missing_contraindications_and_iec60601():
    rules = DigemidLegalRules()
    manual_text = (
        "MANUAL DE USUARIO REHABILITADOR DE PISO PÉLVICO KM 526. "
        "Equipo de electroestimulación neuromuscular y biofeedback para fortalecimiento del suelo pélvico. "
        "Incluye sonda vaginal de silicona médica, programas de frecuencia de 10 a 100 Hz y pantalla LCD."
    )
    findings = rules.analyze_document("Manual_KM526.pdf", {1: manual_text}, product_family="PELVIC_REHAB_ACTIVE")
    assert any("Contraindicaciones Clínicas Obligatorias" in f.title for f in findings)

    tech_text = (
        "INFORME TÉCNICO REHABILITADOR KM 526. Equipo terapéutico de electroestimulación pélvica. "
        "Carcasa de ABS grado médico, corriente de salida 0 a 80 mA, ancho de pulso 250 us."
    )
    tech_findings = rules.analyze_document("Informe_Tecnico_KM526.pdf", {1: tech_text}, product_family="PELVIC_REHAB_ACTIVE")
    assert any("IEC 60601" in f.title for f in tech_findings)


def test_empty_doc_and_corrupt_file_handled_as_fatal(tmp_path):
    rules = DigemidLegalRules()
    empty_findings = rules.analyze_document("Blanco.pdf", {1: "   "})
    assert any("Ilegible o en Blanco" in f.title and f.severity == Severity.FATAL for f in empty_findings)

    bad_pdf = tmp_path / "corrupto.pdf"
    bad_pdf.write_bytes(b"not a real pdf content")
    auditor = DigemidDocumentAuditor(enable_ocr=False)
    res = auditor.audit_batch([str(bad_pdf)])
    assert "corrupto.pdf" in res.documents
    assert res.total_fatal >= 1
    assert any("Error Crítico de Lectura" in f.title for f in res.all_findings)


def test_invima_in_peru_technical_doc_flagged_but_clv_allowed():
    rules = DigemidLegalRules()
    tech = "Informe Técnico del dispositivo médico Uroclamp conforme al Decreto 4725 de 2005 y Registro Sanitario INVIMA."
    f_tech = rules.analyze_document("Informe_Tecnico.pdf", {1: tech})
    assert any("INVIMA" in f.title for f in f_tech)

    clv = "Certificado de Libre Venta emitido por INVIMA Colombia. Exportador Aporte Medico S.A.S. hacia APORTE MÉDICO PERÚ S.A.C. RUC 20610321268."
    f_clv = rules.analyze_document("CLV_Colombia.pdf", {1: clv})
    assert not any("INVIMA" in f.title for f in f_clv)


def test_spanish_labeling_art137_required():
    rules = DigemidLegalRules()
    eng_ifu = (
        "Instructions for use of the sterile medical device. Warning: Do not reuse. "
        "Caution: Federal law restricts this device to sale by a physician. "
        "Manufactured for single use only. Keep away from sunlight and moisture."
    )
    findings = rules.analyze_document("IFU_Product.pdf", {1: eng_ifu})
    assert any("Art. 137°" in f.title for f in findings)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
