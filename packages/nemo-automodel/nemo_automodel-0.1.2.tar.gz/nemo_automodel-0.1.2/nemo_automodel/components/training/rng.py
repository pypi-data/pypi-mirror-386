# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
from dataclasses import dataclass

import numpy as np
import torch


def init_all_rng(seed: int, ranked: bool = False):
    """Initialize RNGs for Python, NumPy, and PyTorch (incl. CUDA) with a seed.

    Args:
        seed (int): Base seed value.
        ranked (bool): Adjust seed by process rank if True.
    """
    assert isinstance(seed, int) and seed > 0, ("Seed must be a positive integer", seed)
    assert isinstance(ranked, bool), "Ranked must be a boolean"

    if ranked:
        # Example: use PyTorch's distributed rank if available
        try:
            import torch.distributed as dist

            if dist.is_initialized():
                seed += dist.get_rank()
        except ImportError:
            pass

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@dataclass
class RNGState:
    random_rng_state: tuple
    np_rng_state: tuple
    torch_rng_state: torch.Tensor
    cuda_rng_state: torch.Tensor


def _get_rng_state():
    """Get current RNG states.

    Returns:
        dict: RNG states for random, NumPy, and PyTorch.
    """
    return RNGState(
        random_rng_state=random.getstate(),
        np_rng_state=np.random.get_state(),
        torch_rng_state=torch.get_rng_state(),
        cuda_rng_state=torch.cuda.get_rng_state_all(),
    )


def _restore_rng_state(state):
    """Restore RNG states from a saved state.

    Args:
        state (dict): RNG states as returned by state_dict().
    """
    random.setstate(state.random_rng_state)
    np.random.set_state(state.np_rng_state)
    torch.set_rng_state(state.torch_rng_state)
    torch.cuda.set_rng_state_all(state.cuda_rng_state)


class StatefulRNG:
    """
    RNG manager for reproducible RNG states across random, NumPy, and PyTorch."""

    def __init__(self, seed: int, ranked: bool = False):
        """Initialize and optionally rank-adjust RNGs with a given seed.

        Args:
            seed (int): Base seed for RNGs.
            ranked (bool): Adjust seed based on process rank.
        """
        self.seed = seed
        self.ranked = ranked
        init_all_rng(self.seed, self.ranked)

    def state_dict(self):
        """Get current RNG states.

        Returns:
            dict: RNG states for random, NumPy, and PyTorch.
        """
        return _get_rng_state()

    def load_state_dict(self, state):  # pragma: no cover
        """Restore RNG states from a saved state.

        Args:
            state (dict): RNG states as returned by state_dict().
        """
        _restore_rng_state(state)


class ScopedRNG:
    """Context manager for reproducible RNG states across random, NumPy, and PyTorch."""

    def __init__(self, seed: int = 95050, ranked: bool = False):
        """Initialize and optionally rank-adjust RNGs with a given seed.

        Args:
            seed (int): Base seed for RNGs.
            ranked (bool): Adjust seed based on process rank.
        """
        self._saved_state = None
        self.seed = seed
        self.ranked = ranked

    def __enter__(self):
        """Save current RNG states."""
        assert self._saved_state is None
        self._saved_state = _get_rng_state()
        init_all_rng(self.seed, self.ranked)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Restore RNG states on context exit."""
        _restore_rng_state(self._saved_state)
        self._saved_state = None
