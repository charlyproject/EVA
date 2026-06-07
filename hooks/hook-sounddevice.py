from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect sounddevice data files
datas = collect_data_files("sounddevice")

# Collect all sounddevice submodules
hiddenimports = collect_submodules("sounddevice")

# Add specific sounddevice imports
hiddenimports += [
    '_sounddevice',
    'sounddevice._sounddevice',
]

# Dejar que PyInstaller detecte automáticamente los binarios
binaries = []