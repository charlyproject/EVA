import os
import json

def check_installation():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("\n=== Verificacion de Instalacion EVA ===")
    print(f"Directorio base: {base_dir}")
    
    # 1. Verificar archivos criticos
    critical_files = {
        "install_config.json": os.path.join(base_dir, "config", "install_config.json"),
        "knowledge_base": os.path.join(base_dir, "eva_knowledge_base.json"),
        "main_executable": os.path.join(base_dir, "EVA.exe")
    }
    
    print("\nArchivos criticos:")
    for name, path in critical_files.items():
        exists = os.path.exists(path)
        print(f"- {name}: {'OK' if exists else 'FALTANTE'} ({path})")
        
        if exists and name == "install_config.json":
            try:
                with open(path, 'r') as f:
                    content = json.load(f)
                    print(f"  Contenido: {json.dumps(content, indent=2)}")
                    
                    # Verificar campos minimos
                    required_fields = ["default_language", "default_voice", "installed_models"]
                    missing_fields = [field for field in required_fields if field not in content]
                    if missing_fields:
                        print(f"  ⚠️ Campos faltantes: {', '.join(missing_fields)}")
            except Exception as e:
                print(f"  Error leyendo archivo: {str(e)}")
    
    # 2. Verificar recursos
    print("\nRecursos esenciales:")
    resources = ["models", "piper", "ffmpeg", "resources", "core", "ui", "commands", "utils", "voice", "help_system", "hooks"]
    for res in resources:
        path = os.path.join(base_dir, res)
        exists = os.path.exists(path)
        print(f"- {res}: {'OK' if exists else 'FALTANTE'} ({path})")
        
        if exists:
            items = os.listdir(path)
            print(f"  Contenido: {items[:3]}{'...' if len(items) > 3 else ''}")
    
    # 3. Verificar wizard
    print("\nWizard de instalacion:")
    wizard_paths = [
        os.path.join(base_dir, "_internal", "installer", "scripts", "install_wizard.py"),
        os.path.join(base_dir, "installer", "scripts", "install_wizard.py"),
        os.path.join(base_dir, "install_wizard.py")
    ]
    
    for path in wizard_paths:
        exists = os.path.exists(path)
        print(f"- {path}: {'EXISTE' if exists else 'NO EXISTE'}")

if __name__ == "__main__":
    check_installation()
    input("\nPresione Enter para salir...")