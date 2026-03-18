# AI项目类型与部署模式

## 目录
1. [PyTorch模型训练/推理](#pytorch模型训练推理)
2. [大语言模型部署](#大语言模型部署)
3. [视频生成模型](#视频生成模型)
4. [传统视觉任务](#传统视觉任务)
5. [通用部署流程](#通用部署流程)

---

## PyTorch模型训练/推理

### 典型项目结构
```
project/
├── requirements.txt
├── setup.py
├── configs/
├── models/
├── data/
├── train.py
└── inference.py
```

### 标准部署流程
```bash
# 1. 创建虚拟环境
conda create -n project python=3.10
conda activate project

# 2. 安装PyTorch (先安装!)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. 安装项目依赖
pip install -r requirements.txt

# 4. 安装项目
pip install -e .
```

### 常见依赖组合
```txt
# requirements.txt 典型内容
torch>=2.0.0
torchvision>=0.15.0
numpy>=1.21.0
pillow>=9.0.0
tqdm>=4.64.0
tensorboard>=2.10.0
```

---

## 大语言模型部署

### 典型框架
- **transformers**: HuggingFace核心库
- **accelerate**: 分布式推理/训练
- **peft**: 参数高效微调
- **bitsandbytes**: 量化
- **vllm**: 高性能推理

### 标准部署
```bash
# 基础环境
conda create -n llm python=3.10
conda activate llm

# 安装PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 安装transformers生态
pip install transformers accelerate sentencepiece

# 可选: 量化支持
pip install bitsandbytes

# 可选: Flash Attention
pip install flash-attn --no-build-isolation
```

### vLLM部署
```bash
pip install vllm

# 启动API服务
python -m vllm.entrypoints.api_server \
    --model meta-llama/Llama-2-7b-hf \
    --host 0.0.0.0 \
    --port 8000
```

### LLaMA系列
```bash
# 使用transformers
pip install transformers accelerate sentencepiece

# 加载模型
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    torch_dtype="auto",
    device_map="auto"
)
```

### ChatGLM系列
```bash
pip install transformers accelerate sentencepiece cpm_kernels

# ChatGLM3
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True).half().cuda()
```

### 量化部署
```python
# 8-bit量化
model = AutoModelForCausalLM.from_pretrained(
    "model_id",
    load_in_8bit=True,
    device_map="auto"
)

# 4-bit量化
model = AutoModelForCausalLM.from_pretrained(
    "model_id",
    load_in_4bit=True,
    device_map="auto"
)
```

---

## 视频生成模型

### Sora类模型
```bash
# 常见依赖
pip install torch torchvision diffusers transformers accelerate

# xformers加速 (可选)
pip install xformers

# 示例: AnimateDiff
pip install diffusers transformers accelerate omegaconf einops
```

### Stable Video Diffusion
```bash
pip install diffusers transformers accelerate

from diffusers import StableVideoDiffusionPipeline
pipe = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid-xt",
    torch_dtype=torch.float16, variant="fp16"
).to("cuda")
```

### 视频编辑模型
```bash
# ControlNet视频
pip install diffusers transformers accelerate controlnet_aux

# 视频修复
pip install opencv-python imageio imageio-ffmpeg
```

---

## 传统视觉任务

### MMDetection
```bash
# 创建环境
conda create -n mmdet python=3.9 -y
conda activate mmdet

# 安装PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 安装MMCV (使用MIM)
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"

# 安装MMDetection
pip install mmdet

# 或从源码安装
git clone https://github.com/open-mmlab/mmdetection.git
cd mmdetection
pip install -v -e .
```

### MMAction2
```bash
conda create -n mmaction python=3.9 -y
conda activate mmaction

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
mim install mmdet  # MMAction2依赖MMDetection

pip install mmaction2
```

### MMSegmentation
```bash
conda create -n mmseg python=3.9 -y
conda activate mmseg

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"

pip install mmsegmentation
```

### YOLO系列
```bash
# Ultralytics YOLOv8
pip install ultralytics

# YOLOv5
git clone https://github.com/ultralytics/yolov5
cd yolov5
pip install -r requirements.txt
```

---

## 通用部署流程

### 1. 分析项目
```bash
# 运行分析脚本
python analyze_repo.py /path/to/project

# 检查文件
ls -la
cat README.md
cat requirements.txt
cat setup.py
cat pyproject.toml
```

### 2. 检查环境
```bash
# 运行诊断
python diagnose_env.py

# 检查GPU
python check_gpu.py
```

### 3. 创建虚拟环境
```bash
# conda (推荐)
conda create -n project python=3.10
conda activate project

# 或 venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### 4. 安装PyTorch (优先)
```bash
# 根据CUDA版本选择
python check_gpu.py --install-cmd

# 执行安装
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 5. 配置镜像源
```bash
# 配置国内镜像
python setup_mirrors.py all --mirror tsinghua
```

### 6. 安装项目依赖
```bash
# 按顺序安装
pip install -r requirements.txt

# 或使用setup.py
pip install -e .

# 或使用pyproject.toml
pip install -e .
```

### 7. 下载模型权重
```bash
# HuggingFace
python download_model.py model_id --mirror

# ModelScope
python download_model.py --modelscope model_id
```

### 8. 验证安装
```bash
# 测试导入
python -c "import torch; print(torch.cuda.is_available())"
python -c "import transformers; print(transformers.__version__)"

# 运行测试
pytest tests/
```

---

## 快速参考

### 镜像源配置
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
export HF_ENDPOINT=https://hf-mirror.com
```

### PyTorch安装
```bash
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### MMCV系列
```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
```

### LLM生态
```bash
pip install transformers accelerate peft bitsandbytes
```