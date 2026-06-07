from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("ddgs")
hiddenimports += [
    'ddgs',
    'ddgs.DDGS',
]

datas = []
binaries = []
