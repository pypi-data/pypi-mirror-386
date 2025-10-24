<div align="center">

# 🚀 NeMo AutoModel

</div>

<div align="center">

<!-- [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) -->
[![codecov](https://codecov.io/github/NVIDIA-NeMo/Automodel/graph/badge.svg?token=4NMKZVOW2Z)](https://codecov.io/github/NVIDIA-NeMo/Automodel)
[![CICD NeMo](https://github.com/NVIDIA-NeMo/Automodel/actions/workflows/cicd-main.yml/badge.svg)](https://github.com/NVIDIA-NeMo/Automodel/actions/workflows/cicd-main.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![GitHub Stars](https://img.shields.io/github/stars/NVIDIA-NeMo/Automodel.svg?style=social&label=Star)](https://github.com/NVIDIA-NeMo/Automodel/stargazers/)

<!-- **Day-0 integration with Hugging Face models automating fine-tuning and pretraining with pytorch-native parallelism, custom-kernels and optimized recipes** -->

[📖 Documentation](https://docs.nvidia.com/nemo/automodel/latest/index.html) • [🔥 Ready-to-Use Recipes](https://github.com/NVIDIA-NeMo/Automodel/#-ready-to-use-recipes) • [💡 Examples](https://github.com/NVIDIA-NeMo/Automodel/tree/main/examples) • [🤝 Contributing](https://github.com/NVIDIA-NeMo/Automodel/blob/main/CONTRIBUTING.md)

</div>

---

NeMo Framework is NVIDIA's GPU accelerated, end-to-end training framework for large language models (LLMs), multi-modal models and speech models. It enables seamless scaling of training (both pretraining and post-training) workloads from single GPU to thousand-node clusters for both 🤗Hugging Face/PyTorch and Megatron models. It includes a suite of libraries and recipe collections to help users train models from end to end. The **AutoModel library ("NeMo AutoModel")** provides GPU-accelerated PyTorch training for 🤗Hugging Face models on **Day-0**. Users can start training and fine-tuning models instantly without conversion delays, scale effortlessly with PyTorch-native parallelisms, optimized custom kernels, and memory-efficient recipes-all while preserving the original checkpoint format for seamless use across the Hugging Face ecosystem.

> ⚠️ Note: NeMo AutoModel is under active development. New features, improvements, and documentation updates are released regularly. We are working toward a stable release, so expect the interface to solidify over time. Your feedback and contributions are welcome, and we encourage you to follow along as new updates roll out.

## Feature Roadmap

✅ _Available now_ | 🔜 _Coming in 25.09_

- ✅ **HuggingFace Integration** - Works with 1-70B models (Qwen, Llama).
- ✅ **Distributed Training** - Fully Sharded Data Parallel (FSDP2) support.
- ✅ **Environment Support** - Support for SLURM and interactive training.
- ✅ **Learning Algorithms** - SFT (Supervised Fine-Tuning), and PEFT (Parameter Efficient Fine-Tuning).
- ✅ **Large Model Support** - Native PyTorch support for models up to 70B parameters.
- ✅ **Advanced Parallelism** - PyTorch native FSDP2, TP, CP, and SP for efficient training.
- ✅ **Sequence Packing** - Sequence packing in both DTensor and MCore for huge training perf gains.
- ✅ **DCP** - Distributed Checkpoint support with SafeTensors output.
- ✅ **HSDP** - Hybrid Sharding Data Parallelism based on FSDP2.

- 🔜 **Pipeline Support** - Torch-native support for pipelining composable with FSDP2 and DTensor (3D Parallelism).
- 🔜 **Pre-training** - Support for model pre-training, including DeepSeekV3, GPT-OSS and Qwen3 (Coder-480B-A35B, etc).
- 🔜 **Knowledge Distillation** - Support for knowledge distillation with LLMs; VLM support will be added post 25.09.


## 🎛️ Supported Models
NeMo AutoModel provides native support for a wide range of models available on the Hugging Face Hub, enabling efficient fine-tuning for various domains. Below is a comprehensive list of all supported models with their available recipes:

### 📋 Ready-to-Use Recipes
To get started quickly, NeMo AutoModel provides a collection of ready-to-use recipes for common LLM and VLM fine-tuning tasks. Simply select the recipe that matches your model and training setup (e.g., single-GPU, multi-GPU, or multi-node).

| Domain | Model Family | Model ID | Recipes |
|--------|--------------|----------|---------|
| **LLM** |  **LLaMA** | [`meta-llama/Llama-3.2-1B`](https://huggingface.co/meta-llama/Llama-3.2-1B) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/llama3_2/llama3_2_1b_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/llama3_2/llama3_2_1b_hellaswag_peft.yaml) |
| | | [`meta-llama/Llama-3.2-3B-Instruct`](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/llama3_2/llama_3_2_3b_instruct_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/llama3_2/llama_3_2_3b_instruct_squad_peft.yaml) |
| | | [`meta-llama/Llama-3.1-8B`](https://huggingface.co/meta-llama/Llama-3.1-8B) | [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/llama3_1/llama3_1_8b_hellaswag_fp8.yaml) |
| **LLM** | **Mistral** | [`mistralai/Mistral-7B-v0.1`](https://huggingface.co/mistralai/Mistral-7B-v0.1) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mistral_7b_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mistral_7b_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mistral_7b_hellaswag_fp8.yaml) |
|  |  | [`mistralai/Mistral-Nemo-Base-2407`](https://huggingface.co/mistralai/Mistral-Nemo-Base-2407) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mistral_nemo_2407_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mistral_nemo_2407_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mistral_nemo_2407_hellaswag_fp8.yaml) |
|  |  | [`mistralai/Mixtral-8x7B-Instruct-v0.1`](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) |[PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/mistral/mixtral_8x7b_instruct_squad_peft.yaml) |
| **LLM** | **Qwen** | [`Qwen/Qwen2.5-7B`](https://huggingface.co/Qwen/Qwen2.5-7B) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwen2_5_7b_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwen2_5_7b_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwen2_5_7b_hellaswag_fp8.yaml) |
|  |  | [`Qwen/Qwen3-0.6B`](https://huggingface.co/Qwen/Qwen3-0.6B) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwen3_0p6b_hellaswag.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwen3_0p6b_hellaswag_peft.yaml) |
|  |  | [`Qwen/QwQ-32B`](https://huggingface.co/Qwen/QwQ-32B) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwq_32b_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/qwen/qwq_32b_squad_peft.yaml) |
| **LLM** | **Gemma** | [`google/gemma-3-270m`](https://huggingface.co/google/gemma-3-270m) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_3_270m_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_3_270m_squad_peft.yaml) |
| | | [`google/gemma-2-9b-it`](https://huggingface.co/google/gemma-2-9b-it) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_2_9b_it_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_2_9b_it_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_2_9b_it_hellaswag_fp8.yaml) |
| | | [`google/gemma-7b`](https://huggingface.co/google/gemma-7b) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_7b_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/gemma/gemma_7b_squad_peft.yaml) |
| **LLM** | **Phi** | [`microsoft/phi-2`](https://huggingface.co/microsoft/phi-2) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_2_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_2_squad_peft.yaml) |
|  |  | [`microsoft/Phi-3-mini-4k-instruct`](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_3_mini_it_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_3_mini_it_squad_peft.yaml) |
|  |  | [`microsoft/phi-4`](https://huggingface.co/microsoft/phi-4) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_4_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_4_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/phi/phi_4_hellaswag_fp8.yaml) |
| **LLM** | **Seed** | [`ByteDance-Seed/Seed-Coder-8B-Instruct`](https://huggingface.co/ByteDance-Seed/Seed-Coder-8B-Instruct) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/seed/seed_coder_8b_instruct_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/seed/seed_coder_8b_instruct_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/seed/seed_coder_8b_instruct_hellaswag_fp8.yaml) |
|  |  | [`ByteDance-Seed/Seed-OSS-36B-Instruct`](https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Instruct) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/seed/seed_oss_36B_hellaswag.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/seed/seed_oss_36B_hellaswag_peft.yaml) |
| **LLM** | **Baichuan** | [`baichuan-inc/Baichuan2-7B-Chat`](https://huggingface.co/baichuan-inc/Baichuan2-7B-Chat) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/baichuan/baichuan_2_7b_squad.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/baichuan/baichuan_2_7b_squad_peft.yaml), [FP8](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/baichuan/baichuan_2_7b_mock_fp8.yaml) |
| **VLM** | **Gemma** | [`google/gemma-3-4b-it`](https://huggingface.co/google/gemma-3-4b-it) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune/gemma3/gemma3_vl_4b_cord_v2.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune/gemma3/gemma3_vl_4b_cord_v2_peft.yaml) |
|  |  | [`google/gemma-3n-e4b-it`](https://huggingface.co/google/gemma-3n-e4b-it) | [SFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune/gemma3n/gemma3n_vl_4b_medpix.yaml), [PEFT](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune/gemma3n/gemma3n_vl_4b_medpix_peft.yaml) |

**And more**: Check out more [LLM](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune) and [VLM](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune) examples! Any causal LM on Hugging Face Hub can be used with the base recipe template!

### Run a Recipe
To run a NeMo AutoModel recipe, you need a recipe script (e.g., [LLM](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/finetune.py), [VLM](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune/finetune.py)) and a YAML config file (e.g., [LLM](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/llm_finetune/llama/llama3_2_1b_squad.yaml), [VLM](https://github.com/NVIDIA-NeMo/Automodel/blob/main/examples/vlm_finetune/gemma3/gemma3_vl_4b_cord_v2_peft.yaml)):
```
# Command invocation format:
uv run <recipe_script_path> --config <yaml_config_path>

# LLM example: multi-GPU with FSDP2
uv run torchrun --nproc-per-node=8 recipes/llm_finetune/finetune.py --config recipes/llm_finetune/llama/llama3_2_1b_hellaswag.yaml

# VLM example: single GPU fine-tuning (Gemma-3-VL) with LoRA
uv run recipes/vlm_finetune/finetune.py --config recipes/vlm_finetune/gemma3/gemma3_vl_3b_cord_v2_peft.yaml
```


<!-- 
### PEFT Methods
- **LoRA**: Low-Rank Adaptation
<!-- - **DoRA**: Weight-Decomposed Low-Rank Adaptation
- **Custom**: Easy to implement new PEFT methods -->


## 🚀 Key Features

- **Day-0 Hugging Face Support**: Instantly fine-tune any model from the Hugging Face Hub
- **Lightning Fast Performance**: Custom CUDA kernels and memory optimizations deliver 2–5× speedups
- **Large-Scale Distributed Training**: Built-in FSDP2 and Megatron-FSDP for seamless multi-node scaling
- **Vision-Language Model Ready**: Native support for VLMs (Qwen2-VL, Gemma-3-VL, etc)
- **Advanced PEFT Methods**: LoRA and extensible PEFT system out of the box
- **Seamless HF Ecosystem**: Fine-tuned models work perfectly with Transformers pipeline, VLM, etc.
- **Robust Infrastructure**: Distributed checkpointing with integrated logging and monitoring
- **Optimized Recipes**: Pre-built configurations for common models and datasets
- **Flexible Configuration**: YAML-based configuration system for reproducible experiments
- **FP8 Precision**: Native FP8 training & inference for higher throughput and lower memory use
- **INT4 / INT8 Quantization**: Turn-key quantization workflows for ultra-compact, low-memory training


---
## ✨ Install NeMo AutoModel
NeMo AutoModel is offered both as a standard Python package installable via pip and as a ready-to-run NeMo Framework Docker container.

### Prerequisites
```
# We use `uv` for package management and environment isolation.
pip3 install uv

# If you cannot install at the system level, you can install for your user with
# pip3 install --user uv
```
Run every command with `uv run`. It auto-installs the virtual environment from the lock file and keeps it up to date, so you never need to activate a venv manually. Example: `uv run recipes/llm_finetune/finetune.py`. If you prefer to install NeMo Automodel explicitly, please follow the instructions below.

### 📦 Install from a Wheel Package
```
# Install the latest stable release from PyPI
# We first need to initialize the virtual environment using uv
uv venv

uv pip install nemo_automodel   # or: uv pip install --upgrade nemo_automodel
```

### 🔧 Install from Source
```
# Install the latest NeMo Automodel from the GitHub repo (best for development).
# We first need to initialize the virtual environment using uv
uv venv

# We can now install from source
uv pip install git+https://github.com/NVIDIA-NeMo/Automodel.git
```

<!-- ### 🐳 NeMo Container
```bash
# Pull the latest NeMo Framework container
docker pull nvcr.io/nvidia/nemo:25.07

# Run with GPU support
docker run --gpus all -it --rm \
    -v $(pwd):/workspace \
    nvcr.io/nvidia/nemo:25.07 bash
``` -->

### Verify the Installation
```
uv run python -c "import nemo_automodel; print('✅ NeMo AutoModel ready')"
```

---

<!-- ## 🔥 Quickstart -->

<!-- ### 30-Second Fine-tuning

```python
import nemo_automodel as na

# Load any Hugging Face model
model = na.NeMoAutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")

# Apply LoRA with one line
na.peft.lora(model, rank=16, alpha=32)

# Your model is ready for training!
``` -->

<!-- ## Run with Pre-built Recipes
These YAML examples illustrate common configurations used with NeMo AutoModel recipes.

```bash
# Fine-tune LLaMA on HellaSwag (single GPU)
python recipes/llm_finetune/finetune.py --config recipes/llm_finetune/llama/llama3_2_1b_squad.yaml

# Fine-tune with LoRA (memory efficient)
python recipes/llm_finetune/finetune.py --config recipes/llm_finetune/llama/llama3_2_1b_hellaswag_peft.yaml

# Multi-GPU with FSDP2
torchrun --nproc-per-node=8 recipes/llm_finetune/finetune.py --config recipes/llm_finetune/llama/llama_3_2_1b_hellaswag.yaml

# Multi-GPU with Megatron-FSDP
torchrun --nproc-per-node=8 recipes/llm_finetune/finetune.py --config recipes/llm_finetune/llama/llama_3_2_1b_hellaswag_megatron_fsdp.yaml

```
<!-- # #Multi-Node training
# torchrun --nproc-per-node=8 --nnodes=2 \
#     recipes/llm_finetune/finetune.py --config recipes/llm_finetune/llama/llama3_2_1b_squad_megatron_fsdp.yaml
### Vision-Language Models 
- ->

```bash
# Fine-tune Qwen2.5-VL
python recipes/vlm_finetune/finetune.py --config recipes/vlm_finetune/qwen2_5_vl_3b_rdr.yaml

# Fine-tune Gemma-3-VL with LoRA on a single GPU
python recipes/vlm_finetune/finetune.py --config recipes/vlm_finetune/gemma_3_vl_3b_cord_v2_peft.yaml
```

---
 -->

## 📋 YAML Configuration Examples


### 1. Distributed Training Configuration

```yaml
distributed:
  _target_: nemo_automodel.distributed.megatron_fsdp.MegatronFSDPManager
  dp_size: 8
  tp_size: 1
  cp_size: 1

```

### 2. LoRA Configuration
```yaml
peft:
  peft_fn: nemo_automodel._peft.lora.apply_lora_to_linear_modules
  match_all_linear: True
  dim: 8
  alpha: 32
  use_triton: True
```

### 3. Vision-Language Model Fine-Tuning
```yaml
model:
  _target_: nemo_automodel._transformers.NeMoAutoModelForImageTextToText.from_pretrained
  pretrained_model_name_or_path: Qwen/Qwen2.5-VL-3B-Instruct

processor:
  _target_: transformers.AutoProcessor.from_pretrained
  pretrained_model_name_or_path: Qwen/Qwen2.5-VL-3B-Instruct
  min_pixels: 200704
  max_pixels: 1003520
```

### 4. Checkpointing and Resume
```yaml
checkpoint:
  enabled: true
  checkpoint_dir: ./checkpoints
  save_consolidated: true      # HF-compatible safetensors
  model_save_format: safetensors
```

---

<!-- ## ⚡ Performance (Do we have a table like to show/do we want to show it?)

NeMo AutoModel delivers significant speedups through optimized kernels and distributed training:

| Model | Method | Speedup | Memory Savings |
|-------|--------|---------|----------------|
| LLaMA-3-8B | LoRA + Liger | **3.2x** | 60% |
| Qwen2.5-7B | Full FT + FSDP2 | **2.8x** | 40% |  
| Gemma-2-9B | DoRA + Cut-CE | **4.1x** | 55% |

### Optimizations Included
- **Liger Kernel**: Optimized attention and MLP operations
- **Cut-CrossEntropy**: Memory-efficient loss computation
- **FSDP2**: Latest fully sharded data parallelism
- **Megatron FSDP**: NVIDIA's enterprise FSDP implementation
- **Mixed Precision**: Automatic FP16/BF16 training

--- -->

## 🗂️ Project Structure

```
NeMo-Automodel/
├── nemo_automodel/              # Core library
│   ├── _peft/                   # PEFT implementations (LoRA)
│   ├── _transformers/           # HF model integrations  
│   ├── checkpoint/              # Distributed checkpointing
│   ├── datasets/                # Dataset loaders
│   │   ├── llm/                 # LLM datasets (HellaSwag, SQuAD, etc.)
│   │   └── vlm/                 # VLM datasets (CORD-v2, rdr etc.)
│   ├── distributed/             # FSDP2, Megatron FSDP, parallelization
│   ├── loss/                    # Optimized loss functions
│   └── training/                # Training recipes and utilities
├── recipes/                     # Ready-to-use training recipes
│   ├── llm/                     # LLM fine-tuning recipes
│   └── vlm/                     # VLM fine-tuning recipes  
└── tests/                       # Comprehensive test suite
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/NVIDIA-NeMo/Automodel/blob/main/CONTRIBUTING.md) for details.

---

## 📄 License

NVIDIA NeMo AutoModel is licensed under the [Apache License 2.0](https://github.com/NVIDIA-NeMo/Automodel/blob/main/LICENSE).

---


## 🔗 Links

- **Documentation**: https://docs.nvidia.com/nemo-framework/user-guide/latest/automodel/index.html
- **Hugging Face Hub**: https://huggingface.co/models
- **Issues**: https://github.com/NVIDIA-NeMo/Automodel/issues
- **Discussions**: https://github.com/NVIDIA-NeMo/Automodel/discussions

---

<div align="center">

**Made with ❤️ by NVIDIA**

*Accelerating AI for everyone*

</div>
