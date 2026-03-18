# CUDA与PyTorch版本兼容性

## 版本对应表

### PyTorch与CUDA版本

| PyTorch版本 | 支持的CUDA版本 |
|-------------|----------------|
| 2.5.x | 12.4, 12.1, 11.8 |
| 2.4.x | 12.1, 11.8 |
| 2.3.x | 12.1, 11.8 |
| 2.2.x | 12.1, 11.8 |
| 2.1.x | 12.1, 11.8 |
| 2.0.x | 11.8, 11.7 |
| 1.13.x | 11.7, 11.6 |
| 1.12.x | 11.6, 11.3 |
| 1.11.x | 11.3 |
| 1.10.x | 11.3 |

### 驱动与CUDA版本

| NVIDIA驱动版本 | 支持的最高CUDA版本 |
|----------------|-------------------|
| 550.x | 12.4 |
| 545.x | 12.3 |
| 535.x | 12.2 |
| 530.x | 12.1 |
| 525.x | 12.0 |
| 520.x | 11.8 |
| 515.x | 11.7 |
| 510.x | 11.6 |
| 495.x | 11.5 |

### GPU计算能力与CUDA

| GPU系列 | 计算能力 | 最低CUDA版本 |
|---------|----------|--------------|
| RTX 40系列 | 8.9 | 11.8+ |
| RTX 30系列 | 8.6 | 11.1+ |
| RTX 20系列 | 7.5 | 10.0+ |
| GTX 16系列 | 7.5 | 10.0+ |
| GTX 10系列 | 6.1 | 9.0+ |
| H100 | 9.0 | 11.8+ |
| A100 | 8.0 | 11.0+ |
| V100 | 7.0 | 9.0+ |

---

## 安装命令

### CUDA 12.4
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### CUDA 12.1
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### CUDA 11.8
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### CPU版本
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Conda安装
```bash
# CUDA 12.1
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia

# CUDA 11.8
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

---

## 常见框架CUDA要求

### transformers
```bash
# 最简单安装
pip install transformers

# GPU支持需要正确安装PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers
```

### diffusers
```bash
pip install diffusers transformers accelerate
# GPU支持需要PyTorch
```

### bitsandbytes (8-bit量化)
```bash
# CUDA 11.8+
pip install bitsandbytes

# CUDA 12.x 可能需要从源码安装
pip install git+https://github.com/TimDettmers/bitsandbytes.git
```

### flash-attn
```bash
# 需要CUDA 11.6+
pip install flash-attn --no-build-isolation

# 或预编译版本
pip install flash-attn
```

### xformers
```bash
# 需要匹配PyTorch版本
pip install xformers

# 特定版本
pip install xformers==0.0.22
```

### MMCV系列
```bash
# 使用MIM安装 (推荐)
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"

# MMCV版本对应
# mmcv 2.x -> PyTorch 1.8+
# mmcv 1.x -> PyTorch 1.3-1.11
```

---

## 检查脚本

```python
import torch

print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"PyTorch CUDA版本: {torch.version.cuda}")
    print(f"cuDNN版本: {torch.backends.cudnn.version()}")
    print(f"GPU数量: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        props = torch.cuda.get_device_properties(i)
        print(f"    显存: {props.total_memory / 1024**3:.1f} GB")
        print(f"    计算能力: {props.major}.{props.minor}")
```

---

## 故障排除

### 1. 查看系统CUDA版本
```bash
# nvcc版本 (开发工具)
nvcc --version

# 驱动支持的CUDA版本
nvidia-smi
```

### 2. PyTorch CUDA版本与系统不匹配
```python
import torch
print(f"PyTorch编译CUDA版本: {torch.version.cuda}")

# 这个版本是PyTorch编译时使用的CUDA版本
# 它应该 <= 系统安装的CUDA版本
```

### 3. 多CUDA版本管理
```bash
# 检查CUDA路径
ls /usr/local/ | grep cuda

# 切换CUDA版本 (Linux)
export PATH=/usr/local/cuda-11.8/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH

# 或使用软链接
sudo ln -sf /usr/local/cuda-11.8 /usr/local/cuda
```

### 4. Windows CUDA路径
```cmd
# 检查环境变量
echo %CUDA_PATH%
echo %PATH%

# 设置CUDA路径
set CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8
set PATH=%CUDA_PATH%\bin;%PATH%
```