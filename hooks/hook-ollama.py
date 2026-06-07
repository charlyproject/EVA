from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect ollama data files
datas = collect_data_files("ollama")

# Collect all ollama submodules
hiddenimports = collect_submodules("ollama")

# Add specific ollama imports
hiddenimports += [
    'ollama',
    'ollama.client',
    'ollama.async_client',
    'ollama.constants'
]

# Exclude unused components
excludedimports = [
    'ollama.tests',
    'ollama.bin'
]