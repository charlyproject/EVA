import logging
import os
import re
import threading

logger = logging.getLogger("EVA")

# =============================================================================
# CACHÉ DE CARPETA ACTIVA
# =============================================================================
# Arquitectura de dos fases (resuelve los 3 bugs del EXE PySide6):
#
#   FASE ESCRITURA  _run_folder_cache_update()  ← hilo daemon, PowerShell
#   FASE LECTURA    get_working_folder()         ← hilo Qt, solo lee dict
#
# Por qué PowerShell y no COM directo:
#   PySide6 compilado con PyInstaller inicializa COM en modo MTA; win32com
#   lo necesita en STA. El conflicto hace que Shell.Application devuelva
#   rutas erróneas o falle silenciosamente. PowerShell corre en su propio
#   proceso con contexto COM limpio.
#
# Por qué NO depender solo de GetForegroundWindow():
#   Cuando el usuario habla con EVA, la ventana activa ES EVA, no el
#   Explorador. La prioridad 1 busca coincidencia exacta de HWND; si no la
#   hay, la prioridad 2 recorre TODAS las ventanas del Explorador y devuelve
#   la más reciente que no sea ruta de sistema, evitando "ProgramData" etc.
# =============================================================================

_folder_cache = {
    'path': None,       # str | None  — última ruta detectada válida
    'updating': False,  # bool        — semáforo para evitar doble refresh
}
_cache_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Script PowerShell embebido (v2)
# Cambios vs versión anterior:
#   ① Document.Folder.Self.Path en lugar de LocationURL+unescaping
#      (más robusto con rutas Unicode/espacios)
#   ② Fuerza HWND a [int64] en la comparación (evita mismatch IntPtr/Int32)
#   ③ Fallback filtra explícitamente rutas de sistema (ProgramData, Windows…)
#   ④ Normaliza raíces de unidad: "D:" → "D:\"
# ---------------------------------------------------------------------------
_PS_SCRIPT = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinHelper {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
}
"@

$fgHwnd = [WinHelper]::GetForegroundWindow().ToInt64()
$shell  = New-Object -ComObject Shell.Application

function Normalize-Path($p) {
    if ($p -and $p.Length -eq 2 -and $p[1] -eq ':') { return $p + '\' }
    return $p
}

# PRIORIDAD 1: ventana del Explorador que coincide con el HWND activo
foreach ($w in $shell.Windows()) {
    try {
        if ([int64]$w.HWND -eq $fgHwnd) {
            $path = Normalize-Path $w.Document.Folder.Self.Path
            if ($path -and (Test-Path -LiteralPath $path -PathType Container)) {
                Write-Output $path
                exit 0
            }
        }
    } catch {}
}

# PRIORIDAD 2 (fallback): cualquier ventana Explorer que no sea ruta de sistema
$systemRoots = @(
    $env:SystemRoot,
    $env:ProgramFiles,
    ${env:ProgramFiles(x86)},
    $env:ProgramData,
    (Join-Path $env:SystemRoot 'System32'),
    (Join-Path $env:SystemRoot 'SysWOW64')
)

foreach ($w in $shell.Windows()) {
    try {
        $path = Normalize-Path $w.Document.Folder.Self.Path
        if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Container)) { continue }
        $isSystem = $false
        foreach ($root in $systemRoots) {
            if ($root -and $path.ToLower().StartsWith($root.ToLower())) {
                $isSystem = $true
                break
            }
        }
        if (-not $isSystem) {
            Write-Output $path
            exit 0
        }
    } catch {}
}
exit 0
"""


def refresh_folder_cache(blocking=True):
    """
    Actualiza la caché de carpeta activa lanzando PowerShell en un subproceso.

    Args:
        blocking (bool):
            True  -> espera a que termine (refresh inicial o manual).
            False -> hilo daemon, regresa de inmediato (uso normal del timer Qt).
                     El resultado estará listo en ~400ms, mucho antes del
                     próximo tick del timer a los 5s.
    """
    with _cache_lock:
        if _folder_cache['updating']:
            return  # Ya hay un refresh en curso, ignorar petición duplicada
        _folder_cache['updating'] = True

    if blocking:
        try:
            _run_folder_cache_update()
        finally:
            with _cache_lock:
                _folder_cache['updating'] = False
    else:
        def _worker():
            try:
                _run_folder_cache_update()
            finally:
                with _cache_lock:
                    _folder_cache['updating'] = False

        t = threading.Thread(target=_worker, daemon=True, name="FolderCacheUpdater")
        t.start()


def _run_folder_cache_update():
    """Ejecuta el script PowerShell y guarda el resultado en _folder_cache."""
    import subprocess

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-Command", _PS_SCRIPT,
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )

        raw = result.stdout.strip()
        if raw and os.path.isdir(raw):
            with _cache_lock:
                _folder_cache['path'] = raw
            logger.debug(f"✅ Caché actualizada (PowerShell): {raw}")
        else:
            stderr = result.stderr.strip()
            if stderr:
                logger.debug(f"PowerShell stderr: {stderr[:200]}")
            logger.debug("PowerShell: sin carpeta válida del Explorador en primer plano")

    except subprocess.TimeoutExpired:
        logger.warning("⚠️ PowerShell tardó más de 5s detectando carpeta")
    except FileNotFoundError:
        logger.error("❌ PowerShell no encontrado — detección de carpeta deshabilitada")
    except Exception as e:
        logger.error(f"❌ Error en _run_folder_cache_update: {e}")


# =============================================================================
# API PÚBLICA
# =============================================================================

def get_working_folder():
    """
    Devuelve la carpeta de trabajo activa.

    Prioridades:
      1. Caché PowerShell (actualizada en background cada 5s)
      2. Última carpeta guardada en disco (~/.eva_last_folder.txt)
      3. Carpeta home del usuario (nunca devuelve None)

    IMPORTANTE: NO llama a COM, NO lanza subprocesos, NO bloquea.
    Es completamente segura para llamar desde el hilo principal de Qt.
    """
    # 1. Caché (ruta más fresca, actualizada por el daemon PowerShell)
    with _cache_lock:
        cached = _folder_cache.get('path')
    if cached and os.path.isdir(cached):
        return cached

    # 2. Última carpeta guardada en disco
    saved = load_last_folder_path()
    if saved and os.path.isdir(saved):
        logger.debug(f"📁 Caché vacía, usando última carpeta guardada: {saved}")
        return saved

    # 3. Fallback al home del usuario
    home = os.path.expanduser("~")
    logger.debug(f"📁 Sin carpeta previa, usando home: {home}")
    return home


# =============================================================================
# FUNCIONES DE PERSISTENCIA
# =============================================================================

def load_last_folder_path():
    last_folder_path_file = os.path.expanduser("~/.eva_last_folder.txt")
    try:
        if os.path.exists(last_folder_path_file):
            with open(last_folder_path_file, "r", encoding="utf-8") as f:
                path = f.read().strip()
                if os.path.isdir(path):
                    logger.info(f"Última carpeta cargada: {path}")
                    return path
                else:
                    logger.warning(f"Ruta guardada no válida: {path}")
    except Exception as e:
        logger.error(f"Error cargando última ruta: {str(e)}")
    return None


def save_last_folder_path(path):
    last_folder_path_file = os.path.expanduser("~/.eva_last_folder.txt")
    try:
        if path and os.path.isdir(path):
            with open(last_folder_path_file, "w", encoding="utf-8") as f:
                f.write(path)
            logger.info(f"Última carpeta guardada: {path}")
    except Exception as error:
        logger.error(f"Error guardando última ruta: {str(error)}")


# =============================================================================
# STUBS DE COMPATIBILIDAD
# Mantienen la firma original para que otros módulos (windows_commands.py,
# processor.py, etc.) no lancen ImportError. El EXE ya no los necesita para
# el flujo principal de detección de carpeta.
# =============================================================================

def auto_update_working_folder():
    """
    Compatibilidad: actualiza la caché (bloqueando) y guarda la carpeta.

    Returns:
        bool: True si se detectó una carpeta nueva respecto a la anterior.
    """
    try:
        with _cache_lock:
            old_path = _folder_cache.get('path')

        refresh_folder_cache(blocking=True)

        with _cache_lock:
            new_path = _folder_cache.get('path')

        if new_path and new_path != old_path:
            logger.info(f"🔄 auto_update_working_folder: {old_path} → {new_path}")
            save_last_folder_path(new_path)
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Error en auto_update_working_folder: {e}")
        return False


def get_active_explorer_folder():
    """
    Compatibilidad: devuelve la carpeta cacheada si existe.
    En el EXE la detección real la hace PowerShell vía refresh_folder_cache.
    """
    with _cache_lock:
        cached = _folder_cache.get('path')
    return cached if (cached and os.path.isdir(cached)) else None


def get_explorer_path_for_active_window(active_window=None):
    """Stub — delega a la caché PowerShell."""
    return get_active_explorer_folder()


def _get_explorer_path_fallback(windows=None):
    """Stub de compatibilidad."""
    return None


def _get_folder_via_clipboard():
    """Stub de compatibilidad — ya no se usa en el flujo principal del EXE."""
    return None


def _is_explorer_window_by_class(window):
    try:
        import win32gui
        class_name = win32gui.GetClassName(window._hWnd)
        return class_name in ("CabinetWClass", "ExploreWClass")
    except Exception:
        return False


def _is_explorer_window_by_title(window_title):
    try:
        t = window_title.lower().strip()
        if any(k == t for k in ["file explorer", "explorador de archivos", "windows explorer"]):
            return True
        return bool(re.match(r"^[a-z]:\\", t))
    except Exception:
        return False


def _contains_valid_windows_path(title):
    try:
        return any(
            os.path.exists(m.strip())
            for m in re.findall(r'[A-Z]:\\[^<>:"|?*]*', title)
        )
    except Exception:
        return False


def extract_folder_path_from_title(window_title):
    """
    Extrae la ruta de carpeta del título de una ventana del Explorador.
    Mantenida para compatibilidad; el EXE ya no la usa para el flujo principal.
    """
    try:
        title = window_title.strip()

        # Regex — permite espacios, excluye caracteres ilegales de Windows
        for pattern in [r'([A-Za-z]:\\[^<>:"|?*]+)', r'([A-Za-z]:/[^<>:"|?*]+)']:
            for m in re.findall(pattern, title):
                clean = m.strip().rstrip('\\/')
                if os.path.isdir(clean):
                    return clean

        # Separadores comunes
        for sep in [' - ', ' | ', ': ', ' – ', ' — ']:
            if sep in title:
                for part in reversed(title.split(sep)):
                    p = part.strip()
                    if p and os.path.isdir(p):
                        return p

        # Título completo como ruta
        if os.path.isdir(title):
            return title

        # Carpetas conocidas del sistema
        home = os.path.expanduser("~")
        known = {
            "documentos": os.path.join(home, "Documents"),
            "documents":  os.path.join(home, "Documents"),
            "descargas":  os.path.join(home, "Downloads"),
            "downloads":  os.path.join(home, "Downloads"),
            "escritorio": os.path.join(home, "Desktop"),
            "desktop":    os.path.join(home, "Desktop"),
            "imágenes":   os.path.join(home, "Pictures"),
            "pictures":   os.path.join(home, "Pictures"),
            "música":     os.path.join(home, "Music"),
            "music":      os.path.join(home, "Music"),
            "vídeos":     os.path.join(home, "Videos"),
            "videos":     os.path.join(home, "Videos"),
        }
        for key, path in known.items():
            if key in title.lower() and os.path.isdir(path):
                return path

        return None
    except Exception as e:
        logger.error(f"Error extrayendo ruta del título '{window_title}': {e}")
        return None


# =============================================================================
# DIAGNÓSTICO
# =============================================================================

def test_folder_detection():
    """
    Diagnóstico rápido del sistema de detección.
    Llama a esto desde el REPL o un comando de voz para depurar.

    Returns:
        dict: estado del sistema de caché y PowerShell.
    """
    result = {
        "powershell_available": False,
        "cache_path": None,
        "cache_updating": False,
        "last_saved": load_last_folder_path(),
        "get_working_folder_result": None,
    }

    # Verificar PowerShell
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", "Write-Output ok"],
            capture_output=True, text=True, timeout=3,
            creationflags=0x08000000
        )
        result["powershell_available"] = r.stdout.strip() == "ok"
    except Exception:
        pass

    with _cache_lock:
        result["cache_path"]     = _folder_cache.get('path')
        result["cache_updating"] = _folder_cache.get('updating', False)

    result["get_working_folder_result"] = get_working_folder()
    logger.info(f"🔍 test_folder_detection: {result}")
    return result
