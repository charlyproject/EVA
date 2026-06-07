from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("docx")
hiddenimports += [
    'docx',
    'docx.Document',
    'docx.text',
    'docx.table',
    'docx.section',
    'docx.shared',
    'docx.enum',
    'docx.oxml',
    'docx.opc',
]

datas = []
binaries = []
