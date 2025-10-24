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

# Copyright (C) 2024 Apple Inc. All Rights Reserved.

# IMPORTANT:  This Apple software is supplied to you by Apple
# Inc. ("Apple") in consideration of your agreement to the following
# terms, and your use, installation, modification or redistribution of
# this Apple software constitutes acceptance of these terms.  If you do
# not agree with these terms, please do not use, install, modify or
# redistribute this Apple software.

# In consideration of your agreement to abide by the following terms, and
# subject to these terms, Apple grants you a personal, non-exclusive
# license, under Apple's copyrights in this original Apple software (the
# "Apple Software"), to use, reproduce, modify and redistribute the Apple
# Software, with or without modifications, in source and/or binary forms;
# provided that if you redistribute the Apple Software in its entirety and
# without modifications, you must retain this notice and the following
# text and disclaimers in all such redistributions of the Apple Software.
# Neither the name, trademarks, service marks or logos of Apple Inc. may
# be used to endorse or promote products derived from the Apple Software
# without specific prior written permission from Apple.  Except as
# expressly stated in this notice, no other rights or licenses, express or
# implied, are granted by Apple herein, including but not limited to any
# patent rights that may be infringed by your derivative works or by other
# works in which the Apple Software may be incorporated.

# The Apple Software is provided by Apple on an "AS IS" basis.  APPLE
# MAKES NO WARRANTIES, EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION
# THE IMPLIED WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE, REGARDING THE APPLE SOFTWARE OR ITS USE AND
# OPERATION ALONE OR IN COMBINATION WITH YOUR PRODUCTS.

# IN NO EVENT SHALL APPLE BE LIABLE FOR ANY SPECIAL, INDIRECT, INCIDENTAL
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) ARISING IN ANY WAY OUT OF THE USE, REPRODUCTION,
# MODIFICATION AND/OR DISTRIBUTION OF THE APPLE SOFTWARE, HOWEVER CAUSED
# AND WHETHER UNDER THEORY OF CONTRACT, TORT (INCLUDING NEGLIGENCE),
# STRICT LIABILITY OR OTHERWISE, EVEN IF APPLE HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


# -------------------------------------------------------------------------------
# SOFTWARE DISTRIBUTED WITH CUT CROSS ENTROPY:

# The Cut Cross Entropy software includes a number of subcomponents with separate
# copyright notices and license terms - please see the file ACKNOWLEDGEMENTS.md.
# -------------------------------------------------------------------------------


from typing import Optional

import torch
import torch.nn as nn

from nemo_automodel.shared.import_utils import MISSING_CUT_CROSS_ENTROPY_MSG

try:
    import cut_cross_entropy.tl_utils as tl_utils
    from cut_cross_entropy import linear_cross_entropy

    HAVE_CUT_CROSS_ENTROPY = True
except ImportError:  # pragma: no cover
    HAVE_CUT_CROSS_ENTROPY = False  # pragma: no cover


def new_is_triton_greater_or_equal(version_str):
    """
    Check if pytorch-triton version is greater than or equal to the specified version.

    Args:
        version_str: Version string to check

    Returns:
        bool: True if pytorch-triton version >= specified version
    """
    import pkg_resources

    try:
        pytorch_triton_version = pkg_resources.get_distribution("pytorch-triton").version
        current = pkg_resources.parse_version(pytorch_triton_version)
        required = pkg_resources.parse_version(version_str)
        print(f"Current pytorch-triton version: {pytorch_triton_version}, Required triton version: {version_str}")
        return current >= required
    except pkg_resources.DistributionNotFound:
        print("pytorch-triton not found")
        return False


def new_is_triton_greater_or_equal_3_2_0():
    """
    Check if pytorch-triton version is greater than or equal to 3.1.0.

    Returns:
        bool: True if pytorch-triton version >= 3.1.0
    """
    return new_is_triton_greater_or_equal("3.1.0")


if HAVE_CUT_CROSS_ENTROPY:
    # Apply the monkey patches
    tl_utils.is_triton_greater_or_equal = new_is_triton_greater_or_equal
    tl_utils.is_triton_greater_or_equal_3_2_0 = new_is_triton_greater_or_equal_3_2_0


class FusedLinearCrossEntropy(nn.Module):
    def __init__(self, ignore_index: int = -100, logit_softcapping: float = 0, reduction: str = "sum"):
        """
        Fused linear cross entropy loss.

        Args:
            ignore_index (int): Target value that is ignored when computing the loss. Defaults to -100.
            logit_softcapping (float): Value for softcapping logits (0 means no capping). Defaults to 0.
            reduction (str): Type of reduction. Defaults to "sum".
        """
        super().__init__()
        self.ignore_index = ignore_index
        self.logit_softcapping = logit_softcapping
        self.reduction = reduction

    def forward(
        self,
        hidden_states: torch.Tensor,
        labels: torch.Tensor,
        lm_weight: torch.Tensor,
        num_label_tokens: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Compute fused linear cross entropy loss that matches PyTorch's cross_entropy behavior.

        Args:
            hidden_states: Input hidden states
            labels: Target labels
            lm_weight: Weight matrix for linear transformation
            num_label_tokens: Number of non-padding tokens.
        """
        if not HAVE_CUT_CROSS_ENTROPY:
            raise ImportError(MISSING_CUT_CROSS_ENTROPY_MSG)

        # First compute loss with sum reduction to handle normalization ourselves
        if self.logit_softcapping == 0:
            self.logit_softcapping = None

        # Compute loss with shift=False to match PyTorch behavior
        # Set filter_eps=None to avoid any token filtering
        loss = linear_cross_entropy(
            hidden_states,
            lm_weight,
            targets=labels,
            ignore_index=self.ignore_index,
            softcap=self.logit_softcapping,
            reduction=self.reduction,  # Use sum reduction to handle normalization ourselves
            shift=False,  # Match PyTorch behavior
            filter_eps=None,  # No token filtering
        )
        if num_label_tokens is not None:
            assert self.reduction == "sum", "num_label_tokens is only supported when reduction is 'sum'"
            loss = loss / num_label_tokens
        return loss
