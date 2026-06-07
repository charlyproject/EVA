from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("fitz")
hiddenimports = [
    'fitz',
    'fitz.fitz',
]
binaries = collect_dynamic_libs("fitz")
