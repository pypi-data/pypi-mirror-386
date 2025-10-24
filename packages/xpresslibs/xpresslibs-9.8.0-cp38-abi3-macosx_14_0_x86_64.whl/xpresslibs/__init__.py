# This file is only included in the xpresslibs PyPI package. It is used on
# Windows to locate the solver libraries and CUDA runtime.
import os
solver_libs_dir = os.path.join(os.path.dirname(__file__), 'lib')
cuda_libs_dir = os.path.join(os.path.dirname(__file__), '../nvidia/cu13/bin/x86_64')
