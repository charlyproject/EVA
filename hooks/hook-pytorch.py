from PyInstaller.utils.hooks import collect_data_files

# Solo módulos esenciales para CPU
hiddenimports = [
    'torch',
    'torch._C',
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.utils.data',
    'torch.jit',
    'torch.autograd',
    'torchvision',
    'torchaudio'
]

# Solo datos esenciales
datas = collect_data_files('torch', include_py_files=True)
datas += collect_data_files('torchvision', include_py_files=True)
datas += collect_data_files('torchaudio', include_py_files=True)

# Excluir componentes CUDA
excludedimports = [
    'torch.cuda',
    'torch.backends.cuda',
    'torch.backends.cudnn',
    'torch.distributed',
    'torch.utils.cpp_extension'
]