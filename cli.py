"""
Interfaz de Línea de Comandos (CLI) con formato Rich para el Auditor Documental DIGEMID.
Permite auditar archivos individuales o carpetas completas y exportar reportes.
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from core.auditor import DigemidDocumentAuditor
from core.report_generator import ReportGenerator
from core.models import Severity
from config import DEFAULT_TEST_DATA_DIR, REPORTS_DIR, BASE_CASE_INFO

console = Console()


def run_cli_audit(files: list, output_html: str = None, output_json: str = None):
    console.print(Panel.fit(
        f"[bold white on blue] SISTEMA AUDITOR DOCUMENTAL DIGEMID (PERÚ) [/bold white on blue]\n"
        f"[bold]Titular:[/bold] {BASE_CASE_INFO['titular']} | [bold]Fabricante:[/bold] {BASE_CASE_INFO['fabricante']}\n"
        f"[bold]Producto:[/bold] {BASE_CASE_INFO['producto']}\n"
        f"[dim]Control de Inconsistencias, Notación Científica, Fórmulas y Contravenciones Normativas[/dim]",
        border_style="blue"
    ))

    if not files:
        console.print("[bold red]❌ No se encontraron archivos para auditar.[/bold red]")
        sys.exit(1)

    auditor = DigemidDocumentAuditor(enable_ocr=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Auditando documentos...", total=len(files))

        def cb(curr, total, msg):
            progress.update(task, completed=curr, description=f"[cyan]{msg}")

        result = auditor.audit_batch([str(f) for f in files], progress_callback=cb)

    # 1. Tabla de Resumen
    summary = result.to_dict()["summary"]
    table_sum = Table(title="📊 RESUMEN EJECUTIVO DE AUDITORÍA", border_style="bright_blue")
    table_sum.add_column("Métrica", style="bold")
    table_sum.add_column("Valor", justify="right")

    table_sum.add_row("Documentos Analizados", str(summary["total_documents"]))
    table_sum.add_row("Total de Hallazgos Detectados", str(summary["total_findings"]))
    table_sum.add_row("🔴 Fallas Fatales (Rechazo Inminente)", f"[bold red]{summary['total_fatal']}[/bold red]")
    table_sum.add_row("🟡 Observaciones Críticas (Subsanación)", f"[bold yellow]{summary['total_critical']}[/bold yellow]")
    table_sum.add_row("🔵 Errores Menores / Formato", f"[bold blue]{summary['total_minor']}[/bold blue]")
    table_sum.add_row("Probabilidad de Denegatoria", f"[bold red]{summary['rejection_probability_pct']}%[/bold red]")
    table_sum.add_row("Veredicto Técnico-Legal", f"[bold white on red] {result.verdict} [/bold white on red]" if summary['total_fatal'] > 0 else f"[bold green]{result.verdict}[/bold green]")

    console.print(table_sum)

    # 2. Tabla de Fallas Fatales
    fatals = [f for f in result.all_findings if f.severity == Severity.FATAL]
    if fatals:
        table_fatal = Table(title="🔴 FALLAS FATALES DE RECHAZO DIRECTO ANTE DIGEMID", border_style="red")
        table_fatal.add_column("Documento", style="cyan", width=25)
        table_fatal.add_column("Categoría", width=20)
        table_fatal.add_column("Hallazgo / Título", style="bold red", width=35)
        table_fatal.add_column("Texto Detectado vs Esperado", width=40)

        for f in fatals[:15]: # Primeros 15
            p_str = f" (p.{f.page})" if f.page else ""
            table_fatal.add_row(
                f"{f.document_name[:22]}...{p_str}" if len(f.document_name) > 22 else f"{f.document_name}{p_str}",
                f.category.value[:18],
                f.title,
                f"[red]- {f.detected_text}[/red]\n[green]+ {f.expected_text}[/green]"
            )
        console.print(table_fatal)

    # 3. Exportar Reportes
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html_file = output_html or str(REPORTS_DIR / "Reporte_Auditoria_DIGEMID.html")
    json_file = output_json or str(REPORTS_DIR / "Reporte_Auditoria_DIGEMID.json")

    ReportGenerator.export_html(result, html_file)
    ReportGenerator.export_json(result, json_file)

    console.print(f"\n[bold green]✅ Reporte interactivo HTML generado en:[/bold green] [underline]{html_file}[/underline]")
    console.print(f"[bold green]✅ Datos estructurados JSON generados en:[/bold green] [underline]{json_file}[/underline]")


def main():
    parser = argparse.ArgumentParser(description="Auditor Documental DIGEMID - Aporte Médico Perú S.A.C.")
    parser.add_argument("--path", type=str, help="Ruta a un archivo o carpeta de documentos a auditar")
    parser.add_argument("--test-suite", action="store_true", help="Audita la carpeta del caso base real de Catéteres")
    parser.add_argument("--all-bundles", action="store_true", help="Incluye los PDFs consolidados masivos de 70+ páginas")
    parser.add_argument("--html", type=str, help="Ruta del reporte HTML de salida")
    parser.add_argument("--json", type=str, help="Ruta del reporte JSON de salida")

    args = parser.parse_args()

    target_files = []

    if args.test_suite:
        if DEFAULT_TEST_DATA_DIR.exists():
            console.print(f"[cyan]Cargando banco de pruebas real desde: {DEFAULT_TEST_DATA_DIR}[/cyan]")
            all_files = list(DEFAULT_TEST_DATA_DIR.glob("*.pdf")) + list(DEFAULT_TEST_DATA_DIR.glob("*.docx"))
            # Si no se pasó --all, priorizar documentos individuales y omitir bundles consolidados redundantes
            for f in all_files:
                if not getattr(args, "all_bundles", False):
                    if "EXPEDIENTE" in f.name.upper() or "DOCUMENTOS TÉCNICOS" in f.name.upper():
                        continue
                target_files.append(f)
        else:
            console.print(f"[yellow]No se encontró el directorio base {DEFAULT_TEST_DATA_DIR}. Buscando en el workspace...[/yellow]")
    elif args.path:
        p = Path(args.path)
        if p.is_file():
            target_files.append(p)
        elif p.is_dir():
            for ext in ["*.pdf", "*.docx"]:
                target_files.extend(list(p.glob(ext)))
    else:
        # Por defecto, si existe la carpeta del caso real, usarla
        if DEFAULT_TEST_DATA_DIR.exists():
            console.print(f"[cyan]Ejecutando por defecto sobre el banco de pruebas real: {DEFAULT_TEST_DATA_DIR}[/cyan]")
            for ext in ["*.pdf", "*.docx"]:
                target_files.extend(list(DEFAULT_TEST_DATA_DIR.glob(ext)))
        else:
            console.print("[yellow]Indique una ruta con --path o active el banco con --test-suite[/yellow]")
            sys.exit(1)

    run_cli_audit(target_files, output_html=args.html, output_json=args.json)


if __name__ == "__main__":
    main()
