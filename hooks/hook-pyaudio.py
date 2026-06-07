from PyInstaller.utils.hooks import collect_submodules

# Collect all pyaudio submodules
hiddenimports = collect_submodules("pyaudio")

# Add specific pyaudio imports
hiddenimports += [
    '_portaudio',
    'pyaudio._portaudio',
]

# Dejar que PyInstaller detecte automáticamente los binarios
binaries = []
datas = []