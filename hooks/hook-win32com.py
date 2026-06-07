from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Recopilar submódulos de win32com
hiddenimports = collect_submodules('win32com') + [
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'pythoncom',
    'pywintypes',
    'win32com.client',
    'win32com.server',
    'win32com.shell'
]

# Recopilar archivos de datos de win32com
datas = collect_data_files('win32com')

# No incluir binarios manualmente - PyInstaller los detectará automáticamente
binaries = []