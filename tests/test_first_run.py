#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar el sistema de primera ejecución
"""
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TEST")

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_first_run_system():
    """Probar el sistema de primera ejecución"""
    print("=" * 60)
    print("PRUEBA DEL SISTEMA DE PRIMERA EJECUCIÓN")
    print("=" * 60)
    
    try:
        from utils.first_run import is_first_run, mark_first_run_complete, CONFIG_DIR, CONFIG_FILE
        
        print(f"📁 Directorio de configuración: {CONFIG_DIR}")
        print(f"📄 Archivo de configuración: {CONFIG_FILE}")
        print()
        
        # Verificar estado actual
        print("🔍 PASO 1: Verificando estado actual...")
        first_run_status = is_first_run()
        print(f"   is_first_run() = {first_run_status}")
        
        if CONFIG_FILE.exists():
            print(f"   ✅ Archivo existe: {CONFIG_FILE}")
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
                print(f"   📄 Contenido: {content}")
        else:
            print(f"   ❌ Archivo NO existe: {CONFIG_FILE}")
        
        print()
        
        # Simular completar primera ejecución
        print("🔧 PASO 2: Simulando completar primera ejecución...")
        result = mark_first_run_complete()
        print(f"   mark_first_run_complete() = {result}")
        
        if CONFIG_FILE.exists():
            print(f"   ✅ Archivo creado: {CONFIG_FILE}")
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
                print(f"   📄 Contenido: {content}")
        else:
            print(f"   ❌ ERROR: Archivo NO se creó: {CONFIG_FILE}")
        
        print()
        
        # Verificar después de marcar como completo
        print("🔍 PASO 3: Verificando después de marcar como completo...")
        first_run_status_after = is_first_run()
        print(f"   is_first_run() = {first_run_status_after}")
        
        print()
        print("=" * 60)
        if first_run_status and not first_run_status_after:
            print("✅ ÉXITO: El sistema funciona correctamente")
            print("   - Primera vez: True")
            print("   - Después de completar: False")
        else:
            print("❌ ERROR: El sistema NO funciona correctamente")
            print(f"   - Primera vez: {first_run_status}")
            print(f"   - Después de completar: {first_run_status_after}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_first_run_system()