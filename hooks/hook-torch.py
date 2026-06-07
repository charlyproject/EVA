# -*- coding: utf-8 -*-
"""
Hook para PyTorch - Optimizado para CPU únicamente desde _internal
Excluye componentes CUDA para reducir tamaño y evitar conflictos
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

# Recopilar submódulos esenciales de torch (solo los que existen)
hiddenimports = [
    'torch._C',
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.utils',
    'torch.utils.data',
    'torch.jit',
    'torch.autograd',
    'torch.backends',
    'torch.backends.cpu',
    'torch.distributed',
    'torch.multiprocessing',
    'torch.serialization',
    'torch.storage',
    'torch.tensor',
    'torch.random',
    'torch.sparse',
    'torch.overrides',
    'torch.fx',
    'torch.onnx',
    'torch.quantization',
    'torch.profiler',
    'torch.hub',
    'torch.library',
    'torch.masked',
    'torch.nested',
    'torch.special',
    'torch.linalg',
    'torch.fft',
    'torch.signal',
    'torch.testing',
    'torch.utils.benchmark',
    'torch.utils.bottleneck',
    'torch.utils.checkpoint',
    'torch.utils.cpp_extension',
    'torch.utils.data.datapipes',
    'torch.utils.tensorboard',
    'torch.utils.mobile_optimizer',
    'torch.utils.model_zoo',
    'torch.utils.collect_env',
    'torch.utils.hipify',
    'torch.utils.file_baton',
    'torch.utils.dlpack',
    'torch.utils.weak',
]

# Recopilar librerías dinámicas (solo CPU)
binaries = collect_dynamic_libs('torch')

# Excluir componentes CUDA para reducir tamaño y evitar conflictos
excludedimports = [
    'torch.cuda',
    'torch.backends.cuda',
    'torch.backends.cudnn',
    'torch.utils.cpp_extension',
    'torch.distributed.rpc',
    'torch.distributed.pipeline',
    'torch.distributed.elastic',
    'torch.distributed.launcher',
    'torch.distributed.run',
    'torch.distributed.algorithms',
    'torch.distributed.checkpoint',
    'torch.distributed.device_mesh',
    'torch.distributed.tensor',
    'torch.distributed.optim',
    'torch.distributed.fsdp',
    'torch.distributed._shard',
    'torch.distributed._spmd',
    'torch.distributed._tensor',
    'torch.distributed.nn',
    'torch.distributed.utils',
]