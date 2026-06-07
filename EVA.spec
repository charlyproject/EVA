# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import certifi
import importlib

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

spec_root = os.path.dirname(os.path.abspath(SPEC))

# Obtener las dependencias binarias de Vosk
try:
    vosk_path = os.path.dirname(importlib.import_module('vosk').__file__)
    vosk_binaries = [
        (os.path.join(vosk_path, f), 'vosk')
        for f in os.listdir(vosk_path)
        if f.endswith(('.dll', '.so', '.pyd', '.lib'))
    ]
except Exception:
    vosk_binaries = []

a = Analysis(
    [os.path.join(spec_root, 'main.py')],
    pathex=[],
    binaries=vosk_binaries,
    datas=[
        (os.path.join(spec_root, 'config'), 'config'),
        (os.path.join(spec_root, 'resources'), 'resources'),
        (os.path.join(spec_root, 'styles.qss'), '.'),
        (certifi.where(), 'certifi'),
        (os.path.join(spec_root, 'models'), 'models'),
        (os.path.join(spec_root, 'ffmpeg'), 'ffmpeg'),
        (os.path.join(spec_root, 'piper'), 'piper'),
    ],
    hiddenimports=[
        'vosk',
        'vosk.vosk_interface',
    ],
    hookspath=[os.path.join(spec_root, 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EVA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(spec_root, 'resources', 'icon.ico')],
)
