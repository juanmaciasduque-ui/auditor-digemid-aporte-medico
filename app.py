"""
Aplicación Web Interactiva - Auditor Documental DIGEMID (Aporte Médico Perú).
Diseño UI/UX de Alta Gama Corporativa con Logo Centrado, Estilos Modernos y Alta Ergonomía.
Incluye Mini-Agente Regulatorio DIGEMID para búsqueda normativa en vivo y generación de soluciones oficiales.
"""

import os
import sys
import base64
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

from core.auditor import DigemidDocumentAuditor
from core.report_generator import ReportGenerator
from core.models import Severity, Category, BatchAuditResult
from core.agents.digemid_agent import DigemidAgent
from config import (
    BASE_CASE_INFO,
    DEFAULT_TEST_DATA_DIR,
    VAGINAL_SLING_DATA_DIR,
    REPORTS_DIR,
    DIGEMID_LEGAL_FRAMEWORK,
    PRODUCT_FAMILIES
)

# Configuración de página
st.set_page_config(
    page_title="Auditor Forense DIGEMID · Aporte Médico Perú",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_base64_image(image_path: Path) -> str:
    """Convierte una imagen local a base64 para incrustación fluida en HTML."""
    if image_path.exists():
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


logo_path = Path(__file__).parent / "assets" / "logo_aporte_medico.png"
logo_b64 = get_base64_image(logo_path)

# ==============================================================================
# ESTILOS CSS DE ALTA GAMA CORPORATIVA (UX / UI MODERN SAAS)
# ==============================================================================
st.markdown("""
<style>
    /* Tipografía y contenedor general */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }
    
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        max-width: 1240px;
    }

    /* BANNER HERO CORPORATIVO CENTRADO */
    .hero-banner {
        background: linear-gradient(160deg, #ffffff 0%, #f8fafc 45%, #eff6ff 100%);
        border: 1.5px solid #dbeafe;
        border-radius: 20px;
        box-shadow: 0 12px 35px -5px rgba(30, 58, 138, 0.08), 0 4px 10px -2px rgba(0, 0, 0, 0.02);
        text-align: center;
        padding: 36px 30px 30px 30px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 6px;
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 35%, #0284c7 70%, #10b981 100%);
    }
    .hero-logo-box {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 18px;
    }
    .hero-logo {
        max-height: 115px;
        max-width: 320px;
        object-fit: contain;
        filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.08));
        transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .hero-logo:hover {
        transform: scale(1.03);
    }
    .hero-badge-row {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 14px;
    }
    .hero-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .pill-navy { background-color: #e0e7ff; color: #1e3a8a; border: 1px solid #c7d2fe; }
    .pill-blue { background-color: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .pill-cyan { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .pill-green { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.6px;
        line-height: 1.2;
    }
    .hero-company {
        font-size: 1.15rem;
        font-weight: 700;
        color: #2563eb;
        margin: 6px 0 10px 0;
        letter-spacing: 0.5px;
    }
    .hero-subtitle {
        font-size: 0.96rem;
        color: #475569;
        max-width: 820px;
        margin: 0 auto;
        line-height: 1.55;
    }

    /* TARJETA DE PERFIL Y SELECTOR */
    .profile-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 22px;
    }

    /* BOTONES RESALTADOS */
    button[kind="primary"] {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #0284c7 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.4px !important;
        padding: 0.75rem 1.8rem !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 8px 22px -2px rgba(37, 99, 235, 0.45) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 14px 28px -2px rgba(37, 99, 235, 0.6) !important;
        background: linear-gradient(135deg, #172554 0%, #1d4ed8 50%, #0369a1 100%) !important;
    }
    button[kind="secondary"] {
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        color: #1e3a8a !important;
        background: #ffffff !important;
        padding: 0.65rem 1.2rem !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease-in-out !important;
    }
    button[kind="secondary"]:hover {
        border-color: #2563eb !important;
        color: #2563eb !important;
        background: #f0f7ff !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.15) !important;
    }

    /* CAJA DE CARGA RÁPIDA DE PRUEBAS */
    .quick-suite-box {
        background: #f8fafc;
        border: 1px dashed #94a3b8;
        border-radius: 14px;
        padding: 16px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* BADGES Y ETIQUETAS */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.78rem;
        letter-spacing: 0.3px;
    }
    .badge-fatal { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .badge-critical { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-minor { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

    /* TARJETAS KPI DE RESULTADOS */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin: 20px 0;
    }
    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }
    .kpi-fatal { border-top: 4px solid #dc2626; }
    .kpi-critical { border-top: 4px solid #d97706; }
    .kpi-minor { border-top: 4px solid #0284c7; }
    .kpi-total { border-top: 4px solid #4f46e5; }

    /* CONTENEDOR DE DISCREPANCIAS Y DIFERENCIAS */
    .diff-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px;
        margin: 10px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        line-height: 1.5;
    }
    .diff-detected {
        background-color: #fff1f2;
        border-left: 4px solid #e11d48;
        padding: 8px 12px;
        border-radius: 6px;
        color: #9f1239;
        margin-bottom: 6px;
    }
    .diff-expected {
        background-color: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 8px 12px;
        border-radius: 6px;
        color: #166534;
    }

    /* PESTAÑAS ELEGANTES */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 18px;
        font-weight: 700;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        border-top: 3px solid #1e3a8a !important;
        color: #1e3a8a !important;
    }
</style>
""", unsafe_allow_html=True)


# Estado de sesión
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "agent" not in st.session_state:
    st.session_state.agent = DigemidAgent()

agent: DigemidAgent = st.session_state.agent

# ==============================================================================
# HERO BANNER PRINCIPAL CON LOGO CENTRADO Y METADATOS CORPORATIVOS
# ==============================================================================
logo_html = ""
if logo_b64:
    logo_html = f'<div class="hero-logo-box"><img src="data:image/png;base64,{logo_b64}" alt="Aporte Médico Perú Logo" class="hero-logo" /></div>'
else:
    logo_html = '<div class="hero-logo-box"><img src="https://img.icons8.com/color/120/medical-history.png" width="90" alt="Logo" class="hero-logo" /></div>'

st.markdown(f"""
<div class="hero-banner">
    {logo_html}
    <div class="hero-badge-row">
        <span class="hero-pill pill-navy">🇵🇪 PERÚ · DIGEMID / MINSA</span>
        <span class="hero-pill pill-blue">⚖️ D.S. 016-2011-SA / D.S. 003-2020-SA</span>
        <span class="hero-pill pill-cyan">🛡️ CONTROL PRE-RADICACIÓN VUCE</span>
        <span class="hero-pill pill-green">🔒 100% CONFIDENCIAL Y LOCAL</span>
    </div>
    <h1 class="hero-title">AUDITOR FORENSE DOCUMENTAL</h1>
    <h2 class="hero-company">APORTE MÉDICO PERÚ S.A.C.</h2>
    <p class="hero-subtitle">
        Inspección técnica automatizada de expedientes para registros sanitarios de <strong>Dispositivos Médicos (Clases I, IIa, IIb, III y IV)</strong>.
        Detección pericial de inconsistencias cruzadas, descalces de medidas, incongruencias de esterilización, errores de traducción y causales de rechazo oficial.
    </p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SELECTOR DE PERFIL DE DISPOSITIVO MÉDICO
# ==============================================================================
col_fam, col_info_fam = st.columns([1.6, 2.4])
with col_fam:
    selected_family_key = st.selectbox(
        "🎯 Perfil de Dispositivo Médico a Auditar:",
        list(PRODUCT_FAMILIES.keys()),
        format_func=lambda k: PRODUCT_FAMILIES[k]["nombre"],
        index=0,
        help="El motor calibra automáticamente las reglas universales del D.S. 016-2011-SA y las unidades dimensionales esperadas."
    )
with col_info_fam:
    fam_info = PRODUCT_FAMILIES[selected_family_key]
    st.markdown(f"""
    <div class="profile-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; color: #1e3a8a; font-size: 0.95rem;">⚖️ Base Legal: <code>{fam_info.get('norma_base', 'D.S. 016-2011-SA')}</code></span>
            <span class="badge" style="background:#e0e7ff; color:#1e3a8a;">🛡️ {fam_info.get('clase_defecto', 'Clase I-IV')}</span>
        </div>
        <div style="font-size: 0.88rem; color: #475569; line-height: 1.45;">
            {fam_info['descripcion']}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# ZONA DE CARGA DE DOCUMENTOS Y BANCO DE PRUEBAS
# ==============================================================================
c_upload, c_quick = st.columns([2.8, 1.2])

with c_upload:
    uploaded_files = st.file_uploader(
        "📂 Arrastre aquí los documentos (PDFs, Word DOCX) o seleccione los archivos del expediente técnico:",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Puede arrastrar decenas de archivos o carpetas completas. Soporta expedientes técnicos de hasta 2 GB."
    )

with c_quick:
    st.markdown("""
    <div style="font-weight: 700; color: #1e3a8a; margin-bottom: 6px; font-size: 0.92rem;">
        ⚡ Pruebas con Expedientes Reales:
    </div>
    """, unsafe_allow_html=True)
    test_suite_btn = st.button("🧪 Caso 1: Catéteres Doble J\n(ACE Medical · India)", use_container_width=True)
    test_sling_btn = st.button("🧪 Caso 2: Cinta Vaginal / Mallas\n(Orion · Malla TOT/TVT)", use_container_width=True)

archivos_para_auditar = []

if test_suite_btn:
    if DEFAULT_TEST_DATA_DIR.exists():
        archivos_para_auditar = list(DEFAULT_TEST_DATA_DIR.glob("*.pdf")) + list(DEFAULT_TEST_DATA_DIR.glob("*.docx"))
        archivos_para_auditar = [f for f in archivos_para_auditar if "EXPEDIENTE" not in f.name.upper() and "DOCUMENTOS TÉCNICOS" not in f.name.upper()]
        st.toast(f"Cargados {len(archivos_para_auditar)} documentos del Caso Real 1 (Catéteres Doble J).", icon="📂")
    else:
        st.error(f"No se encontró el directorio base {DEFAULT_TEST_DATA_DIR}")

elif test_sling_btn:
    if VAGINAL_SLING_DATA_DIR.exists():
        archivos_para_auditar = list(VAGINAL_SLING_DATA_DIR.glob("*.pdf")) + list(VAGINAL_SLING_DATA_DIR.glob("*.docx"))
        archivos_para_auditar = [f for f in archivos_para_auditar if not f.is_dir()][:10]
        st.toast(f"Cargados {len(archivos_para_auditar)} documentos del Caso Real 2 (Cintas Vaginales / Mallas).", icon="📂")
    else:
        st.error(f"No se encontró el directorio base {VAGINAL_SLING_DATA_DIR}")

elif uploaded_files:
    temp_dir = Path(tempfile.gettempdir()) / "aporte_digemid_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for uf in uploaded_files:
        dest = temp_dir / uf.name
        with open(dest, "wb") as f:
            f.write(uf.getbuffer())
        archivos_para_auditar.append(dest)


# ==============================================================================
# BOTÓN DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if archivos_para_auditar:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_act1, col_act2 = st.columns([2.3, 1.2])
    with col_act1:
        st.info(f"📋 **{len(archivos_para_auditar)} documentos listos para auditar:** {', '.join([f.name for f in archivos_para_auditar[:4]])}{'...' if len(archivos_para_auditar) > 4 else ''}")
    with col_act2:
        ejecutar = st.button("🚀 INICIAR AUDITORÍA FORENSE", type="primary", use_container_width=True)

    if ejecutar:
        with st.spinner("Ejecutando lectura neuronal OCR, extracción y matriz de concordancia cruzada..."):
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
            st.toast("Auditoría pericial completada con éxito.", icon="✅")


# ==============================================================================
# RESULTADOS DE LA AUDITORÍA
# ==============================================================================
res: BatchAuditResult = st.session_state.audit_result

if res is not None:
    st.markdown("---")

    # BANNER DE DICTAMEN PERICIAL
    prob = res.rejection_probability_pct
    verdict = res.verdict
    
    if res.total_fatal > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fff1f2 0%, #fee2e2 100%); border: 2px solid #f87171; border-radius: 14px; padding: 20px 24px; margin-bottom: 22px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span style="font-size: 2.2rem;">⛔</span>
                <div>
                    <h3 style="color: #991b1b; margin: 0; font-size: 1.35rem; font-weight: 800;">DICTAMEN PERICIAL: {verdict}</h3>
                    <p style="color: #7f1d1d; margin: 4px 0 0 0; font-size: 0.98rem; font-weight: 500;">
                        <strong>Probabilidad de Denegatoria de Oficio ante DIGEMID: {prob}%</strong> — Se han detectado <strong>{res.total_fatal} fallas fatales directas</strong> que motivarán pérdida de tasa TUPA o nulidad procesal si se radican en VUCE.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif res.total_critical > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 2px solid #fbbf24; border-radius: 14px; padding: 20px 24px; margin-bottom: 22px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span style="font-size: 2.2rem;">⚠️</span>
                <div>
                    <h3 style="color: #92400e; margin: 0; font-size: 1.35rem; font-weight: 800;">DICTAMEN PERICIAL: {verdict}</h3>
                    <p style="color: #78350f; margin: 4px 0 0 0; font-size: 0.98rem; font-weight: 500;">
                        <strong>Probabilidad de Notificación con Observación: {prob}%</strong> — Se requiere subsanación técnica obligatoria antes de radicar.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #4ade80; border-radius: 14px; padding: 20px 24px; margin-bottom: 22px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span style="font-size: 2.2rem;">✅</span>
                <div>
                    <h3 style="color: #166534; margin: 0; font-size: 1.35rem; font-weight: 800;">DICTAMEN PERICIAL: {verdict}</h3>
                    <p style="color: #14532d; margin: 4px 0 0 0; font-size: 0.98rem; font-weight: 500;">
                        Expediente técnico íntegro y consistente. <strong>Apto para radicación oficial en VUCE.</strong>
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # TARJETAS KPI DE RESUMEN
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="kpi-card kpi-total">
            <div style="font-size: 0.85rem; font-weight: 700; color: #4338ca; text-transform: uppercase;">Documentos Auditados</div>
            <div style="font-size: 2.1rem; font-weight: 800; color: #1e1b4b; margin: 4px 0;">{len(res.documents)}</div>
            <div style="font-size: 0.8rem; color: #64748b;">Archivos procesados en el lote</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="kpi-card kpi-fatal">
            <div style="font-size: 0.85rem; font-weight: 700; color: #b91c1c; text-transform: uppercase;">🔴 Fallas Fatales</div>
            <div style="font-size: 2.1rem; font-weight: 800; color: #7f1d1d; margin: 4px 0;">{res.total_fatal}</div>
            <div style="font-size: 0.8rem; color: #991b1b;">Causales de denegatoria directa</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="kpi-card kpi-critical">
            <div style="font-size: 0.85rem; font-weight: 700; color: #b45309; text-transform: uppercase;">🟡 Observaciones Críticas</div>
            <div style="font-size: 2.1rem; font-weight: 800; color: #78350f; margin: 4px 0;">{res.total_critical}</div>
            <div style="font-size: 0.8rem; color: #92400e;">Observaciones en Notificación</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="kpi-card kpi-minor">
            <div style="font-size: 0.85rem; font-weight: 700; color: #0369a1; text-transform: uppercase;">🔵 Errores Menores</div>
            <div style="font-size: 2.1rem; font-weight: 800; color: #0c4a6e; margin: 4px 0;">{res.total_minor}</div>
            <div style="font-size: 0.8rem; color: #0284c7;">Typos, formato y traducción</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # PESTAÑAS DE ANÁLISIS ESTRUCTURADO
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
                <div class="diff-detected"><strong>❌ Detectado en Documento:</strong> <code>{f.detected_text}</code></div>
                <div class="diff-expected"><strong>✅ Exigencia Reglamentaria:</strong> <code>{f.expected_text}</code></div>
            </div>
            """, unsafe_allow_html=True)
            st.info(f"**⚖️ Exigencia Legal DIGEMID:** {f.digemid_norm_ref}")
            st.success(f"**🛠️ Instrucción de Subsanación Pericial:** {f.remediation_advice}")

    with tab_fatal:
        fatals = [f for f in res.all_findings if f.severity == Severity.FATAL]
        if not fatals:
            st.success("🎉 ¡Excelente! No se detectaron fallas fatales en este expediente.")
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
        st.markdown("### 📊 Matriz Dimensional y Clínica Comparativa entre Documentos")
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
        st.write("Seleccione el problema a resolver para generar el redactado técnico formal para el fabricante o para el escrito de subsanación ante DIGEMID:")

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
            st.text_area("Instrucción Oficial en Inglés para Solicitar al Fabricante:", sol_data["texto_ingles_ace"], height=130)

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
