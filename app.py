"""
Aplicación Web Interactiva con Streamlit para el Auditor Documental DIGEMID.
Permite auditar lotes de documentos en tiempo real, visualizar la matriz cruzada,
explorar hallazgos categorizados por severidad y exportar dictámenes periciales.
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
from config import BASE_CASE_INFO, DEFAULT_TEST_DATA_DIR, REPORTS_DIR, DIGEMID_LEGAL_FRAMEWORK

# Configuración de página
st.set_page_config(
    page_title="Auditor Documental DIGEMID · Aporte Médico",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .fatal-badge {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .critical-badge {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .minor-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .diff-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "audit_result" not in st.session_state:
        st.session_state.audit_result = None
    if "last_source" not in st.session_state:
        st.session_state.last_source = ""


init_session_state()

# Barra lateral (Configuración y Carga)
st.sidebar.image("https://img.icons8.com/color/96/medical-history.png", width=64)
st.sidebar.title("Auditor DIGEMID")
st.sidebar.caption("Control Documental Pre-Radicación VUCE")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Titular:** {BASE_CASE_INFO['titular']}")
st.sidebar.markdown(f"**RUC:** `{BASE_CASE_INFO['ruc_titular']}`")
st.sidebar.markdown(f"**Fabricante:** {BASE_CASE_INFO['fabricante']}")
st.sidebar.markdown(f"**Producto:** {BASE_CASE_INFO['producto']}")
st.sidebar.markdown(f"**Riesgo:** {BASE_CASE_INFO['clasificacion_riesgo']}")
st.sidebar.markdown("---")

modo_origen = st.sidebar.radio(
    "Fuente de Documentos:",
    ["Banco de Pruebas Real (ACE Medical)", "Subir Archivos (PDF / DOCX)"],
    index=0
)

archivos_a_procesar = []

if modo_origen == "Banco de Pruebas Real (ACE Medical)":
    if DEFAULT_TEST_DATA_DIR.exists():
        archivos_reales = list(DEFAULT_TEST_DATA_DIR.glob("*.pdf")) + list(DEFAULT_TEST_DATA_DIR.glob("*.docx"))
        st.sidebar.success(f"Detectados {len(archivos_reales)} documentos en carpeta real.")
        archivos_seleccionados = st.sidebar.multiselect(
            "Seleccionar documentos a auditar:",
            options=[f.name for f in archivos_reales],
            default=[f.name for f in archivos_reales][:8] # Primeros 8 por defecto
        )
        archivos_a_procesar = [DEFAULT_TEST_DATA_DIR / name for name in archivos_seleccionados]
    else:
        st.sidebar.warning(f"Ruta base no accesible: {DEFAULT_TEST_DATA_DIR}")
else:
    uploaded_files = st.sidebar.file_uploader(
        "Arrastra tus expedientes técnicos:",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    if uploaded_files:
        temp_dir = Path(tempfile.gettempdir()) / "digemid_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        for uf in uploaded_files:
            dest = temp_dir / uf.name
            with open(dest, "wb") as f:
                f.write(uf.getbuffer())
            archivos_a_procesar.append(dest)

ejecutar_btn = st.sidebar.button("🚀 EJECUTAR AUDITORÍA DOCUMENTAL", type="primary", use_container_width=True)

# Lógica de Ejecución
if ejecutar_btn and archivos_a_procesar:
    with st.spinner("Ejecutando auditoría forense con OCR y motor de reglas..."):
        auditor = DigemidDocumentAuditor(enable_ocr=True)
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def progress_cb(curr, total, msg):
            pct = curr / max(1, total)
            progress_bar.progress(pct)
            status_text.text(f"[{curr}/{total}] {msg}")

        result = auditor.audit_batch([str(p) for p in archivos_a_procesar], progress_callback=progress_cb)
        progress_bar.empty()
        status_text.empty()
        st.session_state.audit_result = result
        st.session_state.last_source = modo_origen
        st.success("✅ Auditoría completada con éxito.")

# Área Principal de Contenido
st.markdown('<div class="main-title">AUDITOR DOCUMENTAL DE REGISTROS SANITARIOS DIGEMID</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Peritaje Automatizado de Fallas de Digitación, Notación Científica, Inconsistencias Cruzadas y Contravenciones Normativas</div>', unsafe_allow_html=True)

res: BatchAuditResult = st.session_state.audit_result

if res is None:
    st.info("👈 Seleccione los documentos en el panel lateral y haga clic en **'EJECUTAR AUDITORÍA DOCUMENTAL'** para iniciar el análisis.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 📋 Módulos de Verificación Integrados
        1. **Tipografía y Notación Científica:**
           - Detección de exponentes microbiológicos erróneos (`SAL 10^6` vs `10^-6`).
           - Corrección de normas ISO mal digitadas (`ISO 111737`).
           - Detección de normas derogadas (`ISO 14971:2012`, `MDD 93/42/EEC`, `EN 980:2008`).
        2. **Traducción y Léxico Médico:**
           - Filtro de traducciones automáticas absurdas (*"no debe mantenerse mora"*, *"el doble coleta"*, *"de la vegiga"*, *"el gato No.*").
           - Mezclas lingüísticas e inconsistencias léxicas (*blíster* en inglés, *silicon* vs *silicone*, *Columbia*).
        3. **Integridad Estructural y Firmas:**
           - Páginas rotadas, invertidas (180°) o espejadas.
           - Omisión de firmas formales en reportes clínicos (CER) y verificación de diseño (DVR).
           - Celdas vacías y formatos que solo contienen *"Complies"* sin valores reales.
        """)
    with col2:
        st.markdown("""
        ### ⚖️ Concordancia Cruzada y Marco DIGEMID
        4. **Matriz Dimensional y Paramétrica (Cross-Clash):**
           - Descalce de calibres Fr (2–12 Fr vs 3–8 Fr).
           - Infiltración de otros productos (longitudes de 70–90 cm de catéter ureteral externo).
           - Descalce de vida útil (3 años vs 5 años vs 1 día).
           - Descalce de tiempo de permanencia clínica (<25 días vs 30–90 días vs 6 meses).
           - Descalce de componentes del Set (CER sin componentes vs Set con 5 accesorios).
        5. **Contaminación por Copia Clínica:**
           - Drenaje quirúrgico (*"Bottle/grenade type"*).
           - Procedimientos gastroenterológicos en dispositivos urológicos.
           - Abrazadera de cordón umbilical (*"Umbilical cord clamp"*).
           - Catéteres balón Foley (8–28 Fr con globo de 3–50 ml).
        """)

else:
    # BANNER DE VEREDICTO
    prob = res.rejection_probability_pct
    verdict = res.verdict
    if res.total_fatal > 0:
        st.error(f"⛔ **DICTAMEN: {verdict}**  \n**Probabilidad de Denegatoria ante DIGEMID: {prob}%** (Existen {res.total_fatal} defectos fatales no subsanables de oficio).")
    elif res.total_critical > 0:
        st.warning(f"⚠️ **DICTAMEN: {verdict}**  \n**Probabilidad de Observación: {prob}%** (Requiere subsanación técnica obligatoria).")
    else:
        st.success(f"✅ **DICTAMEN: {verdict}**  \n**Apto para trámite en VUCE.**")

    # MÉTRICAS KPI
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Documentos Auditados", len(res.documents))
    kpi2.metric("🔴 Fallas Fatales", res.total_fatal, help="Causales directas de denegatoria y pérdida de tasa TUPA")
    kpi3.metric("🟡 Observaciones Críticas", res.total_critical, help="Observaciones seguras en Notificación oficial")
    kpi4.metric("🔵 Errores Menores / Formato", res.total_minor, help="Traducción, tildes y detalles formales")

    st.markdown("---")

    # PESTAÑAS DE NAVEGACIÓN
    tab_fatal, tab_critical, tab_minor, tab_matrix, tab_docs, tab_legal = st.tabs([
        f"🔴 Fallas Fatales ({res.total_fatal})",
        f"🟡 Observaciones Críticas ({res.total_critical})",
        f"🔵 Errores Menores ({res.total_minor})",
        "📊 Matriz Dimensional Cruzada",
        "📄 Explorador por Documento",
        "⚖️ Marco Legal DIGEMID"
    ])

    def render_finding_item(f):
        badge_color = "fatal-badge" if f.severity == Severity.FATAL else ("critical-badge" if f.severity == Severity.CRITICAL else "minor-badge")
        with st.expander(f"[{f.severity.value}] {f.title} — {f.document_name}", expanded=(f.severity == Severity.FATAL)):
            st.markdown(f"<span class='{badge_color}'>{f.severity.value}</span> | **Categoría:** {f.category.value} | **Página:** {f.page or 'General'}", unsafe_allow_html=True)
            st.write(f.description)
            st.markdown(f"""
            <div class="diff-container">
                <div style="color: #dc2626;"><strong>❌ Texto Detectado:</strong> <code>{f.detected_text}</code></div>
                <div style="color: #16a34a; margin-top: 4px;"><strong>✅ Texto Esperado:</strong> <code>{f.expected_text}</code></div>
            </div>
            """, unsafe_allow_html=True)
            st.info(f"**⚖️ Base Legal DIGEMID:** {f.digemid_norm_ref}")
            st.success(f"**🛠️ Acción de Remediación Obligatoria:** {f.remediation_advice}")

    # Pestaña 1: Fatales
    with tab_fatal:
        fatals = [f for f in res.all_findings if f.severity == Severity.FATAL]
        if not fatals:
            st.success("No se encontraron fallas fatales.")
        else:
            st.markdown("### Fallas con Rechazo Seguro (Denegatoria de Plano)")
            for f in fatals:
                render_finding_item(f)

    # Pestaña 2: Críticas
    with tab_critical:
        criticals = [f for f in res.all_findings if f.severity == Severity.CRITICAL]
        if not criticals:
            st.success("No se encontraron observaciones críticas.")
        else:
            st.markdown("### Observaciones Críticas de Subsanación Obligatoria")
            for f in criticals:
                render_finding_item(f)

    # Pestaña 3: Menores
    with tab_minor:
        minors = [f for f in res.all_findings if f.severity == Severity.MINOR]
        if not minors:
            st.success("No se encontraron observaciones menores.")
        else:
            st.markdown("### Errores Tipográficos y Formato")
            for f in minors:
                render_finding_item(f)

    # Pestaña 4: Matriz Dimensional Cruzada
    with tab_matrix:
        st.markdown("### Matriz Dimensional y Clínica Comparativa entre Documentos")
        st.write("Identifica descalces de calibres, longitudes infiltradas (70–90 cm) y contradicciones de vida útil / permanencia.")

        matrix_data = []
        for name, rep in res.documents.items():
            p = rep.parameters
            matrix_data.append({
                "Documento": name,
                "Calibres Fr": p.diameters_fr_raw or "No declarado",
                "Longitud cm": p.lengths_cm_raw or "No declarado",
                "Vida Útil": p.shelf_life_raw or "No declarado",
                "Permanencia Clínica": p.indwelling_time_raw or "No declarado",
                "Componentes": ", ".join(p.components) if p.components else "Estándar",
                "Contaminaciones": ", ".join(p.foreign_contaminations) if p.foreign_contaminations else "Limpio",
            })
        df_matrix = pd.DataFrame(matrix_data)
        st.dataframe(df_matrix, use_container_width=True)

        if res.cross_findings:
            st.markdown("#### Alertas de Inconsistencia Cruzada Detectadas:")
            for cf in res.cross_findings:
                render_finding_item(cf)

    # Pestaña 5: Explorador por Documento
    with tab_docs:
        doc_selected = st.selectbox("Seleccione el archivo a examinar:", list(res.documents.keys()))
        if doc_selected:
            d_rep = res.documents[doc_selected]
            meta = d_rep.metadata
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.write(f"**Páginas Totales:** {meta.total_pages}")
            col_m1.write(f"**Tipo:** {meta.file_type}")
            col_m2.write(f"**Escaneado / OCR:** {'Sí' if meta.is_scanned else 'No (Digital)'}")
            col_m2.write(f"**Autor:** {meta.author or 'No especificado'}")
            col_m3.write(f"**Software Creador:** {meta.creator or meta.producer or 'No disponible'}")

            st.markdown("##### Parámetros Extraídos del Archivo:")
            st.json(d_rep.parameters.to_dict())

            st.markdown(f"##### Hallazgos en este Documento ({len(d_rep.findings)}):")
            for f in d_rep.findings:
                render_finding_item(f)

    # Pestaña 6: Marco Legal DIGEMID
    with tab_legal:
        st.markdown("### Marco Jurídico y Normativo Obligatorio (DIGEMID / MINSA)")
        for k, v in DIGEMID_LEGAL_FRAMEWORK.items():
            with st.expander(f"{v['articulo']}"):
                st.write(v['descripcion'])

    # SECCIÓN DE EXPORTACIÓN Y DESCARGAS
    st.markdown("---")
    st.markdown("### 📥 Exportación de Informes Periciales")
    c_exp1, c_exp2, c_exp3 = st.columns(3)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_html = REPORTS_DIR / "Dictamen_Pericial_DIGEMID.html"
    temp_json = REPORTS_DIR / "Dictamen_Pericial_DIGEMID.json"
    temp_md = REPORTS_DIR / "Dictamen_Pericial_DIGEMID.md"

    ReportGenerator.export_html(res, str(temp_html))
    ReportGenerator.export_json(res, str(temp_json))
    ReportGenerator.export_markdown(res, str(temp_md))

    with open(temp_html, "r", encoding="utf-8") as f:
        html_bytes = f.read().encode("utf-8")
    with open(temp_json, "r", encoding="utf-8") as f:
        json_bytes = f.read().encode("utf-8")
    with open(temp_md, "r", encoding="utf-8") as f:
        md_bytes = f.read().encode("utf-8")

    c_exp1.download_button(
        label="📄 Descargar Reporte HTML Interactivo",
        data=html_bytes,
        file_name="Reporte_Auditoria_DIGEMID.html",
        mime="text/html",
        use_container_width=True
    )
    c_exp2.download_button(
        label="📊 Descargar Datos JSON Estructurados",
        data=json_bytes,
        file_name="Reporte_Auditoria_DIGEMID.json",
        mime="application/json",
        use_container_width=True
    )
    c_exp3.download_button(
        label="📝 Descargar Resumen Markdown",
        data=md_bytes,
        file_name="Dictamen_Ejecutivo_DIGEMID.md",
        mime="text/markdown",
        use_container_width=True
    )
