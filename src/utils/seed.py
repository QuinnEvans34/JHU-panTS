"""Global seeding for reproducible runs (Python / NumPy / torch / MPS)."""
from __future__ import annotations

import os
import random

import numpy as np


def set_seed(seed: int = 42, deterministic: bool = True) -> int:
    """Seed all RNGs. torch is optional so this import-safe module works before torch is installed."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if hasattr(torch, "mps") and torch.backends.mps.is_available():
            torch.mps.manual_seed(seed)
        if deterministic:
            try:
                torch.use_deterministic_algorithms(True, warn_only=True)
            except Exception:
                pass  # some ops (esp. on MPS) have no deterministic impl — don't hard-fail
    except ImportError:
        pass
    return seed
