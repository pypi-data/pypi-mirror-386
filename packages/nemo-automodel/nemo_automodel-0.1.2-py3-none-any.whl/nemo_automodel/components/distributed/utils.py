# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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


import logging
from contextlib import ContextDecorator, nullcontext
from datetime import datetime, timedelta
from typing import Optional

import torch
import torch.distributed
import torch.distributed as dist

logger = logging.getLogger(__name__)


def _create_gloo_group():
    """
    Create a Gloo process group for barrier operations.

    This allows us to use monitored_barrier with Gloo backend while
    keeping NCCL for the main training operations.

    Returns:
        ProcessGroup: Gloo process group for barriers
    """
    if not dist.is_initialized():
        return None

    try:
        # Create a Gloo group for barrier operations
        gloo_group = dist.new_group(backend="gloo")
        logger.debug("Created Gloo group for barrier operations")
        return gloo_group
    except Exception as e:
        logger.warning(f"Failed to create Gloo group: {e}")
        return None


def _barrier_with_timeout(timeout: timedelta, group=None):
    """
    A timeout wrapper for torch.distributed.barrier() using Gloo backend.

    This approach creates a separate Gloo process group for barrier operations
    while keeping the main NCCL backend for training operations.

    Args:
        timeout: Maximum time to wait for the barrier
        group: Process group for the barrier operation

    Returns:
        bool: True if barrier completed successfully, False if timeout occurred
    """
    if not dist.is_initialized() or dist.get_world_size() == 1:
        return True

    # Use Gloo group for barrier operations
    gloo_group = _create_gloo_group()
    if gloo_group is None:
        # Fallback to regular barrier if Gloo group creation fails
        try:
            dist.barrier(group=group)
            return True
        except Exception as e:
            logger.warning(f"Barrier failed: {e}")
            return False

    try:
        # Use monitored_barrier with Gloo group
        dist.monitored_barrier(group=gloo_group, timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Monitored barrier failed: {e}")
        return False
    finally:
        # Clean up the Gloo group
        try:
            dist.destroy_process_group(gloo_group)
        except Exception:
            pass


class FirstRankPerNode(ContextDecorator):
    """
    Context manager to enforce rank0 to process section over other ranks.

      - Lets RANK==0 run the protected code first on each node.
      - Inserts an extra barrier across *only* the node-local rank-0 processes.
      - Works on a single GPU (no env flags, no distributed initialisation).

    Note: it is assumed the scoped code is not torch.distributed heavy.
    """

    def __enter__(self, timeout=timedelta(hours=10)):
        """
        Create / bootstrap a (distributed) proc. group that rank0 enters first.

        Returns:
            bool: ``True``  - if the current process is node-rank-0
                  ``False`` - otherwise
        """
        self._created_pg = False
        self._node0_group = None
        self._first = True  # default for single-GPU / no-dist case
        self._timeout = timeout
        if not dist.is_initialized() or dist.get_world_size() == 1:
            # pure single GPU
            return True

        # Figure out rank
        self._first = dist.get_rank() == 0

        # Synchronisation logic
        if not self._first:
            # Non-rank-0 processes wait for their node-rank-0
            # Use Gloo group for monitored_barrier to avoid NCCL timeout issues
            success = _barrier_with_timeout(timeout=self._timeout)
            if not success:
                logger.warning("Barrier timed out, continuing anyway")

        return self._first

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Tear down the context.

        1. If the current process was the first on its node, release the
           waiting peer ranks by issuing a barrier.
        2. If an exception occurred, abort the *entire* distributed job.
        3. If this context manager created the process group, destroy it.

        Args:
            exc_type (Type[BaseException] | None): Exception class if one
                occurred inside the ``with`` block.
            exc_val  (BaseException | None): The raised exception instance.
            exc_tb   (TracebackType | None): Traceback associated with the
                exception.

        Returns:
            bool: ``False`` so that any exception raised inside the ``with``
                  block is propagated to the caller (standard CM semantics).
        """
        try:
            if self._first and dist.is_initialized():
                # Re-sync the whole world so that non-rank-0s can proceed
                # Use Gloo group for monitored_barrier to avoid NCCL timeout issues
                success = _barrier_with_timeout(timeout=self._timeout)
                if not success:
                    logger.warning("Barrier timed out during exit, continuing anyway")
                if exc_type is not None:
                    # TODO: propagate failure to the entire job
                    quit(1)
        finally:
            if self._created_pg:
                dist.destroy_process_group()

        # propagate any exception to outer scope
        return False


def barrier_and_log(string: str) -> None:
    """
    Perform a distributed barrier and then log a message on rank 0.

    Args:
        string: The message string to log.
    """
    if torch.distributed.is_initialized():
        torch.distributed.barrier()
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("[{}] datetime: {} ".format(string, time_str))


def reduce_loss(
    loss_store: list[torch.Tensor],
    total_num_tokens: torch.Tensor,
    per_token_loss: bool = True,
    dp_group: Optional[torch.distributed.ProcessGroup] = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Reduce loss across all ranks.

    Args:
        loss_store: List of loss tensors to reduce.
        total_num_tokens: Total number of tokens to divide the loss by.
        per_token_loss: Whether to divide the loss by the number of tokens.
        dp_group: Process group to reduce the loss across.

    Returns:
        Tuple of reduced loss and denominator.
    """
    loss = torch.sum(torch.stack(loss_store).float()).view(1).clone().detach()
    if dp_group is not None:
        dist.all_reduce(loss, op=torch.distributed.ReduceOp.SUM, group=dp_group)

    if per_token_loss:
        denominator = total_num_tokens.clone().detach().to(torch.int)
    else:
        denominator = torch.tensor([len(loss_store)], dtype=torch.int, device="cuda")
    if dp_group is not None:
        dist.all_reduce(denominator, op=torch.distributed.ReduceOp.SUM, group=dp_group)
    return loss, denominator


def get_sync_ctx(model, is_optim_step):
    """
    Get the synchronization context for the model.

    Args:
        model: The model to synchronize.
        is_optim_step: Whether the current step is an optimizer step.

    Returns:
        A context manager that synchronizes the model.
    """
    # Use `no_sync` on DDP models when we are *not* on the final micro-batch for
    # this gradient update (i.e., when `is_grad` is False). This avoids an
    # all-reduce for every micro-batch and greatly improves throughput.
    sync_ctx = nullcontext()
    if isinstance(model, dist.fsdp._fully_shard._fully_shard.FSDPModule):
        model.set_requires_gradient_sync(is_optim_step)
    elif isinstance(model, torch.nn.parallel.DistributedDataParallel) and not is_optim_step:
        sync_ctx = model.no_sync()
    return sync_ctx


@torch.no_grad()
def rescale_gradients(model, num_tokens_for_grad_scaling, dp_group=None):
    """
    Rescale gradients across the DP group.

    Args:
        model: The model to rescale.
        num_tokens_for_grad_scaling: The number of tokens to divide the gradients by.
        dp_group: The process group to rescale the gradients across.
    """
    num_tokens_for_grad_scaling = num_tokens_for_grad_scaling.clone().detach()
    dp_group_size = 1
    if dp_group is not None:
        dist.all_reduce(num_tokens_for_grad_scaling, group=dp_group)
        dp_group_size = dist.get_world_size(group=dp_group)
    # DDP/FSDP reduces gradients across ranks, so we need to scale by the world size to inverse it
    scaling_factor = dp_group_size / num_tokens_for_grad_scaling
    for param in model.parameters():
        if param.grad is not None:
            param.grad.data.mul_(scaling_factor)


# based on: https://github.com/pytorch/torchtitan/blob/main/torchtitan/distributed/utils.py#L278
@torch.no_grad()
def clip_gradients(model, clip_norm, foreach=True):
    """
    Clip gradients across the DP group.

    Args:
        model: The model to clip the gradients of.
        clip_norm: The maximum norm of the gradients.
        foreach: if enabled will use fused operations.
    """
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    grad_norm = torch.nn.utils.get_total_norm(grads, foreach=foreach)
    if isinstance(grad_norm, torch.distributed.tensor.DTensor):
        grad_norm = grad_norm.full_tensor()
    torch.nn.utils.clip_grads_with_norm_([p for p in model.parameters()], clip_norm, grad_norm, foreach=foreach)
    return grad_norm
