# 预编译Wheels索引

## 目录
1. [Flash Attention](#flash-attention)
2. [xFormers](#xformers)
3. [BitsAndBytes](#bitsandbytes)
4. [DeepSpeed](#deepspeed)
5. [MMCV](#mmcv)
6. [其他常用预编译包](#其他常用预编译包)

---

## Flash Attention

### 预编译Wheels下载

**官方Release**: https://github.com/Dao-AILab/flash-attention/releases

**第三方预编译**: https://github.com/bdashore3/flash-attention/releases

### 安装命令

```bash
# 方法1: pip安装 (需要编译环境)
pip install flash-attn --no-build-isolation

# 方法2: 从预编译whl安装
# 根据CUDA版本和PyTorch版本选择对应的whl
pip install flash_attn-2.x.x+cuxxx.whl

# 方法3: 使用第三方预编译
pip install https://github.com/bdashore3/flash-attention/releases/download/v2.5.6/flash_attn-2.5.6+cu122torch2.3cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
```

### 版本对应表

| Flash Attention | PyTorch | CUDA |
|-----------------|---------|------|
| 2.5.6 | 2.3.0+ | 12.1, 11.8 |
| 2.5.5 | 2.2.0+ | 12.1, 11.8 |
| 2.4.2 | 2.1.0+ | 12.1, 11.8 |
| 2.3.6 | 2.0.0+ | 11.8 |

### 编译要求
```bash
# 需要安装
pip install ninja packaging
# 需要CUDA开发工具
nvcc --version
```

---

## xFormers

### 官方安装
```bash
pip install xformers
```

### 预编译Wheels

**官方Release**: https://github.com/facebookresearch/xformers/releases

### 版本对应表

| xFormers | PyTorch | CUDA |
|----------|---------|------|
| 0.0.26 | 2.4.0 | 12.1, 11.8 |
| 0.0.25 | 2.3.0 | 12.1, 11.8 |
| 0.0.24 | 2.2.0 | 12.1, 11.8 |
| 0.0.23 | 2.1.0 | 12.1, 11.8 |
| 0.0.22 | 2.0.0 | 11.8 |

### 从特定索引安装
```bash
# 查看可用版本
pip index versions xformers

# 安装特定版本
pip install xformers==0.0.26
```

---

## BitsAndBytes

### 安装
```bash
# CUDA 11.8+
pip install bitsandbytes

# CUDA 12.x 需要从源码编译
pip install git+https://github.com/TimDettmers/bitsandbytes.git
```

### 预编译Wheels

**官方Release**: https://github.com/TimDettmers/bitsandbytes/releases

### 常见问题
```bash
# 检查安装
python -c "import bitsandbytes; print(bitsandbytes.__version__)"

# 如果报错，检查CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

---

## DeepSpeed

### 安装
```bash
pip install deepspeed

# 或特定版本
pip install deepspeed==0.12.6
```

### 预编译Wheels

**官方Release**: https://github.com/microsoft/DeepSpeed/releases

### 系统依赖
```bash
# 需要的库
sudo apt-get install libaio-dev

# 检查
ds_report
```

---

## MMCV

### 推荐使用MIM安装
```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
```

### 预编译Wheels

**官方索引**: https://download.openmmlab.com/mmcv/dist/

### 安装命令
```bash
# 根据CUDA和PyTorch版本选择
# 格式: cu{cuda}/torch{pytorch}/index.html

# CUDA 11.8 + PyTorch 2.1
pip install mmcv -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.1/index.html

# CUDA 12.1 + PyTorch 2.3
pip install mmcv -f https://download.openmmlab.com/mmcv/dist/cu121/torch2.3/index.html
```

### 版本对应
| MMCV | MMCV版本 | PyTorch | CUDA |
|------|----------|---------|------|
| mmcv 2.1.0 | 2.1.0 | 2.0-2.3 | 11.6-12.1 |
| mmcv 2.0.1 | 2.0.1 | 1.8-2.1 | 11.3-11.8 |
| mmcv 1.7.1 | 1.7.1 | 1.6-1.11 | 10.2-11.7 |

---

## 其他常用预编译包

### Triton
```bash
pip install triton

# 特定版本
pip install triton==2.3.0
```

### apex (NVIDIA)
```bash
# 需要从源码编译
git clone https://github.com/NVIDIA/apex
cd apex
pip install -v --disable-pip-version-check --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" ./

# 或只安装Python部分 (无CUDA扩展)
pip install apex -f https://dl.fbaipublicfiles.com/detectron2/wheels/index.html
```

### Detectron2
```bash
# 预编译版本
python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cu118/torch2.1/index.html
```

### spconv
```bash
# 预编译版本
pip install spconv-cu118  # CUDA 11.8
pip install spconv-cu121  # CUDA 12.1
```

### MinkowskiEngine
```bash
# 从源码编译
pip install -U MinkowskiEngine

# 需要CUDA环境
export CUDA_HOME=/usr/local/cuda
```

---

## 通用查找预编译包的方法

### 1. 查看GitHub Releases
```bash
# 大多数项目会在Releases页面提供预编译whl
https://github.com/owner/repo/releases
```

### 2. PyPI查看可用版本
```bash
pip index versions package_name
```

### 3. 使用pip download
```bash
# 下载但不安装
pip download package_name --no-deps
```

### 4. 查看项目文档
- 通常在Installation或Getting Started章节
- 会列出预编译版本的下载链接

---

## 快速安装脚本示例

```bash
#!/bin/bash
# install_special_packages.sh

# 检测CUDA版本
CUDA_VERSION=$(nvcc --version | grep -oP 'release \K[0-9]+\.[0-9]+')
echo "Detected CUDA: $CUDA_VERSION"

# PyTorch
if [[ "$CUDA_VERSION" == "12.1" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
elif [[ "$CUDA_VERSION" == "11.8" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi

# Flash Attention (预编译)
# 根据实际版本选择
# pip install https://github.com/.../flash_attn-xxx.whl

# xFormers
pip install xformers

# MMCV (使用MIM)
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
```