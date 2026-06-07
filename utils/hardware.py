import os
import logging
import subprocess
import json
from datetime import datetime, timedelta

# Configurar el logger primero para evitar errores de referencia
logger = logging.getLogger("EVA.hardware")

# Deshabilitar la inspección de código fuente de PyTorch antes de importarlo
os.environ['TORCH_DISABLE_INSPECT'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TORCH_DISABLE_SOURCE_CODE_EMBEDDING'] = '1'  # Evitar problemas con el código fuente

import psutil

# Importar PyTorch con configuración para evitar inspección de código fuente
try:
    import torch
    # Configurar PyTorch para evitar intentar acceder al código fuente
    torch._dynamo.config.suppress_errors = True
    torch._dynamo.config.verbose = False
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.enabled = True
    
    # Deshabilitar la generación de código JIT que podría necesitar el código fuente
    torch.jit._state.disable()
    
    # Configuración para evitar que PyTorch intente compilar modelos
    torch._dynamo.config.suppress_errors = True
    torch._dynamo.config.verbose = False
    
    # Deshabilitar la generación de código que podría necesitar el código fuente
    torch._C._jit_set_autocast_mode(False)
    torch._C._jit_set_profiling_mode(False)
    torch._C._jit_set_profiling_executor(False)
    
    # Configuración adicional para evitar problemas con el código fuente
    if hasattr(torch, '_dynamo'):
        torch._dynamo.config.cache_size_limit = 1
        torch._dynamo.config.accumulated_cache_size_limit = 1
        torch._dynamo.config.cache_size = 1
        
except Exception as e:
    logger.error(f"Error al configurar PyTorch: {str(e)}")
    # Si hay un error, deshabilitar PyTorch
    torch = None

logger = logging.getLogger("EVA")

# Cache configuration
HARDWARE_CACHE_FILE = "config/hardware_cache.json"
CACHE_VALIDITY_HOURS = 24  # Cache válido por 24 horas


def verificar_ffmpeg():
    """Verifica FFmpeg usando la ruta configurada en paths.json"""
    try:
        # Obtener ruta desde configuración (unified ConfigManager)
        from core.config_manager_unified import config_manager

        ffmpeg_path = config_manager.get("ffmpeg", "")
        ffmpeg_bin = os.path.join(ffmpeg_path, "ffmpeg.exe")

        # Ejecutar con ruta específica
        result = subprocess.run(
            [ffmpeg_bin, "-version"],  # Usar ruta configurada
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0] if result.stdout else ""
            gpu_support = (
                "cuda" in version_line.lower() or "nvenc" in version_line.lower()
            )
            return {"disponible": True, "version": version_line, "gpu": gpu_support}
        else:
            return {"disponible": False, "error": result.stderr, "gpu": False}
    except FileNotFoundError:
        return {
            "disponible": False,
            "error": "FFmpeg no encontrado en la ruta configurada",
            "gpu": False,
        }
    except Exception as e:
        return {"disponible": False, "error": str(e), "gpu": False}


def load_hardware_cache():
    """Carga el cache de hardware si existe y es válido"""
    try:
        if not os.path.exists(HARDWARE_CACHE_FILE):
            return None
            
        with open(HARDWARE_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verificar si el cache es válido (menos de 24 horas)
        cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
        if datetime.now() - cache_time < timedelta(hours=CACHE_VALIDITY_HOURS):
            logger.info(f"✅ Cache de hardware válido encontrado (creado: {cache_time.strftime('%Y-%m-%d %H:%M:%S')})")
            return cache_data.get('hardware_info')
        else:
            logger.info(f"⏰ Cache de hardware expirado (creado: {cache_time.strftime('%Y-%m-%d %H:%M:%S')})")
            return None
            
    except Exception as e:
        logger.warning(f"Error cargando cache de hardware: {str(e)}")
        return None

def save_hardware_cache(hardware_info):
    """Guarda la información de hardware en cache"""
    try:
        # Crear directorio config si no existe
        os.makedirs(os.path.dirname(HARDWARE_CACHE_FILE), exist_ok=True)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'hardware_info': hardware_info
        }
        
        with open(HARDWARE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"💾 Cache de hardware guardado: {HARDWARE_CACHE_FILE}")
        
    except Exception as e:
        logger.warning(f"Error guardando cache de hardware: {str(e)}")

def configure_hardware(config=None):
    """
    Detecta hardware del sistema para información de Ollama únicamente.
    Piper TTS siempre usa CPU - no requiere configuración GPU.
    """
    try:
        # OPTIMIZACIÓN: Intentar cargar desde cache primero
        cached_result = load_hardware_cache()
        if cached_result:
            logger.info("🚀 Usando información de hardware desde cache (ahorro de tiempo)")
            # Aplicar configuraciones manuales sobre el cache
            return _apply_manual_overrides(cached_result, config)
        
        logger.info("🔍 Cache no disponible, detectando hardware...")
        
        # Inicializar estructura de resultado con valores por defecto
        result = {
            "gpu_available": False,
            "gpu_name": "Ninguna detectada",
            "recommended_backend": "CPU",
            "cuda_available": False,
            "cuda_version": None,
            "cudnn_available": False,
            "cudnn_version": None,
            "gpu_memory_mb": 0,
            "cpu_cores": os.cpu_count() or 1,
            "system_memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
            "torch_available": torch is not None,
            "warnings": [],
            "ffmpeg": verificar_ffmpeg(),
        }

        # Verificar RAM mínima
        min_ram_gb = config.get("hardware_settings", {}).get("min_ram_gb", 4)
        ram_gb = psutil.virtual_memory().total / (1024**3)  # en GB
        if ram_gb < min_ram_gb:
            result["warnings"].append(
                f"RAM insuficiente: {ram_gb:.1f} GB < {min_ram_gb} GB mínimo"
            )

        # Intentar detectar GPU con logging detallado
        try:
            logger.info("🔍 Iniciando detección de hardware GPU/CUDA...")
            
            # Verificar si PyTorch detecta CUDA
            cuda_available = torch.cuda.is_available()
            logger.info(f"🔍 torch.cuda.is_available(): {cuda_available}")
            
            if cuda_available:
                device_count = torch.cuda.device_count()
                logger.info(f"🔍 Número de GPUs detectadas: {device_count}")
                
                if device_count > 0:
                    result["gpu_available"] = True
                    
                    # Obtener información detallada de la GPU
                    gpu_name = torch.cuda.get_device_name(0)
                    result["gpu_name"] = gpu_name
                    logger.info(f"🔍 GPU detectada: {gpu_name}")
                    
                    # Obtener propiedades de la GPU
                    gpu_props = torch.cuda.get_device_properties(0)
                    vram_bytes = gpu_props.total_memory
                    vram_gb = vram_bytes / (1024**3)
                    logger.info(f"🔍 VRAM disponible: {vram_gb:.2f} GB")
                    
                    # Verificar versión de CUDA
                    cuda_version = torch.version.cuda
                    logger.info(f"🔍 Versión CUDA: {cuda_version}")
                    
                    # Configuración de VRAM mínima (más permisiva)
                    min_vram_gb = config.get("hardware_settings", {}).get("min_vram_gb", 1.5)  # Reducido de 2 a 1.5
                    cpu_fallback = config.get("hardware_settings", {}).get("cpu_fallback", True)
                    
                    logger.info(f"🔍 VRAM mínima requerida: {min_vram_gb} GB")
                    
                    # Información GPU para Ollama (Piper TTS siempre usa CPU)
                    if vram_gb >= min_vram_gb:
                        result["recommended_backend"] = "GPU disponible para Ollama"
                        logger.info("✅ GPU disponible para aceleración de IA (Ollama)")
                    else:
                        result["recommended_backend"] = f"CPU recomendado (VRAM: {vram_gb:.1f} GB < {min_vram_gb} GB)"
                        result["warnings"].append(f"GPU con VRAM limitada: {vram_gb:.1f} GB - Ollama usará CPU")
                        logger.warning("⚠️ GPU disponible pero con VRAM limitada para IA")
                else:
                    logger.warning("⚠️ CUDA disponible pero no se detectaron GPUs")
                    result["warnings"].append("CUDA disponible pero no se detectaron GPUs")
            else:
                logger.warning("⚠️ CUDA no está disponible en este sistema")
                result["warnings"].append("CUDA no disponible en este sistema")
                
                # Intentar detectar por qué CUDA no está disponible
                try:
                    import subprocess
                    nvidia_smi = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
                    if nvidia_smi.returncode == 0:
                        logger.info("🔍 nvidia-smi funciona, pero PyTorch no detecta CUDA")
                        result["warnings"].append("GPU NVIDIA detectada pero PyTorch no puede usar CUDA")
                    else:
                        logger.info("🔍 nvidia-smi no disponible")
                except Exception as e:
                    logger.info(f"🔍 No se pudo ejecutar nvidia-smi: {e}")
                    
        except ImportError as e:
            logger.error(f"❌ Error de importación: {str(e)}")
            result["warnings"].append("PyTorch no está instalado correctamente")
        except Exception as e:
            logger.error(f"❌ Error detectando GPU: {str(e)}")
            result["warnings"].append(f"Error detectando GPU: {str(e)}")

        # Aplicar override manual si existe
        force_gpu = config.get("force_gpu", False)
        gpu_override = config.get("gpu_override", None)

        logger.info(f"🔍 Configuración manual - force_gpu: {force_gpu}, gpu_override: {gpu_override}")

        if force_gpu:
            logger.info("🔧 Forzando uso de GPU mediante configuración manual")
            result["warnings"].append("Forzado uso de GPU mediante configuración manual")
            if result["gpu_available"]:
                # tts_device removed - Piper TTS always uses CPU
                result["recommended_backend"] = "GPU disponible para Ollama (forzado)"
                logger.info("✅ GPU forzada exitosamente")
            else:
                result["warnings"].append("¡No se puede forzar GPU! No hay GPU disponible")
                logger.error("❌ No se puede forzar GPU - no hay GPU disponible")

        if gpu_override == "cuda":
            logger.info("🔧 Override manual a CUDA")
            if result["gpu_available"]:
                # tts_device removed - Piper TTS always uses CPU
                result["recommended_backend"] = "GPU disponible para Ollama (override manual)"
                result["warnings"].append("Forzado uso de GPU mediante override manual")
                logger.info("✅ Override a GPU exitoso")
            else:
                result["warnings"].append("Override a CUDA solicitado pero no hay GPU disponible")
                logger.error("❌ Override a CUDA fallido - no hay GPU disponible")
        elif gpu_override == "cpu":
            logger.info("🔧 Override manual a CPU")
            result["recommended_backend"] = "CPU (override manual)"
            result["warnings"].append("Forzado uso de CPU mediante override manual")
            logger.info("✅ Override a CPU exitoso")

        # Log final de configuración
        logger.info("🎯 Configuración final:")
        logger.info(f"   - GPU disponible: {result['gpu_available']}")
        logger.info(f"   - GPU nombre: {result['gpu_name']}")
        logger.info(f"   - Backend recomendado: {result['recommended_backend']}")
        logger.info("   - TTS: Piper (CPU-only)")
        if result["warnings"]:
            logger.info(f"   - Advertencias: {len(result['warnings'])}")
            for warning in result["warnings"]:
                logger.info(f"     • {warning}")

        # OPTIMIZACIÓN: Guardar resultado en cache para próximas ejecuciones
        save_hardware_cache(result)
        
        return result
    except Exception as e:
        logger.error(f"Error en configure_hardware: {str(e)}")
        return {
            "gpu_available": False,
            "gpu_name": "Error",
            "recommended_backend": "CPU (por error)",
            # tts_device removed - Piper TTS always uses CPU
            "warnings": [f"Error crítico: {str(e)}"],
            "ffmpeg": verificar_ffmpeg(),
        }


def get_ollama_system_info():
    """
    Información del sistema simplificada solo para Ollama.
    No configura TTS - Piper siempre usa CPU optimizado.
    
    Returns:
        dict: Información básica del sistema para Ollama, incluyendo siempre 'ollama_acceleration'
    """
    try:
        import platform
        
        # Obtener información básica del sistema
        system_info = {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_cores": os.cpu_count() or 1,
            "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
            "gpu_available": False,
            "gpu_name": "Ninguna detectada",
            "recommended_backend": "CPU",
            "warnings": [],
            "ollama_acceleration": "Aceleración por hardware no disponible"  # Valor por defecto
        }
        
        # Intentar detectar GPU si está disponible
        try:
            if torch is not None and hasattr(torch, 'cuda') and torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                system_info.update({
                    "gpu_available": True,
                    "gpu_name": gpu_name,
                    "recommended_backend": "CUDA",
                    "ollama_acceleration": f"GPU detectada: {gpu_name} (CUDA)"
                })
            else:
                # Intentar detectar GPU sin usar PyTorch
                try:
                    import subprocess
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        gpu_name = result.stdout.strip()
                        system_info.update({
                            "gpu_available": True,
                            "gpu_name": gpu_name,
                            "recommended_backend": "CUDA",
                            "ollama_acceleration": f"GPU detectada: {gpu_name} (CUDA)"
                        })
                except Exception:
                    pass
        except Exception as e:
            system_info["warnings"].append(f"Error detectando GPU: {str(e)}")
        
        # Asegurar que el mensaje de aceleración sea consistente
        if system_info["gpu_available"]:
            system_info["ollama_acceleration"] = f"GPU detectada: {system_info['gpu_name']} ({system_info['recommended_backend']})"
        else:
            system_info["ollama_acceleration"] = "Usando aceleración por CPU"
        
        return system_info
        
    except Exception as e:
        logger.error(f"Error en get_ollama_system_info: {str(e)}")
        return {
            "system": platform.system() if 'platform' in globals() else "Desconocido",
            "machine": platform.machine() if 'platform' in globals() else "Desconocido",
            "processor": platform.processor() if 'platform' in globals() else "Desconocido",
            "cpu_cores": os.cpu_count() or 1,
            "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1) if 'psutil' in globals() else 0,
            "gpu_available": False,
            "gpu_name": "Error al detectar",
            "recommended_backend": "CPU",
            "warnings": [f"Error al detectar hardware: {str(e)}"],
            "system_ready": False,
            "error": str(e)
        }


def _apply_manual_overrides(result, config):
    """Aplica configuraciones manuales sobre el resultado cacheado"""
    if not config:
        return result
    
    # Aplicar override manual si existe
    force_gpu = config.get("force_gpu", False)
    gpu_override = config.get("gpu_override", None)

    logger.info(f"🔍 Aplicando configuración manual sobre cache - force_gpu: {force_gpu}, gpu_override: {gpu_override}")

    if force_gpu:
        logger.info("🔧 Forzando uso de GPU mediante configuración manual")
        if "Forzado uso de GPU mediante configuración manual" not in result["warnings"]:
            result["warnings"].append("Forzado uso de GPU mediante configuración manual")
        if result["gpu_available"]:
            # tts_device removed - Piper TTS always uses CPU
            result["recommended_backend"] = "GPU disponible para Ollama (forzado)"
            logger.info("✅ GPU forzada exitosamente")
        else:
            if "¡No se puede forzar GPU! No hay GPU disponible" not in result["warnings"]:
                result["warnings"].append("¡No se puede forzar GPU! No hay GPU disponible")
            logger.error("❌ No se puede forzar GPU - no hay GPU disponible")

    if gpu_override == "cuda":
        logger.info("🔧 Override manual a CUDA")
        if result["gpu_available"]:
            # tts_device removed - Piper TTS always uses CPU
            result["recommended_backend"] = "GPU disponible para Ollama (override manual)"
            if "Forzado uso de GPU mediante override manual" not in result["warnings"]:
                result["warnings"].append("Forzado uso de GPU mediante override manual")
            logger.info("✅ Override a GPU exitoso")
        else:
            if "Override a CUDA solicitado pero no hay GPU disponible" not in result["warnings"]:
                result["warnings"].append("Override a CUDA solicitado pero no hay GPU disponible")
            logger.error("❌ Override a CUDA fallido - no hay GPU disponible")
    elif gpu_override == "cpu":
        logger.info("🔧 Override manual a CPU")
        result["recommended_backend"] = "CPU (override manual)"
        if "Forzado uso de CPU mediante override manual" not in result["warnings"]:
            result["warnings"].append("Forzado uso de CPU mediante override manual")
        logger.info("✅ Override a CPU exitoso")

    # Log final de configuración
    logger.info("🎯 Configuración final (con cache):")
    logger.info(f"   - GPU disponible: {result['gpu_available']}")
    logger.info(f"   - GPU nombre: {result['gpu_name']}")
    logger.info(f"   - Backend recomendado: {result['recommended_backend']}")
    # TTS device log removed - Piper TTS always uses CPU
    if result["warnings"]:
        logger.info(f"   - Advertencias: {len(result['warnings'])}")
        for warning in result["warnings"]:
            logger.info(f"     • {warning}")

    return result
