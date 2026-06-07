from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect pygame data files
datas = collect_data_files("pygame")

# Collect all pygame submodules
hiddenimports = collect_submodules("pygame")

# Add specific pygame imports for audio functionality
hiddenimports += [
    'pygame.mixer',
    'pygame.sndarray',
    'pygame._sdl2',
    'pygame._sdl2.audio',
    'pygame._sdl2.mixer',
    'pygame.time',
    'pygame.event',
]

# Dejar que PyInstaller detecte automáticamente los binarios
binaries = []