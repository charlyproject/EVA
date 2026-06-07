from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect pandas submodules
hiddenimports = collect_submodules("pandas")

# Collect pandas data files
datas = collect_data_files("pandas")

# Dejar que PyInstaller detecte automáticamente los binarios
binaries = []

# Add specific pandas imports that might be missed
hiddenimports += [
    'pandas._libs',
    'pandas._libs.tslibs',
    'pandas._libs.tslibs.base',
    'pandas._libs.tslibs.timestamps',
    'pandas.io.formats.style',
    'pandas.plotting._matplotlib',
    'pandas.core.arrays',
    'pandas.core.arrays.categorical',
    'pandas.core.arrays.period',
    'pandas.core.ops',
]