# HOOK DESACTIVADO TEMPORALMENTE
# PyInstaller tiene hooks integrados para cryptography que funcionan mejor
# Este hook personalizado causaba conflictos con collect_binaries

# from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Solo incluir imports específicos sin recopilar binarios automáticamente
hiddenimports = [
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.hazmat.primitives.asymmetric.padding',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    'cryptography.exceptions',
]

# Dejar que PyInstaller maneje automáticamente los datos y binarios
datas = []
binaries = []