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


def dtype_from_str(val):
    """
    Translate a str val of a dtype into the corresponding torch.dtype
    Args:
        val (str): the dotted path of the dtype (e.g., "torch.bfloat16").

    Returns:
        torch.dtype: the actual dtype (e.g., torch.bfloat16)
    """
    import torch

    if isinstance(val, torch.dtype):
        return val
    lut = {
        "torch.float": torch.float,
        "torch.float32": torch.float,
        "torch.float64": torch.float64,
        "torch.double": torch.float64,
        "torch.complex64": torch.complex,
        "torch.cfloat": torch.complex,
        "torch.float16": torch.float16,
        "torch.half": torch.float16,
        "torch.bfloat16": torch.bfloat16,
        "torch.uint8": torch.uint8,
        "torch.int8": torch.int8,
        "torch.int16": torch.int16,
        "torch.short": torch.short,
        "torch.int32": torch.int32,
        "torch.int": torch.int,
        "torch.int64": torch.int64,
        "torch.long": torch.long,
        "torch.bool": torch.bool,
        "bf16": torch.bfloat16,
    }

    val_lower = val.lower()
    if val_lower in lut:
        return lut[val_lower]
    torch_val = "torch." + val_lower
    if torch_val in lut:
        return lut[torch_val]
    raise KeyError(f"Unknown dtype string: {val}")
