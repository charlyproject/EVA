from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("odf")
hiddenimports += [
    'odf',
    'odf.text',
    'odf.teletype',
    'odf.opendocument',
    'odf.style',
    'odf.element',
]

datas = []
binaries = []
