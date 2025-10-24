# -*- coding: utf-8 -*-
"""Joblib-tqdm: Parallel processing with progress bars using joblib and tqdm."""

from .parallel import ParallelApplier, tqdm_joblib
from .version_helper import get_version

__version__ = get_version()
__all__ = ["ParallelApplier", "tqdm_joblib"]