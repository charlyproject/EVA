from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect Vosk data files (models, libraries)
datas = collect_data_files("vosk")

# Collect all Vosk submodules
hiddenimports = collect_submodules("vosk")

# Add specific Vosk imports that might be missed
hiddenimports += [
    'vosk',
    '_vosk',
]

# Dejar que PyInstaller detecte automáticamente los binarios
binaries = []