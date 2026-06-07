import os
import sys
import shutil
import subprocess
import logging

def setup_logging(app_dir):
    log_dir = os.path.join(os.getenv('APPDATA'), 'EVA', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'install.log')
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger()

def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    logger = setup_logging(app_dir)
    logger.info("=" * 50)
    logger.info("Iniciando post-instalacion de EVA Assistant")
    logger.info(f"Directorio de instalacion: {app_dir}")
    
    try:
        # Paso 1: Copiar contenido de _internal a la raiz
        internal_dir = os.path.join(app_dir, '_internal')
        if os.path.exists(internal_dir):
            logger.info("Copiando contenido de _internal...")
            
            # Lista de elementos a copiar (prioritarios)
            items_to_copy = [
                'models', 'piper', 'ffmpeg', 'resources',
                'config', 'commands', 'core', 'ui', 'utils', 'voice', 'help_system', 'hooks'
            ]
            
            for item in items_to_copy:
                src = os.path.join(internal_dir, item)
                dst = os.path.join(app_dir, item)
                
                if os.path.exists(src):
                    # Eliminar destino si existe
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)
                    
                    # Copiar elemento
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                        logger.info(f"Copiada carpeta: {item}")
                    else:
                        shutil.copy2(src, dst)
                        logger.info(f"Copiado archivo: {item}")
                else:
                    logger.warning(f"Elemento no encontrado en _internal: {item}")
        
        # Paso 2: Verificacion de recursos criticos
        logger.info("Verificando recursos criticos...")
        critical_items = [
            "models",
            "piper",
            "ffmpeg/bin/ffmpeg.exe",
            "resources/icon.ico"
        ]
        
        missing_items = []
        for item in critical_items:
            item_path = os.path.join(app_dir, item)
            if not os.path.exists(item_path):
                missing_items.append(item_path)
                logger.error(f"Recurso faltante: {item_path}")
        
        if missing_items:
            logger.error("¡ERROR! Recursos criticos faltantes despues de la copia")
            for item in missing_items:
                logger.error(f" - {item}")
            # Intentar copia redundante si faltan elementos criticos
            if os.name == 'nt' and os.path.exists(internal_dir):
                logger.info("Intentando copia redundante con Robocopy...")
                robocopy_cmd = [
                    "robocopy",
                    internal_dir,
                    app_dir,
                    "/E",    # Copiar subdirectorios incluyendo vacios
                    "/COPYALL",  # Copiar toda la informacion de archivos
                    "/R:3",  # 3 reintentos
                    "/W:1",  # Esperar 1 segundo entre reintentos
                    "/NP",   # Sin progreso (para evitar sobrecarga)
                    "/LOG:robocopy.log" 
                ]
                result = subprocess.run(robocopy_cmd, capture_output=True, text=True)
                if result.stdout:
                    logger.info(f"Robocopy stdout:\n{result.stdout}")
                if result.stderr:
                    logger.error(f"Robocopy stderr:\n{result.stderr}")
                logger.info(f"Robocopy retorno: {result.returncode}")
        
        # Paso 3: Instalar dependencias
        logger.info("Instalando dependencias Python...")
        requirements = os.path.join(app_dir, 'requirements.txt')
        
        if os.path.exists(requirements):
            # Comando mejorado para instalacion
            cmd = [
                sys.executable, 
                "-m", "pip", "install", 
                "--disable-pip-version-check",
                "--no-warn-script-location",
                "-r", requirements
            ]
            
            result = subprocess.run(
                cmd,
                cwd=app_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                logger.info(f"Salida de pip:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Errores de pip:\n{result.stderr}")
            if result.returncode != 0:
                logger.error(f"pip fallo con codigo: {result.returncode}")
        else:
            logger.error(f"Archivo requirements.txt no encontrado en: {requirements}")
        
        logger.info("Post-instalacion completada exitosamente!")
        return 0
        
    except Exception:
        logger.exception("Error critico en post-instalacion")
        return 1

if __name__ == "__main__":
    sys.exit(main())