from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("soundfile")
hiddenimports = collect_submodules("soundfile")
hiddenimports += [
    'soundfile',
    '_soundfile_data',
]

binaries = []
