from PyInstaller.utils.hooks import collect_submodules

# Collect all webrtcvad submodules
hiddenimports = collect_submodules("webrtcvad")

# Add specific webrtcvad imports
hiddenimports += [
    '_webrtcvad',
]

# Dejar que PyInstaller detecte automáticamente los binarios
binaries = []
datas = []