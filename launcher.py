"""
Lanzador Inteligente para el Auditor Forense Documental DIGEMID.
- Maneja colisiones de puerto 8501 y procesos huérfanos.
- Abre automáticamente el navegador predeterminado en http://localhost:8501.
- Muestra mensajes de error nativos de Windows si ocurre algún problema.
- Habilita la conectividad en red local para que otros miembros del equipo puedan ingresar.
"""

import sys
import os
import time
import socket
import subprocess
import webbrowser
import urllib.request
import ctypes
from pathlib import Path

PORT = 8501
URL = f"http://localhost:{PORT}"
SCRIPT_DIR = Path(__file__).parent.resolve()
APP_FILE = SCRIPT_DIR / "app.py"


def show_error_box(message: str, title: str = "Auditor DIGEMID"):
    """Muestra una ventana de diálogo nativa de Windows con el error."""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)


def show_info_box(message: str, title: str = "Auditor DIGEMID"):
    """Muestra una ventana de diálogo informativa nativa de Windows."""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)


def is_port_bound(port: int) -> bool:
    """Verificación ultrarrápida (0.001s) de disponibilidad del puerto TCP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False


def is_server_running(url: str, timeout: float = 0.3) -> bool:
    """Verifica si el servidor Streamlit ya está respondiendo peticiones HTTP."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AuditorLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 304)
    except Exception:
        return False


def kill_process_on_port(port: int):
    """Termina de inmediato cualquier proceso colgado que esté ocupando el puerto."""
    try:
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
        for line in output.strip().splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.3)
    except Exception:
        pass


def main():
    os.chdir(SCRIPT_DIR)

    # 1. Verificación instantánea: Si ya está en ejecución activa, abrir navegador en 0.05s y salir
    if is_port_bound(PORT):
        if is_server_running(URL, timeout=0.4):
            try:
                webbrowser.open(URL)
            except Exception:
                subprocess.call(f'start {URL}', shell=True)
            sys.exit(0)
        else:
            # Puerto ocupado por proceso muerto/colgado: liberarlo
            kill_process_on_port(PORT)

    # 2. Asegurar que nunca solicite email en consola interactiva (evita bloqueos silenciosos)
    user_cred = Path.home() / ".streamlit" / "credentials.toml"
    if not user_cred.exists():
        try:
            user_cred.parent.mkdir(parents=True, exist_ok=True)
            user_cred.write_text('[general]\nemail = ""\n', encoding="utf-8")
        except Exception:
            pass

    local_cred = SCRIPT_DIR / ".streamlit" / "credentials.toml"
    if not local_cred.exists():
        try:
            local_cred.parent.mkdir(parents=True, exist_ok=True)
            local_cred.write_text('[general]\nemail = ""\n', encoding="utf-8")
        except Exception:
            pass

    # 3. Lanzar Streamlit optimizado
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        str(APP_FILE),
        f"--server.port={PORT}",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--browser.serverAddress=localhost",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
    except Exception as e:
        show_error_box(f"No se pudo iniciar el proceso de Python/Streamlit:\n\n{e}")
        sys.exit(1)

    # 4. Sondeo ultrarrápido (cada 150ms): en cuanto el puerto responda, abrir navegador
    opened = False
    for _ in range(50): # Esperar hasta 7.5 segundos con chequeo rápido
        time.sleep(0.15)
        if is_port_bound(PORT):
            try:
                webbrowser.open(URL)
            except Exception:
                subprocess.call(f'start {URL}', shell=True)
            opened = True
            break
        if proc.poll() is not None:
            show_error_box(f"El Auditor finalizó inesperadamente con código {proc.returncode}.\nVerifique que las dependencias estén instaladas.")
            sys.exit(1)

    if not opened:
        try:
            webbrowser.open(URL)
        except Exception:
            subprocess.call(f'start {URL}', shell=True)

    # Mantener el proceso activo en segundo plano
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
