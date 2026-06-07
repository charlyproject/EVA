from PyInstaller.utils.hooks import collect_submodules

# Collect all keyboard submodules
hiddenimports = collect_submodules("keyboard")

# Add specific keyboard imports for Windows
hiddenimports += [
    'keyboard._keyboard_event',
    'keyboard._winkeyboard',
    'keyboard._generic',
]