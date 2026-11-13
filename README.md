# SOFTWARE AUDITOR DOCUMENTAL PARA REGISTROS SANITARIOS DIGEMID (PERÚ)
**Sistema Pericial Automatizado para Dispositivos Médicos Clase III**  
*Titular Caso Base:* **APORTE MÉDICO PERÚ S.A.C.** (RUC `20610321268`)  
*Fabricante:* **ACE Medical Devices Pvt. Ltd.** (Pune, India)  
*Producto:* **Catéteres Ureterales (Doble J / Stent Ureteral y Set)**

---

## 1. OBJETIVO DEL SISTEMA
Herramienta pericial automatizada desarrollada en Python (con interfaz web interactiva en Streamlit y CLI en Rich) diseñada para auditar lotes de documentos técnicos y legales (PDFs digitales, PDFs escaneados, imágenes y DOCX). 

El sistema ejecuta una auditoría profunda basada en un **motor de reglas regulatorias, lingüísticas y notación científica**, complementado con **OCR local de alto rendimiento (RapidOCR)** y un **Motor de Concordancia Cruzada (Cross-Document Consistency Engine)** para prevenir denegatorias de oficio, observaciones reiterativas y pérdida de tasas TUPA ante DIGEMID (Perú: D.S. 016-2011-SA, D.S. 003-2020-SA, D.S. 014-2011-SA, Ley N° 29459).

---

## 2. CASO BASE Y BANCO DE PRUEBAS REAL
- **Titular Solicitante:** APORTE MÉDICO PERÚ S.A.C.
- **Fabricante de Origen:** ACE Medical Devices Pvt. Ltd. (Planta 401A, Gera 77, Kalyani Nagar, Pune 411006, India).
- **Dispositivo Médico:** Catéteres Ureterales Doble J / Stent Ureteral y Set (Clase III: Dispositivo invasivo de uso quirúrgico/implante prolongado).
- **Antecedentes Reales de Rechazo:**
  - **Exp. 25039778 (Julio 2025):** Desistido por observaciones críticas no subsanadas (sello consular borroso, calibres discordantes).
  - **Exp. 25157794 (Mayo 2026):** Denegado mediante **R.D. N° 4453-2026**, respaldada en la **Notificación Oficial DIGEMID N° 2026068505** con más de 25 observaciones técnicas de fondo.

---

## 3. CATÁLOGO DE ERRORES Y CASOS DE PRUEBA CUBIERTOS

El software audita automáticamente los 3 grandes catálogos de defectos documentales:

### A. Errores Tipográficos, Notación Científica y Traducción Absurda
1. **Exponentes Microbiológicos:**
   - Detección de `SAL of 10^6` o `SAL 106` (exponente positivo = 1 millón de unidades contaminadas) en vez de `SAL 10^-6` (1 en un millón) en conclusiones de esterilización por Óxido de Etileno (EO).
   - Detección de `106` sin superíndice para el Indicador Biológico (*Bacillus atrophaeus*).
2. **Normas ISO Mal Digitadas y Derogadas:**
   - Detección de la norma inexistente `ISO 111737` (error por `ISO 11737-1`).
   - Alerta de normas derogadas: `ISO 14971:2012` (requiere 2019), `MDD 93/42/EEC` (requiere EU MDR 2017/745), `EN 980:2008` (derogada por ISO 15223-1), `ISO 13485:2003`.
3. **Errores de OCR y Lectura Corrupta:**
   - `ZSO 9001:2015` en vez de `ISO 9001:2015`.
   - Palabras truncadas en tablas: `"ifi"` por *orifices*, `"taction"` por *traction*.
4. **Traducciones Automáticas Absurdas / No Médicas:**
   - *"no debe mantenerse mora"* (por *do not delay* o retención).
   - *"El doble coleta"* (traducción literal de *Double Pigtail* por Doble J).
   - *"de la vegiga"* (falta ortográfica por *vejiga*).
   - *"el gato No."* o *"el gato Nº"* (traducción errónea de *Cat. No.* / Número de Catálogo).
   - *"por el tubo"* (traducción literal de *Per tube*).
   - *"pelar las juntas"*, *"sacudidas de calor"*.
5. **Mezclas de Idiomas e Inconsistencias Léxicas:**
   - Tildes en inglés: *"blíster"* dentro de párrafos redactados en inglés; *"identificactión"*.
   - Confusión de materiales: *"Silicon stents"* (silicio en lugar de silicona / *silicone*).
   - Países mal escritos o cruzados: *"Columbia"* en vez de Colombia; cartas para Colombia presentadas en Perú.

### B. Fallas de Orden, Estructura, Páginas e Integridad Visual
1. **Páginas Invertidas / Rotadas / Espejadas:**
   - Detección automática de orientación (páginas rotadas 180° de cabeza o 90°/270° apaisadas).
2. **Documentos sin Firmas ni Sellos Obligatorios:**
   - Reportes regulatorios (Evaluación Clínica CER, Verificación de Diseño DVR, Esterilización) sin firmas de autor, revisor o médico especialista.
   - Recortes de imagen de firma sin fecha, sin nombres legibles o sin sello corporativo.
3. **Celdas y Secciones en Blanco:**
   - Checklists (GSPR) con columnas de cumplimiento vacías.
   - Tablas que rellenan todas las variables exclusivamente con *"Complies"* sin fechas de corrida, números de lote, concentración de gas EO ni equipos reales.
   - Campos en blanco críticos en manuales IFU: `"Artwork code with Rev. No."`, placeholders de borrador (*"Falta agregar breve descripción"*).
4. **Anexos y Reportes Prometidos pero Ausentes:**
   - Cita en texto: *"Annexure 3 CV is attached"*, *"PMS Report attached"*, *"approved NABL accredited laboratory under ISO 10993-7"*, verificando si el anexo existe en el documento o paquete.
5. **Numeración Desordenada de Secciones:**
   - Saltos erráticos de numeración (ej. pasar de sección 1 a sección 5 omitiendo correlativos).

### C. Inconsistencias Cruzadas entre Documentos (Cross-Document Clashes)
1. **Contradicciones Internas en el Mismo Archivo:**
   - Declarar 2 semiciclos de esterilización en la pág. 2 y 3 semiciclos en la pág. 3 y Tabla 1.
   - En GSPR: Marcar `NO` a fecha de expiración en rótulo y en la página siguiente marcar `YES`.
2. **Descalce de Medidas y Modelos (Matriz Dimensional):**
   - CLV declara `2–12 Fr / 6–32 cm`.
   - DVR y CER declaran `3–8 Fr / 8–30 cm`.
   - Infiltración de otro producto: especificaciones de `70–90 cm` correspondientes a *Ureteral Catheter* simple.
3. **Descalce de Vida Útil (Shelf Life):**
   - Verificación de Diseño (DVR) declara `3 años`.
   - Lotes de laboratorio (Accuprec) prueban `5 años` (`09/2021 a 08/2026`).
   - Borrador provisional llegó a declarar `1 día`.
4. **Descalce de Tiempo de Permanencia Clínica (Indwelling Time):**
   - Declaraciones contradictorias: `< 25 días` vs `30–90 días` vs `> 30 días / Implante permanente` vs `6 meses`.
5. **Descalce de Componentes del Set:**
   - CER declara que el dispositivo *"doesn't contain any components"*, mientras que el título, Carta del Fabricante y rótulos declaran un *SET* con 5 componentes (catéter, guía PTFE, empujador, clamp, hilo).
6. **Contaminación por Copia Clínica (Copy-Paste de Otros Dispositivos):**
   - Drenaje quirúrgico: *"Similar device design: Bottle/grenade type"*.
   - Gastroenterología: *"Gastro-enterological Endoscopic procedures"*.
   - Abrazadera umbilical: *"Umbilical cord clamp"* en set urológico.
   - Catéter balón Foley: Tablas de balón `3–50 ml` y calibres `8Fr–28Fr`.

---

## 4. ESTRUCTURA Y ARQUITECTURA DEL PROYECTO

```
programa aporte medico/
├── app.py                      # Interfaz Web interactiva con Streamlit
├── cli.py                      # Interfaz de línea de comandos en Rich
├── config.py                   # Matriz maestra, datos del caso base y referencias legales
├── core/
│   ├── __init__.py
│   ├── auditor.py              # Orquestador central de auditoría
│   ├── ingestion.py            # Motor de ingesta (PyMuPDF + RapidOCR + DOCX + Caché a disco)
│   ├── visual_inspector.py     # Inspector visual (páginas rotadas, firmas y sellos)
│   ├── models.py               # Modelos Pydantic/Dataclass (Finding, Severity, Category, etc.)
│   ├── report_generator.py     # Generador de reportes en HTML interactivo, JSON y Markdown
│   └── rules/
│       ├── __init__.py
│       ├── scientific_typos.py # Reglas del Catálogo A (Notación científica, ISO, traducción)
│       ├── structure.py        # Reglas del Catálogo B (Estructura, vacíos, anexos)
│       ├── cross_clash.py      # Reglas del Catálogo C (Matriz dimensional y contradicciones)
│       └── digemid_legal.py    # Reglas específicas de DIGEMID (Arts. 126°, 130°, D.S. 003)
├── tests/
│   ├── __init__.py
│   └── test_audit_engine.py    # Suite de pruebas automatizadas (15 tests unitarios e integrales)
├── reports/                    # Carpeta de salida para reportes generados
└── .ocr_cache/                 # Caché de disco para lecturas OCR ultra-rápidas
```

---

## 5. GUÍA DE INSTALACIÓN Y EJECUCIÓN

### Requisitos Previos
- Python 3.12+
- `uv` (administrador rápido de paquetes Python)

### Instalación de Dependencias
```powershell
uv pip install --system pymupdf python-docx rapidocr-onnxruntime streamlit rich pandas pytest
```

### Ejecutar las Pruebas Automatizadas
```powershell
python -m pytest tests/test_audit_engine.py -v
```
*Resultado: 15/15 tests aprobados.*

### Ejecutar la Aplicación Web (Streamlit)
```powershell
streamlit run app.py
```
Abre automáticamente el navegador en `http://localhost:8501`. Permite:
- Auditar el **Banco de Pruebas Real de Catéteres** con un solo clic.
- Cargar lotes personalizados de archivos PDF o DOCX vía Drag & Drop.
- Explorar los hallazgos filtrados por **Fallas Fatales**, **Observaciones Críticas** y **Errores Menores**.
- Visualizar la **Matriz Dimensional Cruzada** interactiva.
- Descargar el **Reporte HTML Interactivo**, el archivo **JSON estructurado** y el **Dictamen Markdown**.

### Ejecutar desde Línea de Comandos (CLI)
Auditar el caso base real:
```powershell
python cli.py --test-suite
```
Auditar un archivo o carpeta personalizada:
```powershell
python cli.py --path "C:\ruta\a\documentos" --html "reportes/mi_auditoria.html"
```
