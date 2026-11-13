"""
Aplicación Web Interactiva - Auditor Documental DIGEMID (Aporte Médico Perú).
Diseño sin barreras de acceso: Solo el logo corporativo y la zona de carga de expedientes.
Incluye Mini-Agente Regulatorio DIGEMID para búsqueda normativa en vivo y generación de soluciones oficiales.
"""

import os
import sys
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

from core.auditor import DigemidDocumentAuditor
from core.report_generator import ReportGenerator
from core.models import Severity, Category, BatchAuditResult
from core.agents.digemid_agent import DigemidAgent
from config import BASE_CASE_INFO, DEFAULT_TEST_DATA_DIR, REPORTS_DIR, DIGEMID_LEGAL_FRAMEWORK

# Configuración de página
st.set_page_config(
    page_title="Auditor DIGEMID · Aporte Médico Perú",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed", # Iniciar limpio sin distracciones
)

# Estilos CSS de alta gama corporativa
st.markdown("""
<style>
    /* Estilos globales y paleta institucional */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    .header-box {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px 24px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
        border-left: 6px solid #1e3a8a;
    }
    .header-text h1 {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e3a8a;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-text p {
        font-size: 0.95rem;
        color: #64748b;
        margin: 4px 0 0 0;
    }
    .upload-card {
        background: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        margin-bottom: 24px;
        transition: all 0.3s ease;
    }
    .upload-card:hover {
        border-color: #1e3a8a;
        background: #f1f5f9;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-fatal { background-color: #fee2e2; color: #991b1b; }
    .badge-critical { background-color: #fef3c7; color: #92400e; }
    .badge-minor { background-color: #e0f2fe; color: #0369a1; }
    .diff-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 0.88rem;
    }
    .agent-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# Estado de sesión
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "agent" not in st.session_state:
    st.session_state.agent = DigemidAgent()

agent: DigemidAgent = st.session_state.agent

# ENCABEZADO CON LOGO DE APORTE MÉDICO PERÚ
logo_path = Path(__file__).parent / "assets" / "logo_aporte_medico.png"

col_logo, col_title = st.columns([1, 4])
with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.image("https://img.icons8.com/color/96/medical-history.png", width=90)

with col_title:
    st.markdown("""
    <div style="padding-top: 5px;">
        <h1 style="color: #1e3a8a; margin: 0; font-size: 2rem; font-weight: 800;">AUDITOR FORENSE DOCUMENTAL DIGEMID</h1>
        <p style="color: #475569; margin: 4px 0 0 0; font-size: 1rem;">
            Aporte Médico Perú S.A.C. · Control Automatizado Pre-Radicación VUCE (Clase III / D.S. 016-2011-SA / D.S. 003-2020-SA)
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ZONA DE CARGA DE DOCUMENTOS / CARPETA (SIN LOGIN NI BARRERAS)
c_upload, c_quick = st.columns([3, 1])

with c_upload:
    uploaded_files = st.file_uploader(
        "📂 Arrastre aquí los documentos (PDFs, Word DOCX) o seleccione los archivos de su expediente:",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Puede arrastrar todos los archivos de la carpeta del expediente técnico simultáneamente."
    )

with c_quick:
    st.markdown("**¿Probar expediente real?**")
    test_suite_btn = st.button("⚡ Cargar Banco de Pruebas Real\n(Catéteres ACE Medical)", use_container_width=True)

archivos_para_auditar = []

if test_suite_btn:
    if DEFAULT_TEST_DATA_DIR.exists():
        archivos_para_auditar = list(DEFAULT_TEST_DATA_DIR.glob("*.pdf")) + list(DEFAULT_TEST_DATA_DIR.glob("*.docx"))
        # Excluir duplicados de paquetes de 70 páginas para auditoría instantánea
        archivos_para_auditar = [f for f in archivos_para_auditar if "EXPEDIENTE" not in f.name.upper() and "DOCUMENTOS TÉCNICOS" not in f.name.upper()]
        st.toast(f"Cargados {len(archivos_para_auditar)} documentos del expediente técnico real.", icon="📂")
    else:
        st.error(f"No se encontró el directorio base {DEFAULT_TEST_DATA_DIR}")

elif uploaded_files:
    temp_dir = Path(tempfile.gettempdir()) / "aporte_digemid_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for uf in uploaded_files:
        dest = temp_dir / uf.name
        with open(dest, "wb") as f:
            f.write(uf.getbuffer())
        archivos_para_auditar.append(dest)

# BOTÓN DE ACCIÓN PRINCIPAL
if archivos_para_auditar:
    col_act1, col_act2 = st.columns([2, 1])
    with col_act1:
        st.info(f"📋 **{len(archivos_para_auditar)} documentos listos para auditar:** {', '.join([f.name for f in archivos_para_auditar[:4]])}{'...' if len(archivos_para_auditar) > 4 else ''}")
    with col_act2:
        ejecutar = st.button("🚀 INICIAR AUDITORÍA DOCUMENTAL", type="primary", use_container_width=True)

    if ejecutar:
        with st.spinner("Analizando expedientes con OCR y matriz de concordancia cruzada..."):
            auditor = DigemidDocumentAuditor(enable_ocr=True)
            pbar = st.progress(0.0)
            status_lbl = st.empty()

            def pcb(curr, tot, msg):
                pbar.progress(curr / max(1, tot))
                status_lbl.caption(f"[{curr}/{tot}] {msg}")

            res = auditor.audit_batch([str(p) for p in archivos_para_auditar], progress_callback=pcb)
            pbar.empty()
            status_lbl.empty()
            st.session_state.audit_result = res
            st.toast("Auditoría pericial completada.", icon="✅")

# RESULTADOS DE LA AUDITORÍA
res: BatchAuditResult = st.session_state.audit_result

if res is not None:
    st.markdown("---")

    # DICTAMEN PERICIAL Y RIESGO
    prob = res.rejection_probability_pct
    verdict = res.verdict
    if res.total_fatal > 0:
        st.error(f"⛔ **DICTAMEN PERICIAL: {verdict}**  \n**Probabilidad de Denegatoria de Oficio ante DIGEMID: {prob}%** — Se han detectado **{res.total_fatal} fallas fatales directas** que causarán pérdida de tasa TUPA.")
    elif res.total_critical > 0:
        st.warning(f"⚠️ **DICTAMEN PERICIAL: {verdict}**  \n**Probabilidad de Notificación con Observación: {prob}%** (Subsanación técnica requerida).")
    else:
        st.success(f"✅ **DICTAMEN PERICIAL: {verdict}**  \n**Apto para radicación en VUCE.**")

    # MÉTRICAS KPI
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Documentos Auditados", len(res.documents))
    m2.metric("🔴 Fallas Fatales", res.total_fatal, help="Inconsistencias que motivan denegatoria directa")
    m3.metric("🟡 Observaciones Críticas", res.total_critical, help="Observaciones seguras en Notificación oficial")
    m4.metric("🔵 Errores Menores", res.total_minor, help="Traducción, tipografía y formato")

    # PESTAÑAS DE ANÁLISIS
    tab_fatal, tab_critical, tab_minor, tab_matrix, tab_agent, tab_docs = st.tabs([
        f"🔴 Fallas Fatales ({res.total_fatal})",
        f"🟡 Observaciones Críticas ({res.total_critical})",
        f"🔵 Errores Menores ({res.total_minor})",
        "📊 Matriz Dimensional Cruzada",
        "🤖 Mini-Agente y Buscador DIGEMID",
        "📄 Detalle por Documento"
    ])

    def render_finding_box(f):
        badge_cls = "badge-fatal" if f.severity == Severity.FATAL else ("badge-critical" if f.severity == Severity.CRITICAL else "badge-minor")
        with st.expander(f"[{f.severity.value}] {f.title} — {f.document_name}", expanded=(f.severity == Severity.FATAL)):
            st.markdown(f"<span class='badge {badge_cls}'>{f.severity.value}</span> | **Categoría:** {f.category.value} | **Página:** {f.page or 'General'}", unsafe_allow_html=True)
            st.write(f.description)
            st.markdown(f"""
            <div class="diff-container">
                <div style="color: #dc2626;"><strong>❌ Detectado:</strong> <code>{f.detected_text}</code></div>
                <div style="color: #16a34a; margin-top: 4px;"><strong>✅ Corrección Requerida:</strong> <code>{f.expected_text}</code></div>
            </div>
            """, unsafe_allow_html=True)
            st.info(f"**⚖️ Exigencia Legal DIGEMID:** {f.digemid_norm_ref}")
            st.success(f"**🛠️ Instrucción de Subsanación:** {f.remediation_advice}")

    with tab_fatal:
        fatals = [f for f in res.all_findings if f.severity == Severity.FATAL]
        if not fatals:
            st.success("No se encontraron fallas fatales.")
        else:
            for f in fatals:
                render_finding_box(f)

    with tab_critical:
        criticals = [f for f in res.all_findings if f.severity == Severity.CRITICAL]
        if not criticals:
            st.success("No se encontraron observaciones críticas.")
        else:
            for f in criticals:
                render_finding_box(f)

    with tab_minor:
        minors = [f for f in res.all_findings if f.severity == Severity.MINOR]
        if not minors:
            st.success("No se encontraron observaciones menores.")
        else:
            for f in minors:
                render_finding_box(f)

    with tab_matrix:
        st.markdown("### Matriz Dimensional y Clínica Comparativa entre Documentos")
        matrix_rows = []
        for name, rep in res.documents.items():
            p = rep.parameters
            matrix_rows.append({
                "Documento": name,
                "Calibres Fr": p.diameters_fr_raw or "No declarado",
                "Longitudes cm": p.lengths_cm_raw or "No declarado",
                "Vida Útil": p.shelf_life_raw or "No declarado",
                "Permanencia Clínica": p.indwelling_time_raw or "No declarado",
                "Componentes": ", ".join(p.components) if p.components else "Estándar",
                "Contaminaciones": ", ".join(p.foreign_contaminations) if p.foreign_contaminations else "Limpio",
            })
        st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True)

        if res.cross_findings:
            st.markdown("#### Inconsistencias Cruzadas Detectadas:")
            for cf in res.cross_findings:
                render_finding_box(cf)

    # PESTAÑA DEL MINI-AGENTE REGULATORIO DIGEMID
    with tab_agent:
        st.markdown("### 🤖 Mini-Agente Regulatorio y Buscador en Vivo DIGEMID")
        st.write("Consulte la normativa actualizada de DIGEMID, precedentes de dispositivos aprobados en Perú y descargue modelos de subsanación técnica.")

        col_q1, col_q2 = st.columns([3, 1])
        with col_q1:
            query = st.text_input("🔍 Buscar norma, requisito o precedente en DIGEMID:", value="flujograma breve descripción")
        with col_q2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            buscar_btn = st.button("Buscar en DIGEMID", use_container_width=True)

        if query:
            results = agent.search_regulations(query)
            if results:
                st.markdown(f"#### Resultados Normativos Vigentes ({len(results)} normas encontradas):")
                for r in results:
                    with st.expander(f"📜 {r['norma_codigo']} — {r['norma_nombre']} ({r['vigencia']})", expanded=True):
                        for art, desc in r['articulos'].items():
                            st.markdown(f"**{art}:**")
                            st.write(desc)
            else:
                st.info("No se encontraron coincidencias exactas. Intente con términos como 'Art. 130', 'flujograma', 'esterilización' o 'ftalatos'.")

        st.markdown("---")
        st.markdown("#### 📝 Generador de Soluciones y Redactados Oficiales para VUCE")
        st.write("Seleccione el problema a resolver para generar el redactado técnico formal para ACE Medical Devices o para el escrito de subsanación ante DIGEMID:")

        sol_tipo = st.selectbox(
            "Seleccione la solución a generar:",
            [
                ("CARTA_FABRICANTE_ART126", "Carta de Autorización y Desglose de Modelos del Fabricante (Art. 126°)"),
                ("FLUJOGRAMA_ART130", "Descripción Narrativa Resumida de Etapas del Flujograma (Art. 130° num. 5)"),
                ("ESTERILIZACION_SAL", "Justificación Científica de Esterilidad EO y SAL 10^-6 (ISO 11135)"),
                ("INFILTRACION_LONGITUDES", "Sustento Técnico para Separar Ureteral Catheter (70-90 cm) del Stent (6-32 cm)"),
            ],
            format_func=lambda x: x[1]
        )

        sol_data = agent.generate_solution_template(sol_tipo[0])
        st.markdown(f"##### {sol_data['titulo']}")
        st.text_area("Texto Oficial para Presentar a DIGEMID / VUCE (Español):", sol_data["texto_espanol"], height=160)

        if "texto_ingles_ace" in sol_data:
            st.text_area("Instrucción Oficial en Inglés para Solicitar a ACE Medical Devices (India):", sol_data["texto_ingles_ace"], height=130)

        st.caption(f"💡 **Recomendación Pericial:** {sol_data['instrucciones']}")

        st.markdown("---")
        st.markdown("#### 🏆 Precedentes de Dispositivos Aprobados en DIGEMID (Benchmark)")
        prec_list = agent.get_precedents_for_product()
        for p in prec_list:
            with st.expander(f"Registro Sanitario {p.registro_sanitario} — {p.producto}"):
                st.write(f"**Titular:** {p.titular} | **Fabricante:** {p.fabricante}")
                st.write(f"**Calibres Aprobados:** {p.calibres_fr} | **Longitudes:** {p.longitudes_cm}")
                st.write(f"**Vida Útil Aprobada:** {p.vida_util} | **Tiempo de Permanencia:** {p.tiempo_permanencia}")
                st.write(f"**Material:** {p.material}")

    with tab_docs:
        doc_sel = st.selectbox("Seleccione el documento a inspeccionar:", list(res.documents.keys()))
        if doc_sel:
            d_rep = res.documents[doc_sel]
            meta = d_rep.metadata
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Páginas:** {meta.total_pages}")
            c2.write(f"**Tipo:** {meta.file_type} ({'Escaneado / OCR' if meta.is_scanned else 'Digital'})")
            c3.write(f"**Software / Autor:** {meta.author or meta.creator or 'No especificado'}")

            st.json(d_rep.parameters.to_dict())
            st.markdown(f"##### Hallazgos en `{doc_sel}` ({len(d_rep.findings)}):")
            for f in d_rep.findings:
                render_finding_box(f)

    # EXPORTACIÓN DE REPORTES
    st.markdown("---")
    st.markdown("### 📥 Descargar Dictámenes Periciales")
    c_d1, c_d2 = st.columns(2)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_html = REPORTS_DIR / "Dictamen_Pericial_DIGEMID.html"
    out_json = REPORTS_DIR / "Dictamen_Pericial_DIGEMID.json"

    ReportGenerator.export_html(res, str(out_html))
    ReportGenerator.export_json(res, str(out_json))

    with open(out_html, "r", encoding="utf-8") as f:
        html_bytes = f.read().encode("utf-8")
    with open(out_json, "r", encoding="utf-8") as f:
        json_bytes = f.read().encode("utf-8")

    c_d1.download_button(
        "📄 Descargar Reporte HTML Interactivo",
        data=html_bytes,
        file_name="Reporte_Auditoria_DIGEMID.html",
        mime="text/html",
        use_container_width=True
    )
    c_d2.download_button(
        "📊 Descargar Datos JSON Estructurados",
        data=json_bytes,
        file_name="Reporte_Auditoria_DIGEMID.json",
        mime="application/json",
        use_container_width=True
    )
