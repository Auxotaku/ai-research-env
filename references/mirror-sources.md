# 国内镜像源配置指南

## 目录
1. [pip镜像源](#pip镜像源)
2. [conda镜像源](#conda镜像源)
3. [HuggingFace镜像](#huggingface镜像)
4. [PyTorch镜像](#pytorch镜像)
5. [其他镜像](#其他镜像)

---

## pip镜像源

### 常用镜像源

| 镜像站 | 地址 |
|--------|------|
| 清华 | https://pypi.tuna.tsinghua.edu.cn/simple |
| 阿里云 | https://mirrors.aliyun.com/pypi/simple |
| 中科大 | https://pypi.mirrors.ustc.edu.cn/simple |
| 华为云 | https://repo.huaweicloud.com/repository/pypi/simple |
| 腾讯云 | https://mirrors.cloud.tencent.com/pypi/simple |

### 配置方法

**临时使用**
```bash
pip install package -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**永久配置**
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn
```

**配置文件位置**
- Linux/macOS: `~/.pip/pip.conf`
- Windows: `%APPDATA%\pip\pip.ini`

**配置文件内容**
```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
```

---

## conda镜像源

### 常用镜像源

| 镜像站 | 地址 |
|--------|------|
| 清华 | https://mirrors.tuna.tsinghua.edu.cn/anaconda |
| 阿里云 | https://mirrors.aliyun.com/anaconda |
| 中科大 | https://mirrors.ustc.edu.cn/anaconda |

### 配置方法

**命令行配置**
```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
conda config --set show_channel_urls yes
```

**配置文件 `~/.condarc`**
```yaml
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
```

---

## HuggingFace镜像

### 镜像站

| 镜像站 | 地址 |
|--------|------|
| hf-mirror | https://hf-mirror.com |

### 配置方法

**方法1: 环境变量 (推荐)**
```bash
# Linux/macOS
export HF_ENDPOINT=https://hf-mirror.com

# Windows CMD
set HF_ENDPOINT=https://hf-mirror.com

# Windows PowerShell
$env:HF_ENDPOINT="https://hf-mirror.com"

# 永久配置 (添加到 ~/.bashrc 或 ~/.zshrc)
echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.bashrc
source ~/.bashrc
```

**方法2: 使用huggingface_hub**
```python
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from huggingface_hub import snapshot_download
snapshot_download('model_id')
```

**方法3: git clone替换**
```bash
# 原地址
git clone https://huggingface.co/model_id

# 替换为
git clone https://hf-mirror.com/model_id
```

### modelscope替代方案

对于大模型，可以使用ModelScope:
```bash
pip install modelscope

from modelscope import snapshot_download
snapshot_download('model_id')
```

---

## PyTorch镜像

### 官方安装命令

访问 https://pytorch.org/get-started/locally/ 获取最新命令

### 国内镜像安装

```bash
# CUDA 12.4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### conda安装
```bash
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

---

## 其他镜像

### GitHub镜像

```bash
# 克隆仓库
git clone https://github.com/user/repo.git
# 替换为
git clone https://gitclone.com/github.com/user/repo.git
git clone https://hub.fastgit.xyz/user/repo.git
git clone https://mirror.ghproxy.com/https://github.com/user/repo.git
```

### GitHub文件下载加速

```bash
# 原地址
https://github.com/user/repo/releases/download/v1.0/file.zip

# 加速地址
https://ghproxy.com/https://github.com/user/repo/releases/download/v1.0/file.zip
https://mirror.ghproxy.com/https://github.com/user/repo/releases/download/v1.0/file.zip
```

### weights.gg (模型权重镜像)

```bash
# 使用weights.gg下载模型
pip install weights
weights download model_id
```

### Docker镜像

```bash
# Docker Hub镜像
docker pull dockerpull.org/library/ubuntu:latest
docker pull docker.1panel.live/library/ubuntu:latest
```

---

## 快速配置脚本

使用本skill的脚本一键配置:
```bash
# 列出所有镜像源
python setup_mirrors.py list

# 配置pip镜像
python setup_mirrors.py pip --mirror tsinghua

# 配置conda镜像
python setup_mirrors.py conda --mirror tsinghua

# 配置HuggingFace镜像
python setup_mirrors.py hf

# 一键配置所有镜像
python setup_mirrors.py all --mirror tsinghua
```