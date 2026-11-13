"""
Generador de Reportes de Auditoría Documental para DIGEMID.
Genera reportes en HTML interactivo (Executive Dashboard), JSON y Markdown.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from core.models import BatchAuditResult, Severity, Category, Finding
from config import BASE_CASE_INFO, DIGEMID_LEGAL_FRAMEWORK


class ReportGenerator:
    """Generador de reportes visuales y estructurados."""

    @staticmethod
    def export_json(result: BatchAuditResult, output_path: str) -> None:
        """Exporta los resultados a formato JSON estructurado."""
        data = result.to_dict()
        data["base_case"] = BASE_CASE_INFO
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_markdown(result: BatchAuditResult, output_path: str) -> None:
        """Exporta un resumen ejecutivo en formato Markdown."""
        summary = result.to_dict()["summary"]
        md_lines = [
            f"# DICTAMEN REGULATORIO DE AUDITORÍA PRE-VUCE DIGEMID",
            f"**Titular:** {BASE_CASE_INFO['titular']} (RUC {BASE_CASE_INFO['ruc_titular']})  ",
            f"**Fabricante:** {BASE_CASE_INFO['fabricante']}  ",
            f"**Producto:** {BASE_CASE_INFO['producto']}  ",
            f"**Veredicto Oficial:** **{result.verdict}**  ",
            f"**Probabilidad de Denegatoria ante DIGEMID:** **{result.rejection_probability_pct}%**  \n",
            "---",
            "## 1. RESUMEN EJECUTIVO DE HALLAZGOS",
            f"- **Documentos Auditados:** {summary['total_documents']}",
            f"- **Total de Hallazgos:** {summary['total_findings']}",
            f"- **🔴 Fallas Fatales (Rechazo Inminente):** {summary['total_fatal']}",
            f"- **🟡 Observaciones Críticas (Subsanación Obligatoria):** {summary['total_critical']}",
            f"- **🔵 Errores Menores / Tipográficos:** {summary['total_minor']}\n",
            "---",
            "## 2. HALLAZGOS FATALES DE RECHAZO DIRECTO",
        ]

        fatals = [f for f in result.all_findings if f.severity == Severity.FATAL]
        if not fatals:
            md_lines.append("*No se detectaron hallazgos fatales.*")
        else:
            for idx, f in enumerate(fatals, 1):
                p_info = f" (Pág. {f.page})" if f.page else ""
                md_lines.extend([
                    f"### {idx}. {f.title}",
                    f"- **Documento:** `{f.document_name}`{p_info}",
                    f"- **Categoría:** {f.category.value}",
                    f"- **Descripción:** {f.description}",
                    f"- **Texto Detectado:** `{f.detected_text}`",
                    f"- **Texto Esperado:** `{f.expected_text}`",
                    f"- **Base Legal DIGEMID:** *{f.digemid_norm_ref}*",
                    f"- **Acción de Remediación:** {f.remediation_advice}\n",
                ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    @staticmethod
    def export_html(result: BatchAuditResult, output_path: str) -> None:
        """Genera un tablero interactivo moderno en HTML para visualización pericial."""
        data = result.to_dict()
        summary = data["summary"]

        all_findings = result.all_findings
        fatal_findings = [f for f in all_findings if f.severity == Severity.FATAL]
        critical_findings = [f for f in all_findings if f.severity == Severity.CRITICAL]
        minor_findings = [f for f in all_findings if f.severity == Severity.MINOR]

        # Construir filas de la matriz dimensional cruzada
        matrix_rows = []
        for name, rep in result.documents.items():
            p = rep.parameters
            fr = p.diameters_fr_raw or "No declarado"
            cm = p.lengths_cm_raw or "No declarado"
            shelf = p.shelf_life_raw or "No declarado"
            indw = p.indwelling_time_raw or "No declarado"
            comps = ", ".join(p.components) if p.components else "Estándar"
            contam = ", ".join(p.foreign_contaminations) if p.foreign_contaminations else "Ninguna"

            has_error = (
                "70" in cm or "90" in cm or "1 día" in shelf or "6 meses" in indw
                or "NO_COMPONENTS" in comps or p.foreign_contaminations
            )
            row_class = "danger-row" if has_error else ""

            matrix_rows.append(f"""
            <tr class="{row_class}">
                <td><strong>{name}</strong></td>
                <td><span class="badge {'badge-danger' if '28' in fr else 'badge-info'}">{fr}</span></td>
                <td><span class="badge {'badge-danger' if '70' in cm or '90' in cm else 'badge-info'}">{cm}</span></td>
                <td><span class="badge {'badge-danger' if '1 día' in shelf else 'badge-warning'}">{shelf}</span></td>
                <td><span class="badge {'badge-danger' if '6 meses' in indw or 'permanente' in indw.lower() else 'badge-warning'}">{indw}</span></td>
                <td>{comps}</td>
                <td>{f'<span class="badge badge-danger">{contam}</span>' if p.foreign_contaminations else '<span class="text-success">Limpio</span>'}</td>
            </tr>
            """)

        def render_cards(findings: List[Finding], badge_class: str) -> str:
            if not findings:
                return "<p class='text-muted'>No se encontraron observaciones en esta categoría.</p>"
            html_cards = []
            for f in findings:
                page_str = f"Página {f.page}" if f.page else "Multi-documento / General"
                html_cards.append(f"""
                <div class="card finding-card border-{badge_class}">
                    <div class="card-header d-flex justify-content-between">
                        <span class="badge badge-{badge_class}">{f.severity.value}</span>
                        <span class="badge badge-secondary">{f.category.value}</span>
                        <span class="text-muted"><small><strong>{f.document_name}</strong> ({page_str})</small></span>
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{f.title}</h5>
                        <p class="card-text">{f.description}</p>
                        <div class="diff-box">
                            <div class="text-danger"><strong>❌ Texto Detectado:</strong> <code>{f.detected_text}</code></div>
                            <div class="text-success"><strong>✅ Texto Esperado:</strong> <code>{f.expected_text}</code></div>
                        </div>
                        <div class="legal-box mt-2">
                            <small><strong>⚖️ Base Legal DIGEMID:</strong> {f.digemid_norm_ref}</small>
                        </div>
                        <div class="remediation-box mt-2">
                            <small><strong>🛠️ Acción de Remediación Obligatoria:</strong> {f.remediation_advice}</small>
                        </div>
                    </div>
                </div>
                """)
            return "\n".join(html_cards)

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dictamen Regulatorio DIGEMID - {BASE_CASE_INFO['titular']}</title>
    <style>
        :root {{
            --primary: #1e3a8a;
            --danger: #dc2626;
            --warning: #d97706;
            --success: #16a34a;
            --info: #0284c7;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1280px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            color: white;
            padding: 32px;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            font-size: 26px;
            letter-spacing: -0.5px;
        }}
        .header-meta {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .verdict-banner {{
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 24px;
            font-size: 18px;
            font-weight: 700;
            text-align: center;
            letter-spacing: 0.5px;
            background-color: #fee2e2;
            color: #991b1b;
            border: 2px solid #ef4444;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #cbd5e1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .kpi-card.kpi-danger {{ border-left-color: var(--danger); }}
        .kpi-card.kpi-warning {{ border-left-color: var(--warning); }}
        .kpi-card.kpi-info {{ border-left-color: var(--info); }}
        .kpi-val {{
            font-size: 32px;
            font-weight: 800;
            margin-top: 4px;
        }}
        .kpi-lbl {{
            font-size: 13px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .tabs {{
            display: flex;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 24px;
            gap: 8px;
        }}
        .tab-btn {{
            background: none;
            border: none;
            padding: 12px 20px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            color: #64748b;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }}
        .tab-btn.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
        }}
        .tab-pane {{
            display: none;
        }}
        .tab-pane.active {{
            display: block;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
        }}
        .card-header {{
            background: #f1f5f9;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
        }}
        .card-body {{
            padding: 20px;
        }}
        .card-title {{
            margin: 0 0 10px 0;
            font-size: 17px;
            color: #0f172a;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-info {{ background: #e0f2fe; color: #075985; }}
        .badge-secondary {{ background: #f1f5f9; color: #475569; }}
        .diff-box {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            margin-top: 12px;
            font-size: 13px;
        }}
        .diff-box code {{
            background: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #cbd5e1;
        }}
        .legal-box {{
            background: #fefce8;
            border-left: 4px solid #eab308;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        .remediation-box {{
            background: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            font-size: 13px;
        }}
        th {{
            background: #f1f5f9;
            font-weight: 700;
            color: #334155;
        }}
        .danger-row {{
            background-color: #fff1f2;
        }}
        .text-danger {{ color: var(--danger); }}
        .text-success {{ color: var(--success); }}
        .text-muted {{ color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AUDITORÍA FORENSE DOCUMENTAL DIGEMID (PERÚ)</h1>
            <div class="header-meta">
                <strong>Titular Solicitante:</strong> {BASE_CASE_INFO['titular']} (RUC {BASE_CASE_INFO['ruc_titular']}) | 
                <strong>Fabricante:</strong> {BASE_CASE_INFO['fabricante']} (India) | 
                <strong>Producto:</strong> {BASE_CASE_INFO['producto']} ({BASE_CASE_INFO['clasificacion_riesgo']})<br>
                <strong>Antecedentes Críticos:</strong> Exp. 25039778 (Desistido) y Exp. 25157794 (Denegado R.D. N° 4453-2026 / Notificación N° 2026068505)
            </div>
        </div>

        <div class="verdict-banner">
            ⛔ {result.verdict} — PROBABILIDAD DE DENEGATORIA: {result.rejection_probability_pct}%
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-lbl">Documentos Analizados</div>
                <div class="kpi-val">{summary['total_documents']}</div>
            </div>
            <div class="kpi-card kpi-danger">
                <div class="kpi-lbl">🔴 Fallas Fatales (Rechazo)</div>
                <div class="kpi-val text-danger">{summary['total_fatal']}</div>
            </div>
            <div class="kpi-card kpi-warning">
                <div class="kpi-lbl">🟡 Observaciones Críticas</div>
                <div class="kpi-val text-warning">{summary['total_critical']}</div>
            </div>
            <div class="kpi-card kpi-info">
                <div class="kpi-lbl">🔵 Errores Menores / Formato</div>
                <div class="kpi-val text-info">{summary['total_minor']}</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="openTab(event, 'tab-fatal')">🔴 Fallas Fatales ({len(fatal_findings)})</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-critical')">🟡 Observaciones Críticas ({len(critical_findings)})</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-minor')">🔵 Errores Menores ({len(minor_findings)})</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-matrix')">📊 Matriz Dimensional Cruzada</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-legal')">⚖️ Marco Normativo DIGEMID</button>
        </div>

        <div id="tab-fatal" class="tab-pane active">
            {render_cards(fatal_findings, "danger")}
        </div>

        <div id="tab-critical" class="tab-pane">
            {render_cards(critical_findings, "warning")}
        </div>

        <div id="tab-minor" class="tab-pane">
            {render_cards(minor_findings, "info")}
        </div>

        <div id="tab-matrix" class="tab-pane">
            <div class="card p-3">
                <h4 style="margin: 0 0 12px 0;">Matriz Dimensional y Clínica Comparativa entre Documentos</h4>
                <p class="text-muted"><small>Muestra las declaraciones de Calibres Fr, Longitudes cm, Vida útil y Permanencia en cada documento. Las filas en rojo indican discordancias o infiltraciones de otros dispositivos.</small></p>
                <table>
                    <thead>
                        <tr>
                            <th>Documento</th>
                            <th>Diámetros (Fr)</th>
                            <th>Longitudes (cm)</th>
                            <th>Vida Útil</th>
                            <th>Permanencia Clínica</th>
                            <th>Componentes Declarados</th>
                            <th>Contaminaciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(matrix_rows)}
                    </tbody>
                </table>
            </div>
        </div>

        <div id="tab-legal" class="tab-pane">
            <div class="card p-3">
                <h4 style="margin: 0 0 12px 0;">Marco Legal y Parámetros Obligatorios de DIGEMID</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Disposición Legal</th>
                            <th>Artículo / Norma</th>
                            <th>Exigencia Vinculante para Catéter Doble J</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td><strong>{k}</strong></td><td>{v['articulo']}</td><td>{v['descripcion']}</td></tr>" for k, v in DIGEMID_LEGAL_FRAMEWORK.items())}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function openTab(evt, tabName) {{
            let i, tabpane, tabbtn;
            tabpane = document.getElementsByClassName("tab-pane");
            for (i = 0; i < tabpane.length; i++) {{
                tabpane[i].classList.remove("active");
            }}
            tabbtn = document.getElementsByClassName("tab-btn");
            for (i = 0; i < tabbtn.length; i++) {{
                tabbtn[i].classList.remove("active");
            }}
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }}
    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
